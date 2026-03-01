from fastapi import APIRouter, Query, Depends
from typing import Optional, List, Dict, Any
from ..analytics.ships import aggregate_ship_stats
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from .schemas import PaginatedShipsResponse

router = APIRouter(prefix="/api/ships", tags=["Ships"])

@router.get("", response_model=PaginatedShipsResponse)
def get_ships(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Popularity"),
    sort_direction: str = Query("desc"),
    
    formats: Optional[List[str]] = Query(None),
    factions: Optional[List[str]] = Query(None),
    ships: Optional[List[str]] = Query(None),
    continent: Optional[List[str]] = Query(None),
    country: Optional[List[str]] = Query(None),
    city: Optional[List[str]] = Query(None),
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
    }

    data = aggregate_ship_stats(filters, criteria, s_dir, ds_enum)
    total = len(data)
    items = data[page * size : (page + 1) * size]
    
    return PaginatedShipsResponse(items=items, total=total, page=page, size=size)
