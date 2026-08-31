"""
Ship Detail API endpoints.

Provides ship info, pilot breakdown, top lists, and top squadrons.
"""
from fastapi import APIRouter, Query
from collections import defaultdict

from ..analytics.ships import aggregate_ship_stats
from ..analytics.lists import aggregate_list_stats, fetch_list_pilots
from ..analytics.squadrons import aggregate_squadron_stats
from ..analytics.core import aggregate_card_stats
from ..cache import get_cached_or_compute
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from ..utils.xwing_data.ships import load_all_ships
from .formatters import enrich_list_data

router = APIRouter(prefix="/api/ship", tags=["Ship Detail"])


def _ship_filter_cache_suffix(
    formats: list[str] | None,
    factions: list[str] | None,
    ships: list[str] | None,
    continent: list[str] | None,
    country: list[str] | None,
    city: list[str] | None,
    platforms: list[str] | None,
    sources: list[str] | None,
    date_start: str | None,
    date_end: str | None,
    player_count_min: int | None,
    player_count_max: int | None,
    search: str | None,
    epic: bool | None,
    faction: str | None,
) -> str:
    """Stable suffix for ship-detail cache keys covering all filter inputs."""
    return (
        f"|f={','.join(sorted(formats or []))}"
        f"|fa={','.join(sorted(factions or []))}"
        f"|s={','.join(sorted(ships or []))}"
        f"|co={','.join(sorted(continent or []))}"
        f"|cn={','.join(sorted(country or []))}"
        f"|ci={','.join(sorted(city or []))}"
        f"|p={','.join(sorted(platforms or []))}"
        f"|so={','.join(sorted(sources or []))}"
        f"|ds={date_start or ''}|de={date_end or ''}"
        f"|pcmin={player_count_min}|pcmax={player_count_max}"
        f"|q={search or ''}|epic={epic}|faction={faction or 'all'}"
    )


def _build_filters(
    ship_xws: str,
    formats: list[str] | None,
    factions: list[str] | None,
    faction: str | None,
    ships: list[str] | None,
    continent: list[str] | None,
    country: list[str] | None,
    city: list[str] | None,
    platforms: list[str] | None,
    sources: list[str] | None,
    date_start: str | None,
    date_end: str | None,
    player_count_min: int | None,
    player_count_max: int | None,
    search: str | None,
    epic: bool | None,
) -> dict:
    """Build a filters dict compatible with all analytics helpers.

    - `ship_xws` (path) is always the primary ship filter.
    - `faction` (singular) is the per-ship detail toggle and overrides the
      global `factions` list when present.
    - `formats` maps to `allowed_formats`.
    - `platforms`/`sources` are merged to both keys for compatibility.
    - `epic` maps to both `epic` and `include_epic` so lists/squadrons and
      pilots (core) both observe it.
    """
    # Resolve faction: detail toggle wins over global.
    if faction:
        eff_faction = [faction]
    elif factions:
        eff_faction = list(factions)
    else:
        eff_faction = None

    # Platforms/sources are aliases; merge.
    merged_platforms: list[str] | None = None
    if platforms or sources:
        merged_platforms = list(platforms or []) + list(sources or [])
        # de-dupe while preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for p in merged_platforms:
            if p not in seen:
                seen.add(p)
                deduped.append(p)
        merged_platforms = deduped

    filters: dict = {"ship": [ship_xws]}

    if formats:
        filters["allowed_formats"] = list(formats)
    if eff_faction:
        # Set both keys so ship/core (which check `faction`) and
        # lists/squadrons (which check `factions`) see the value.
        filters["faction"] = eff_faction
        filters["factions"] = eff_faction
    elif factions:
        # already handled above, but keep for type clarity
        filters["faction"] = list(factions)
        filters["factions"] = list(factions)

    if ships:
        # Global ships filter (chassis multi-select) — keep as `ships`
        # in addition to the detail `ship` so callers that check either
        # key still see the global filter. The detail ship is already
        # in `ship`; analytics prefer `ship` over `ships`.
        filters["ships"] = list(ships)

    if continent:
        filters["continent"] = list(continent)
    if country:
        filters["country"] = list(country)
    if city:
        filters["city"] = list(city)
    if merged_platforms:
        filters["platforms"] = merged_platforms
        filters["sources"] = merged_platforms
    if date_start:
        filters["date_start"] = date_start
    if date_end:
        filters["date_end"] = date_end
    if player_count_min is not None:
        filters["player_count_min"] = player_count_min
    if player_count_max is not None:
        filters["player_count_max"] = player_count_max
    if search:
        filters["search_name"] = search
        filters["search_text"] = search
        filters["search"] = search
    if epic is not None:
        filters["epic"] = bool(epic)
        filters["include_epic"] = bool(epic)

    return filters


