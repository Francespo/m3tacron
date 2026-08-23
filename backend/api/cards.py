from fastapi import APIRouter, Query, Depends
from ..analytics.core import aggregate_card_stats
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from .schemas import PaginatedPilotsResponse, PaginatedUpgradesResponse
from ..cache import get_cached_or_compute

router = APIRouter(prefix="/api/cards", tags=["Cards"])


def _compute_cards(
    data_source: str,
    mode: str,
    filters: dict,
) -> list[dict]:
    """Run the expensive card aggregation for pilots or upgrades mode.

    The heavy SQL aggregation is sort-independent, so it always runs with a
    neutral sort (Lists desc). The caller applies the requested sort to the
    cached list before paginating — see _sort_card_stats.
    """
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    return aggregate_card_stats(
        filters,
        SortingCriteria.LISTS,
        SortDirection.DESCENDING,
        mode,
        ds_enum,
    )


def _sort_card_stats(data: list[dict], sort_metric: str, sort_direction: str) -> list[dict]:
    def sort_key(item):
        if sort_metric == "Squadrons":
            return (item.get("squadron_count", 0), item.get("games_count", 0))
        elif sort_metric == "Entries":
            return (item.get("entries_count", 0), item.get("games_count", 0))
        elif sort_metric == "Games":
            return item.get("games_count", 0)
        elif sort_metric == "Win Rate":
            return item["wins"] / item["games_count"] if item.get("games_count", 0) > 0 else 0
        elif sort_metric == "Name":
            return item.get("xws", "")
        elif sort_metric in ("Cost", "Loadout"):
            return 0
        return (item.get("list_count", 0), item.get("games_count", 0))

    return sorted(data, key=sort_key, reverse=(sort_direction == "desc"))


def _build_filters(
    formats: list[str] | None = None,
    factions: list[str] | None = None,
    ships: list[str] | None = None,
    initiatives: list[int] | None = None,
    upgrade_types: list[str] | None = None,
    search_text: str = "",
    points_min: int | None = None,
    points_max: int | None = None,
    loadout_min: int | None = None,
    loadout_max: int | None = None,
    hull_min: int | None = None,
    hull_max: int | None = None,
    shields_min: int | None = None,
    shields_max: int | None = None,
    agility_min: int | None = None,
    agility_max: int | None = None,
    attack_min: int | None = None,
    attack_max: int | None = None,
    init_min: int | None = None,
    init_max: int | None = None,
    is_unique: bool = False,
    is_limited: bool = False,
    is_not_limited: bool = False,
    base_sizes: list[str] | None = None,
    platforms: list[str] | None = None,
    continent: list[str] | None = None,
    country: list[str] | None = None,
    city: list[str] | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    player_count_min: int | None = None,
    player_count_max: int | None = None,
    upgrade_id: str | None = None,
    epic: bool = False,
) -> dict:
    
    # Base sizes mapping
    sizes_dict = {}
    if base_sizes:
        for s in base_sizes:
            sizes_dict[s] = True

    return {
        "allowed_formats": formats,
        "search_text": search_text,
        "faction": factions,
        "ship": ships,
        "initiative": initiatives,
        "upgrade_type": upgrade_types,
        "points_min": points_min,
        "points_max": points_max,
        "loadout_min": loadout_min,
        "loadout_max": loadout_max,
        "hull_min": hull_min,
        "hull_max": hull_max,
        "shields_min": shields_min,
        "shields_max": shields_max,
        "agility_min": agility_min,
        "agility_max": agility_max,
        "attack_min": attack_min,
        "attack_max": attack_max,
        "init_min": init_min,
        "init_max": init_max,
        "is_unique": is_unique,
        "is_limited": is_limited,
        "is_not_limited": is_not_limited,
        "base_sizes": sizes_dict,
        "platforms": platforms,
        "continent": continent,
        "country": country,
        "city": city,
        "date_start": date_start,
        "date_end": date_end,
        "player_count_min": player_count_min,
        "player_count_max": player_count_max,
        "upgrade_id": upgrade_id,
        "include_epic": epic,
    }


