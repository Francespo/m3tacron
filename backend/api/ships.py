from fastapi import APIRouter, Depends
from ..analytics.ships import aggregate_ship_stats
from ..data_structures.data_source import DataSource
from .schemas import PaginatedShipsResponse, ShipRow
from .filters import ShipFilterParams

router = APIRouter(prefix="/api/ships", tags=["Ships"])

@router.get("", response_model=PaginatedShipsResponse)
def get_ships(
    filters: ShipFilterParams = Depends(),
):
    try:
        ds_enum = DataSource(filters.data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    # Map filter params to analytics engine
    a_filters = {}
    if filters.factions:
        a_filters["faction"] = filters.factions # Ships analytics uses 'faction' not 'factions'
    if filters.ships:
        a_filters["ship"] = filters.ships # Ships analytics uses 'ship' not 'ships'

    raw_data = aggregate_ship_stats(a_filters, data_source=ds_enum)
    
    # Sort and Paginate
    reverse = filters.sort_direction == "desc"
    if filters.sort_metric == "Win Rate":
        def sort_key(x):
            wr = x.get("win_rate", 0)
            return float(wr) if wr != "NA" else -1.0
        raw_data.sort(key=sort_key, reverse=reverse)
    elif filters.sort_metric == "Games":
        raw_data.sort(key=lambda x: x.get("games", 0), reverse=reverse)
    else: # Popularity / Count
        raw_data.sort(key=lambda x: x.get("popularity", 0), reverse=reverse)
        
    total = len(raw_data)
    items_raw = raw_data[filters.page * filters.size : (filters.page + 1) * filters.size]
    
    items = []
    for s in items_raw:
        items.append(ShipRow(
            ship_name=s["ship_name"],
            ship_xws=s["ship_xws"],
            faction=s.get("faction", "Unknown"),
            faction_xws=s.get("faction_xws", ""),
            icon_char=s.get("icon_char", ""),
            win_rate=s.get("win_rate", 0.0) if s.get("win_rate") != "NA" else 0.0,
            popularity=s.get("popularity", 0),
            games=s.get("games", 0),
            pilots_count=s.get("pilots_count", 0)
        ))
        
    return PaginatedShipsResponse(items=items, total=total, page=filters.page, size=filters.size)