def _fetch_ship_pilots(
    ship_xws: str,
    ds: DataSource,
    sort_metric: str = "Lists",
    sort_direction: str = "desc",
    formats: list[str] | None = None,
    factions: list[str] | None = None,
    ships: list[str] | None = None,
    continent: list[str] | None = None,
    country: list[str] | None = None,
    city: list[str] | None = None,
    platforms: list[str] | None = None,
    sources: list[str] | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    player_count_min: int | None = None,
    player_count_max: int | None = None,
    search: str | None = None,
    epic: bool = False,
    faction: str | None = None,
) -> list[dict]:
    criteria_map = {
        "Lists": SortingCriteria.LISTS,
        "Unique Lists": SortingCriteria.UNIQUE_LISTS,
        "Win Rate": SortingCriteria.WINRATE,
        "Games": SortingCriteria.GAMES,
    }
    criteria = criteria_map.get(sort_metric, SortingCriteria.LISTS)
    direction = SortDirection.DESCENDING if sort_direction == "desc" else SortDirection.ASCENDING

    cache_key = (
        f"ship_pilots|{ship_xws}|{ds.value}|{sort_metric}|{sort_direction}"
        + _ship_filter_cache_suffix(formats, factions, ships, continent, country, city, platforms, sources, date_start, date_end, player_count_min, player_count_max, search, epic, faction)
    )

    def compute():
        filters = _build_filters(
            ship_xws=ship_xws,
            formats=formats,
            factions=factions,
            faction=faction,
            ships=ships,
            continent=continent,
            country=country,
            city=city,
            platforms=platforms,
            sources=sources,
            date_start=date_start,
            date_end=date_end,
            player_count_min=player_count_min,
            player_count_max=player_count_max,
            search=search,
            epic=epic,
        )
        return aggregate_card_stats(filters, criteria, direction, "pilots", ds)

    return get_cached_or_compute(cache_key, compute)


def _fetch_ship_lists(
    ship_xws: str,
    ds: DataSource,
    limit: int = 10,
    formats: list[str] | None = None,
    factions: list[str] | None = None,
    ships: list[str] | None = None,
    continent: list[str] | None = None,
    country: list[str] | None = None,
    city: list[str] | None = None,
    platforms: list[str] | None = None,
    sources: list[str] | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    player_count_min: int | None = None,
    player_count_max: int | None = None,
    search: str | None = None,
    epic: bool = False,
    faction: str | None = None,
) -> list[dict]:
    cache_key = (
        f"ship_lists|{ship_xws}|{ds.value}|{limit}"
        + _ship_filter_cache_suffix(formats, factions, ships, continent, country, city, platforms, sources, date_start, date_end, player_count_min, player_count_max, search, epic, faction)
    )

    def compute_lists():
        filters = _build_filters(
            ship_xws=ship_xws,
            formats=formats,
            factions=factions,
            faction=faction,
            ships=ships,
            continent=continent,
            country=country,
            city=city,
            platforms=platforms,
            sources=sources,
            date_start=date_start,
            date_end=date_end,
            player_count_min=player_count_min,
            player_count_max=player_count_max,
            search=search,
            epic=epic,
        )
        return aggregate_list_stats(filters, data_source=ds)

    data = get_cached_or_compute(cache_key, compute_lists)
    
    filtered_data = [d for d in data if d.get("games", 0) >= 5]
    filtered_data.sort(key=lambda x: x.get("win_rate", 0), reverse=True)
    if not filtered_data:
        filtered_data = data

    top = filtered_data[:limit]
    signatures: list[str] = [l["signature"] for l in top if l.get("signature")]
    pilots_map = fetch_list_pilots(signatures) if signatures else {}
    enriched = [
        {**l, "pilots": pilots_map.get(l["signature"], [])}
        for l in top
        if l.get("signature")
    ]
    return [enrich_list_data(l, source=ds) for l in enriched]


