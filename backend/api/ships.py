from fastapi import APIRouter, Query, Depends
from ..analytics.ships import aggregate_ship_stats
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from .schemas import PaginatedShipsResponse
from ..utils.xwing_data.ships import load_all_ships

router = APIRouter(prefix="/api/ships", tags=["Ships"])

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
    size: int = Query(20, ge=1, le=100),
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
    sources: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
):
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

    filters = {
        "allowed_formats": formats,
        "faction": factions,
        "ship": ships,
        "continent": continent,
        "country": country,
        "city": city,
        "search_name": search,
        "sources": sources,
        "date_start": date_start,
        "date_end": date_end,
        "player_count_min": player_count_min,
        "player_count_max": player_count_max,
    }

    data = aggregate_ship_stats(filters, criteria, s_dir, ds_enum)
    total = len(data)
    items = data[page * size : (page + 1) * size]
    
    return PaginatedShipsResponse(items=items, total=total, page=page, size=size)
