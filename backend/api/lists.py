from fastapi import APIRouter, Query
from typing import Optional, List
from ..analytics.lists import aggregate_list_stats
from ..data_structures.data_source import DataSource
from .schemas import PaginatedListsResponse
from .formatters import enrich_list_data

router = APIRouter(prefix="/api/lists", tags=["Lists"])

@router.get("", response_model=PaginatedListsResponse)
def get_lists(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Games"),
    sort_direction: str = Query("desc"),
    
    formats: Optional[List[str]] = Query(None),
    factions: Optional[List[str]] = Query(None),
    ships: Optional[List[str]] = Query(None),
    min_games: int = Query(0, ge=0),
    points_min: int = Query(0, ge=0),
    points_max: int = Query(200, ge=0),
    platforms: Optional[List[str]] = Query(None),
    continent: Optional[List[str]] = Query(None),
    country: Optional[List[str]] = Query(None),
    city: Optional[List[str]] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    player_count_min: Optional[int] = Query(None),
    player_count_max: Optional[int] = Query(None),
):
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    filters = {
        "platforms": platforms,
        "continent": continent,
        "country": country,
        "city": city,
        "date_start": date_start,
        "date_end": date_end,
        "player_count_min": player_count_min,
        "player_count_max": player_count_max,
        "ships": ships,
    }
    if formats:
        filters["allowed_formats"] = formats
        
    raw_data = aggregate_list_stats(filters, limit=2000, data_source=ds_enum)
    
    filtered_data = []
    for row in raw_data:
        if factions and row["faction"] not in factions:
            continue
        if row["games"] < min_games:
            continue
        if row["points"] < points_min or row["points"] > points_max:
            continue
        filtered_data.append(row)
        
    reverse = sort_direction == "desc"
    if sort_metric == "Win Rate":
        filtered_data.sort(key=lambda x: x["win_rate"], reverse=reverse)
    elif sort_metric == "Points Cost":
        filtered_data.sort(key=lambda x: x["points"], reverse=reverse)
    else: 
        filtered_data.sort(key=lambda x: x["games"], reverse=reverse)
        
    total = len(filtered_data)
    items_raw = filtered_data[page * size : (page + 1) * size]
    items = [enrich_list_data(i, source=ds_enum) for i in items_raw]
    
    return PaginatedListsResponse(items=items, total=total, page=page, size=size)