def _fetch_ship_squadrons(
    ship_xws: str,
    ds: DataSource,
    limit: int = 10,
    formats: list[str] | None = None,
    factions: list[str] | None = None,
    ships: list[str] | None = None,
    continent: list[str] | None = None,
    country: list[str] | None = None,
    city: list[str] | None = None,
    platforms: list[str] | None = None,
    sources: list[str] | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    player_count_min: int | None = None,
    player_count_max: int | None = None,
    search: str | None = None,
    epic: bool = False,
    faction: str | None = None,
) -> list[dict]:
    cache_key = (
        f"ship_squadrons|{ship_xws}|{ds.value}|{limit}"
        + _ship_filter_cache_suffix(formats, factions, ships, continent, country, city, platforms, sources, date_start, date_end, player_count_min, player_count_max, search, epic, faction)
    )

    def compute_squadrons():
        filters = _build_filters(
            ship_xws=ship_xws,
            formats=formats,
            factions=factions,
            faction=faction,
            ships=ships,
            continent=continent,
            country=country,
            city=city,
            platforms=platforms,
            sources=sources,
            date_start=date_start,
            date_end=date_end,
            player_count_min=player_count_min,
            player_count_max=player_count_max,
            search=search,
            epic=epic,
        )
        return aggregate_squadron_stats(filters, SortingCriteria.WINRATE, SortDirection.DESCENDING, ds)

    data = get_cached_or_compute(cache_key, compute_squadrons)
    filtered_data = [d for d in data if d.get("games", 0) >= 5]
    if not filtered_data:
        filtered_data = data
    return filtered_data[:limit]


