from fastapi import APIRouter, Query
from ..analytics.squadrons import aggregate_squadron_stats
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from .schemas import PaginatedListsResponse, ListData, PilotData
from ..utils.xwing_data.ships import get_ship_icon_name

router = APIRouter(prefix="/api/squadrons", tags=["Squadrons"])

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
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    filters = {}
    if formats:
        filters["allowed_formats"] = formats
    if ships:
        filters["ships"] = ships
        
    raw_data = aggregate_squadron_stats(filters, sort_metric=SortingCriteria.GAMES, sort_direction=SortDirection.DESCENDING, data_source=ds_enum)
    
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
    items_raw = filtered_data[page * size : (page + 1) * size]
    
    items = []
    for s in items_raw:
        # Create minimal pilots representation just for showing ships properly in UI
        from ..utils.xwing_data.ships import load_all_ships
        all_ships = load_all_ships(ds_enum)
        
        pilots = []
        for ship_xws in s['ships']:
            s_info = all_ships.get(ship_xws, {})
            pilots.append({
                "ship_name": s_info.get("name", ship_xws),
                "ship_icon": ship_xws
            })
            
        items.append({
            "signature": s["signature"],
            "faction": s["faction"],
            "faction_key": s["faction"],
            "games": s["games"],
            "win_rate": s["win_rate"],
            "count": s["popularity"],
            "pilots": pilots
        })
    
    return {"items": items, "total": total, "page": page, "size": size}
