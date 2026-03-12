from fastapi import APIRouter, Depends
from ..analytics.squadrons import aggregate_squadron_stats
from ..data_structures.data_source import DataSource
from .schemas import PaginatedSquadronsResponse, SquadronRow
from .filters import SquadronFilterParams

router = APIRouter(prefix="/api/squadrons", tags=["Squadrons"])

@router.get("", response_model=PaginatedSquadronsResponse)
def get_squadrons(
    filters: SquadronFilterParams = Depends(),
):
    try:
        ds_enum = DataSource(filters.data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    # Squadron stats currently uses raw dict filters
    # We pass what we have
    raw_data = aggregate_squadron_stats(filters.dict(), data_source=ds_enum)
    
    # Sort and Paginate
    reverse = filters.sort_direction == "desc"
    if filters.sort_metric == "Win Rate":
        raw_data.sort(key=lambda x: x.get("win_rate", 0), reverse=reverse)
    elif filters.sort_metric == "Count":
        raw_data.sort(key=lambda x: x.get("count", 0), reverse=reverse)
    else: # Default: Games
        raw_data.sort(key=lambda x: x.get("games", 0), reverse=reverse)
        
    total = len(raw_data)
    items_raw = raw_data[filters.page * filters.size : (filters.page + 1) * filters.size]
    
    items = []
    for sq in items_raw:
        faction_raw = sq.get("faction", "Unknown")
        faction_xws = faction_raw.lower().replace(" ", "").replace("-", "")
        
        items.append(SquadronRow(
            signature=sq["signature"],
            faction=faction_raw,
            faction_xws=faction_xws,
            games=sq.get("games", 0),
            win_rate=sq.get("win_rate", 0.0),
            count=sq.get("count", 0),
            pilots=[] # Plural squadrons list view doesn't return pilots usually
        ))
        
    return PaginatedSquadronsResponse(items=items, total=total, page=filters.page, size=filters.size)