@router.get("/{ship_xws}")
def get_ship_info(
    ship_xws: str,
    data_source: str = Query("xwa"),
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    platforms: list[str] | None = Query(None),
    sources: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
    search: str | None = Query(None),
    epic: bool = Query(False),
    faction: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    full: bool = Query(True),
):
    """Return unified ship detail (info, stats, pilots, top lists, and top squadrons)."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    all_ships = load_all_ships(ds)
    info = all_ships.get(ship_xws, {"name": ship_xws, "xws": ship_xws, "factions": []})

    cache_key = (
        f"ship_info|{ship_xws}|{ds.value}"
        + _ship_filter_cache_suffix(formats, factions, ships, continent, country, city, platforms, sources, date_start, date_end, player_count_min, player_count_max, search, epic, faction)
    )

    def compute():
        filters = _build_filters(
            ship_xws=ship_xws,
            formats=formats,
            factions=factions,
            faction=faction,
            ships=ships,
            continent=continent,
            country=country,
            city=city,
            platforms=platforms,
            sources=sources,
            date_start=date_start,
            date_end=date_end,
            player_count_min=player_count_min,
            player_count_max=player_count_max,
            search=search,
            epic=epic,
        )
        stats = aggregate_ship_stats(filters, SortingCriteria.GAMES, SortDirection.DESCENDING, ds)
        return stats[0] if stats and len(stats) > 0 else {}

    stat_info = get_cached_or_compute(cache_key, compute)

    if not full:
        return {
            "info": info,
            "stats": stat_info,
            "faction": faction or "all",
        }

    # Fetch remaining sections in parallel — cached-or-compute is thread-safe
    # and cold aggregations are DB-bound (2-3s each for pilots). Serial was
    # 3× latency; parallel ~max(pilots,lists,squadrons) => 2-3s -> 0.8s warm.
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=3) as pool:
        fut_pilots = pool.submit(
            _fetch_ship_pilots,
            ship_xws, ds, "Lists", "desc",
            formats, factions, ships, continent, country, city, platforms, sources,
            date_start, date_end, player_count_min, player_count_max, search, epic, faction,
        )
        fut_lists = pool.submit(
            _fetch_ship_lists,
            ship_xws, ds, limit,
            formats, factions, ships, continent, country, city, platforms, sources,
            date_start, date_end, player_count_min, player_count_max, search, epic, faction,
        )
        fut_squadrons = pool.submit(
            _fetch_ship_squadrons,
            ship_xws, ds, limit,
            formats, factions, ships, continent, country, city, platforms, sources,
            date_start, date_end, player_count_min, player_count_max, search, epic, faction,
        )
        pilots = fut_pilots.result()
        lists = fut_lists.result()
        squadrons = fut_squadrons.result()

    return {
        "info": info,
        "stats": stat_info,
        "pilots": pilots,
        "lists": lists,
        "squadrons": squadrons,
        "faction": faction or "all",
    }


@router.get("/{ship_xws}/pilots")
def get_ship_pilots(
    ship_xws: str,
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Lists"),
    sort_direction: str = Query("desc"),
    epic: bool = Query(False),
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    platforms: list[str] | None = Query(None),
    sources: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
    search: str | None = Query(None),
    faction: str | None = Query(None),
):
    """Return pilot stats filtered to this ship."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    pilots = _fetch_ship_pilots(
        ship_xws=ship_xws, ds=ds, sort_metric=sort_metric, sort_direction=sort_direction,
        formats=formats, factions=factions, ships=ships, continent=continent,
        country=country, city=city, platforms=platforms, sources=sources,
        date_start=date_start, date_end=date_end, player_count_min=player_count_min,
        player_count_max=player_count_max, search=search, epic=epic, faction=faction,
    )
    return {"pilots": pilots, "faction": faction or "all"}


@router.get("/{ship_xws}/lists")
def get_ship_lists(
    ship_xws: str,
    data_source: str = Query("xwa"),
    limit: int = Query(10, ge=1, le=50),
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    platforms: list[str] | None = Query(None),
    sources: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
    search: str | None = Query(None),
    epic: bool = Query(False),
    faction: str | None = Query(None),
):
    """Return top performing lists containing this ship."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    lists = _fetch_ship_lists(
        ship_xws=ship_xws, ds=ds, limit=limit,
        formats=formats, factions=factions, ships=ships, continent=continent,
        country=country, city=city, platforms=platforms, sources=sources,
        date_start=date_start, date_end=date_end, player_count_min=player_count_min,
        player_count_max=player_count_max, search=search, epic=epic, faction=faction,
    )
    return {"lists": lists}


@router.get("/{ship_xws}/squadrons")
def get_ship_squadrons(
    ship_xws: str,
    data_source: str = Query("xwa"),
    limit: int = Query(10, ge=1, le=50),
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    platforms: list[str] | None = Query(None),
    sources: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
    search: str | None = Query(None),
    epic: bool = Query(False),
    faction: str | None = Query(None),
):
    """Return top performing squadrons containing this ship."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    squadrons = _fetch_ship_squadrons(
        ship_xws=ship_xws, ds=ds, limit=limit,
        formats=formats, factions=factions, ships=ships, continent=continent,
        country=country, city=city, platforms=platforms, sources=sources,
        date_start=date_start, date_end=date_end, player_count_min=player_count_min,
        player_count_max=player_count_max, search=search, epic=epic, faction=faction,
    )
    return {"squadrons": squadrons}
