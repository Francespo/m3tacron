from fastapi import APIRouter, Query, Depends
from ..analytics.ships import aggregate_ship_stats
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from .schemas import PaginatedShipsResponse
from ..utils.xwing_data.ships import load_all_ships
from ..cache import get_cached_or_compute

router = APIRouter(prefix="/api/ships", tags=["Ships"])


def _compute_ships(
    data_source: str,
    filters: dict,
) -> list[dict]:
    """Run the expensive ship aggregation.

    The heavy SQL aggregation is sort-independent, so it always runs with a
    neutral sort (Lists desc). The caller applies the requested sort to the
    cached list before paginating — see _sort_ship_stats.
    """
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    return aggregate_ship_stats(
        filters,
        SortingCriteria.LISTS,
        SortDirection.DESCENDING,
        ds_enum,
    )


def _sort_ship_stats(data: list[dict], sort_metric: str, sort_direction: str) -> list[dict]:
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
        return (item.get("list_count", 0), item.get("games_count", 0))

    return sorted(data, key=sort_key, reverse=(sort_direction == "desc"))


@router.get("/all")
def get_all_ships(data_source: str = Query("xwa")):
    """Return every chassis once, with all playable factions merged."""
    ds_enum = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    ships_data = load_all_ships(ds_enum)

    # Extract ships directly with all their factions
    results: list[dict] = []
    for xws, info in ships_data.items():
        factions_xws = [
            f.lower().replace(" ", "") if f else "unknown"
            for f in info.get("factions", [])
        ]
        results.append({
            "xws": xws,
            "name": info.get("name", xws),
            "factions": list(set(factions_xws)),
        })

    results = sorted(results, key=lambda x: x["name"])
    return results


@router.get("", response_model=PaginatedShipsResponse)
def get_ships(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=200),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Lists"),
    sort_direction: str = Query("desc"),
    search: str | None = Query(None),

    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    platforms: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
):
    filters = {
        "allowed_formats": formats,
        "faction": factions,
        "ship": ships,
        "continent": continent,
        "country": country,
        "city": city,
        "search_name": search,
        "platforms": platforms,
        "date_start": date_start,
        "date_end": date_end,
        "player_count_min": player_count_min,
        "player_count_max": player_count_max,
    }

    # page/size excluded — pagination is done AFTER caching.
    cache_key = (
        f"ships|{data_source}"
        f"|{','.join(sorted(formats or []))}"
        f"|{','.join(sorted(factions or []))}"
        f"|{','.join(sorted(ships or []))}"
        f"|{search or ''}"
        f"|{','.join(sorted(platforms or []))}"
        f"|{','.join(sorted(continent or []))}"
        f"|{','.join(sorted(country or []))}"
        f"|{','.join(sorted(city or []))}"
        f"|{date_start or ''}|{date_end or ''}"
        f"|{player_count_min}|{player_count_max}"
    )

    def compute():
        return _compute_ships(
            data_source=data_source,
            filters=filters,
        )

    data = get_cached_or_compute(cache_key, compute)
    # Sort AFTER the cache lookup — the heavy aggregation is sort-independent.
    data = _sort_ship_stats(data, sort_metric, sort_direction)
    total = len(data)
    items = data[page * size : (page + 1) * size]

    return PaginatedShipsResponse(items=list(items), total=total, page=page, size=size)