@router.get("/pilots", response_model=PaginatedPilotsResponse)
def get_pilots(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Lists"),
    sort_direction: str = Query("desc"),
    epic: bool = Query(False),
    
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    initiatives: list[int] | None = Query(None),
    search_text: str = Query(""),
    search: str = Query(""),
    points_min: int | None = Query(None),
    points_max: int | None = Query(None),
    loadout_min: int | None = Query(None),
    loadout_max: int | None = Query(None),
    hull_min: int | None = Query(None),
    hull_max: int | None = Query(None),
    shields_min: int | None = Query(None),
    shields_max: int | None = Query(None),
    agility_min: int | None = Query(None),
    agility_max: int | None = Query(None),
    attack_min: int | None = Query(None),
    attack_max: int | None = Query(None),
    init_min: int | None = Query(None),
    init_max: int | None = Query(None),
    is_unique: bool = Query(False),
    is_limited: bool = Query(False),
    is_not_limited: bool = Query(False),
    base_sizes: list[str] | None = Query(None),
    platforms: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
):
    effective_search = search or search_text
    filters = _build_filters(
        formats=formats, factions=factions, ships=ships, initiatives=initiatives,
        search_text=effective_search, points_min=points_min, points_max=points_max,
        loadout_min=loadout_min, loadout_max=loadout_max, hull_min=hull_min,
        hull_max=hull_max, shields_min=shields_min, shields_max=shields_max,
        agility_min=agility_min, agility_max=agility_max, attack_min=attack_min,
        attack_max=attack_max, init_min=init_min, init_max=init_max,
        is_unique=is_unique, is_limited=is_limited, is_not_limited=is_not_limited,
        base_sizes=base_sizes, platforms=platforms, continent=continent, country=country, city=city,
        date_start=date_start, date_end=date_end,
        player_count_min=player_count_min, player_count_max=player_count_max,
        epic=epic,
    )

    cache_key = (
        f"cards_pilots|{data_source}"
        f"|{','.join(sorted(formats or []))}"
        f"|{','.join(sorted(factions or []))}"
        f"|{','.join(sorted(ships or []))}"
        f"|{','.join(sorted(str(i) for i in (initiatives or [])))}"
        f"|{effective_search or ''}"
        f"|{points_min}|{points_max}"
        f"|{loadout_min}|{loadout_max}"
        f"|{hull_min}|{hull_max}"
        f"|{shields_min}|{shields_max}"
        f"|{agility_min}|{agility_max}"
        f"|{attack_min}|{attack_max}"
        f"|{init_min}|{init_max}"
        f"|{is_unique}|{is_limited}|{is_not_limited}"
        f"|{','.join(sorted(base_sizes or []))}"
        f"|{','.join(sorted(platforms or []))}"
        f"|{','.join(sorted(continent or []))}"
        f"|{','.join(sorted(country or []))}"
        f"|{','.join(sorted(city or []))}"
        f"|{date_start or ''}|{date_end or ''}"
        f"|{player_count_min}|{player_count_max}"
        f"|{epic}"
    )

    def compute():
        return _compute_cards(data_source, "pilots", filters)

    data = get_cached_or_compute(cache_key, compute)
    # Sort AFTER the cache lookup — the heavy aggregation is sort-independent.
    data = _sort_card_stats(data, sort_metric, sort_direction)
    total = len(data)
    items = data[page * size : (page + 1) * size]

    return PaginatedPilotsResponse(items=items, total=total, page=page, size=size)


@router.get("/upgrades", response_model=PaginatedUpgradesResponse)
def get_upgrades(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Lists"),
    sort_direction: str = Query("desc"),
    upgrade_id: str | None = Query(None, description="Filter to lists containing this upgrade xws"),
    epic: bool = Query(False),

    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    upgrade_types: list[str] | None = Query(None),
    search_text: str = Query(""),
    search: str = Query(""),
    points_min: int | None = Query(None),
    points_max: int | None = Query(None),
    platforms: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
):
    effective_search = search or search_text
    filters = _build_filters(
        formats=formats, factions=factions, upgrade_types=upgrade_types,
        search_text=effective_search, points_min=points_min, points_max=points_max,
        platforms=platforms, continent=continent, country=country, city=city,
        date_start=date_start, date_end=date_end,
        player_count_min=player_count_min, player_count_max=player_count_max,
        upgrade_id=upgrade_id,
        epic=epic,
    )

    cache_key = (
        f"cards_upgrades|{data_source}"
        f"|{','.join(sorted(formats or []))}"
        f"|{','.join(sorted(factions or []))}"
        f"|{','.join(sorted(upgrade_types or []))}"
        f"|{effective_search or ''}"
        f"|{points_min}|{points_max}"
        f"|{','.join(sorted(platforms or []))}"
        f"|{','.join(sorted(continent or []))}"
        f"|{','.join(sorted(country or []))}"
        f"|{','.join(sorted(city or []))}"
        f"|{date_start or ''}|{date_end or ''}"
        f"|{player_count_min}|{player_count_max}"
        f"|{upgrade_id or ''}"
        f"|{epic}"
    )

    def compute():
        return _compute_cards(data_source, "upgrades", filters)

    data = get_cached_or_compute(cache_key, compute)
    # Sort AFTER the cache lookup — the heavy aggregation is sort-independent.
    data = _sort_card_stats(data, sort_metric, sort_direction)
    total = len(data)
    items = data[page * size : (page + 1) * size]

    return PaginatedUpgradesResponse(items=items, total=total, page=page, size=size)
