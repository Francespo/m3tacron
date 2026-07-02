from fastapi import APIRouter, Query, Depends
from ..analytics.ships import aggregate_ship_stats
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from .schemas import PaginatedShipsResponse
from ..utils.xwing_data.ships import load_all_ships
from ..cache import get_cached_or_compute

router = APIRouter(prefix="/api/ships", tags=["Ships"])


def _compute_ships(
    page: int,
    size: int,
    data_source: str,
    sort_metric: str,
    sort_direction: str,
    filters: dict,
) -> list[dict]:
    """Run the expensive ship aggregation. Returns the full sorted list (caller paginates)."""
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    criteria_map = {
        "Games": SortingCriteria.GAMES,
        "Popularity": SortingCriteria.POPULARITY,
        "Win Rate": SortingCriteria.WINRATE,
    }
    criteria = criteria_map.get(sort_metric, SortingCriteria.POPULARITY)
    s_dir = SortDirection.DESCENDING if sort_direction == "desc" else SortDirection.ASCENDING

    return aggregate_ship_stats(filters, criteria, s_dir, ds_enum)


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
    sort_metric: str = Query("Popularity"),
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
        f"ships|{data_source}|{sort_metric}|{sort_direction}"
        f"|{','.join(sorted(formats or []))}"
        f"|{','.join(sorted(factions or []))}"
        f"|{','.join(sorted(ships or []))}"
        f"|{search or ''}"
    )

    def compute():
        return _compute_ships(
            page=page, size=size, data_source=data_source,
            sort_metric=sort_metric, sort_direction=sort_direction,
            filters=filters,
        )

    data = get_cached_or_compute(cache_key, compute)
    total = len(data)
    items = data[page * size : (page + 1) * size]

    return PaginatedShipsResponse(items=list(items), total=total, page=page, size=size)
