from fastapi import APIRouter, Query
from ..analytics.squadrons import aggregate_squadron_stats
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..cache import get_cached_or_compute
from ..utils.xwing_data.ships import load_all_ships

router = APIRouter(prefix="/api/squadrons", tags=["Squadrons"])


def _compute_squadrons(
    data_source: str,
    filters: dict,
) -> dict:
    """Run the expensive aggregation + post-filter.

    Returns a dict with `filtered` (full list in neutral games-desc order)
    and `total` for the caller to sort, paginate, and enrich. Sorting is
    applied AFTER the cache lookup — see _sort_squadron_stats.
    """
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    factions = filters.get("factions")
    min_games = filters.get("min_games", 0)

    raw_data = aggregate_squadron_stats(
        filters,
        sort_metric=SortingCriteria.GAMES,
        sort_direction=SortDirection.DESCENDING,
        data_source=ds_enum,
    )

    filtered_data = []
    for row in raw_data:
        if factions and row["faction"] not in factions:
            continue
        if row["games"] < min_games:
            continue
        filtered_data.append(row)

    total = len(filtered_data)

    return {"filtered": filtered_data, "total": total}


def _sort_squadron_stats(data: list[dict], sort_metric: str, sort_direction: str) -> list[dict]:
    reverse = sort_direction == "desc"
    if sort_metric == "Win Rate":
        return sorted(data, key=lambda x: x["win_rate"], reverse=reverse)
    elif sort_metric == "Lists":
        return sorted(data, key=lambda x: x.get("different_lists_count", 0), reverse=reverse)
    elif sort_metric == "Entries":
        return sorted(data, key=lambda x: x.get("popularity", x.get("count", 0)), reverse=reverse)
    return sorted(data, key=lambda x: x["games"], reverse=reverse)


@router.get("")
def get_squadrons(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Games"),
    sort_direction: str = Query("desc"),
    epic: bool = Query(False),

    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    platforms: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
    min_games: int = Query(0, ge=0),
):
    filters: dict = {}
    if formats:
        filters["allowed_formats"] = formats
    if factions:
        filters["factions"] = factions
    if ships:
        filters["ships"] = ships
    filters["platforms"] = platforms
    filters["continent"] = continent
    filters["country"] = country
    filters["city"] = city
    filters["date_start"] = date_start
    filters["date_end"] = date_end
    filters["player_count_min"] = player_count_min
    filters["player_count_max"] = player_count_max
    filters["min_games"] = min_games
    filters["epic"] = epic

    # Build a stable cache key from all inputs that affect the response.
    # page/size excluded — pagination is done AFTER caching.
    # sort_metric/sort_direction excluded — sorting is done AFTER caching.
    cache_key = (
        f"squadrons|{data_source}|"
        f"{','.join(sorted(formats or []))}|"
        f"{','.join(sorted(factions or []))}|"
        f"{','.join(sorted(ships or []))}|"
        f"{','.join(sorted(platforms or []))}|"
        f"{','.join(sorted(continent or []))}|"
        f"{','.join(sorted(country or []))}|"
        f"{','.join(sorted(city or []))}|"
        f"{date_start or ''}|{date_end or ''}|"
        f"{player_count_min}|{player_count_max}|"
        f"{min_games}|{epic}"
    )

    def compute():
        return _compute_squadrons(
            data_source=data_source,
            filters=filters,
        )

    cached = get_cached_or_compute(cache_key, compute)

    # Sort AFTER the cache lookup — the heavy aggregation is sort-independent.
    filtered = _sort_squadron_stats(cached["filtered"], sort_metric, sort_direction)

    # Paginate + enrich AFTER cache (only enriches the current page slice)
    total = cached["total"]
    items_raw = filtered[page * size : (page + 1) * size]

    all_ships = load_all_ships(DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA)
    items = []
    for s in items_raw:
        pilots = []
        for ship_xws in s["ships"]:
            s_info = all_ships.get(ship_xws, {})
            pilots.append({
                "ship_name": s_info.get("name", ship_xws),
                "ship_icon": ship_xws,
            })
        items.append({
            "signature": s["signature"],
            "faction": s["faction"],
            "faction_key": s["faction"],
            "games": s["games"],
            "win_rate": s["win_rate"],
            "count": s["popularity"],
            "different_lists_count": s.get("different_lists_count", s["popularity"]),
            "pilots": pilots,
        })

    return {"items": items, "total": total, "page": page, "size": size}
