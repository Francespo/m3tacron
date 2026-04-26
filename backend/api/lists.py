from fastapi import APIRouter, Query
from ..analytics.lists import aggregate_list_stats
from ..data_structures.data_source import DataSource
from ..data_structures.factions import Faction
from .schemas import PaginatedListsResponse

router = APIRouter(prefix="/api/lists", tags=["Lists"])

# Helper to match faction filter
def _match_faction(f_enum: Faction, allowed_list: list[str]) -> bool:
    if not allowed_list: return True
    # allowed_list has strings like "rebelalliance", "rebel", etc.
    # f_enum is normalized.
    # Normalize allowed list
    norm_allowed = {f.lower().replace(" ", "").replace("-", "") for f in allowed_list}
    return f_enum.value.replace("-", "") in norm_allowed

@router.get("", response_model=PaginatedListsResponse)
def get_lists(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Games"),
    sort_direction: str = Query("desc"),
    
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    min_games: int = Query(0, ge=0),
    points_min: int = Query(0, ge=0),
    points_max: int = Query(200, ge=0),
    sources: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
):
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    filters = {
        "sources": sources,
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
        
    # Get raw data (already ListData compatible dicts)
    raw_data = aggregate_list_stats(filters, limit=2000, data_source=ds_enum)
    
    filtered_data = []
    for row in raw_data:
        points = row.get("points") or 0

        # Faction check
        if factions and not _match_faction(row["faction_xws"], factions):
            continue
            
        if row["games"] < min_games:
            continue
        if points < points_min or points > points_max:
            continue

        row["points"] = points
        filtered_data.append(row)
        
    reverse = sort_direction == "desc"
    
    def get_win_rate(r):
        return r["wins"] / r["games"] if r["games"] > 0 else 0.0

    if sort_metric == "Win Rate":
        filtered_data.sort(key=get_win_rate, reverse=reverse)
    elif sort_metric == "Points Cost":
        filtered_data.sort(key=lambda x: x["points"], reverse=reverse)
    else: 
        filtered_data.sort(key=lambda x: x["games"], reverse=reverse)
        
    total = len(filtered_data)
    items = filtered_data[page * size : (page + 1) * size]
    
    # Enrichment removed as ListData is structural-data only, and stats are populated.
    
    return PaginatedListsResponse(items=items, total=total, page=page, size=size)
