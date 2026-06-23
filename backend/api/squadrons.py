from fastapi import APIRouter, Query
from ..analytics.squadrons import aggregate_squadron_stats
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..cache import get_cached_or_compute
from ..utils.xwing_data.ships import load_all_ships

router = APIRouter(prefix="/api/squadrons", tags=["Squadrons"])


def _compute_squadrons(
    page: int,
    size: int,
    data_source: str,
    sort_metric: str,
    sort_direction: str,
    filters: dict,
) -> dict:
    """Run the expensive aggregation + post-filter + sort.

    Returns a dict with `filtered` (full sorted list), `total`, and
    `page`/`size` for the caller to paginate and enrich.
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

    reverse = sort_direction == "desc"
    if sort_metric == "Win Rate":
        filtered_data.sort(key=lambda x: x["win_rate"], reverse=reverse)
    else:
        filtered_data.sort(key=lambda x: x["games"], reverse=reverse)

    total = len(filtered_data)

    return {"filtered": filtered_data, "total": total, "page": page, "size": size}


@router.get("")
def get_squadrons(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Games"),
    sort_direction: str = Query("desc"),

    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    min_games: int = Query(0, ge=0),
):
    filters: dict = {}
    if formats:
        filters["allowed_formats"] = formats
    if factions:
        filters["factions"] = factions
    if ships:
        filters["ships"] = ships
    filters["min_games"] = min_games

    # Build a stable cache key from all inputs that affect the response.
    # page/size excluded — pagination is done AFTER caching.
    cache_key = (
        f"squadrons|{data_source}|"
        f"{','.join(sorted(formats or []))}|"
        f"{','.join(sorted(factions or []))}|"
        f"{','.join(sorted(ships or []))}|"
        f"{min_games}|{sort_metric}|{sort_direction}"
    )

    def compute():
        return _compute_squadrons(
            page=page, size=size, data_source=data_source,
            sort_metric=sort_metric, sort_direction=sort_direction,
            filters=filters,
        )

    cached = get_cached_or_compute(cache_key, compute)

    # Paginate + enrich AFTER cache (only enriches the current page slice)
    filtered = cached["filtered"]
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
            "pilots": pilots,
        })

    return {"items": items, "total": total, "page": page, "size": size}
