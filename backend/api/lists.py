from fastapi import APIRouter, Depends
from ..analytics.lists import aggregate_list_stats
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from .schemas import PaginatedListsResponse, ListData, PilotData, UpgradeData
from .filters import BaseFilterParams

router = APIRouter(prefix="/api/lists", tags=["Lists"])

@router.get("", response_model=PaginatedListsResponse)
def get_lists(
    filters: BaseFilterParams = Depends(),
):
    try:
        ds_enum = DataSource(filters.data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    # For now aggregate_list_stats takes raw filters, but we map standard ones
    # In a full refactor, aggregate_list_stats should take the Filter object
    raw_data = aggregate_list_stats({}, sort_metric=SortingCriteria.GAMES, sort_direction=SortDirection.DESCENDING, data_source=ds_enum)
    
    total = len(raw_data)
    items_raw = raw_data[filters.page * filters.size : (filters.page + 1) * filters.size]
    
    items = []
    for l in items_raw:
        pilots = []
        for p in l.get("pilots", []):
            upgrades = []
            if isinstance(p.get("upgrades"), dict):
                for slot, items_list in p["upgrades"].items():
                    if isinstance(items_list, list):
                        for u_name in items_list:
                            # Standardize identifiers for Option A
                            xws_clean = u_name.lower().replace(" ", "")
                            upgrades.append(UpgradeData(name=u_name, xws=xws_clean, slot=slot))
            
            # Map identifiers to xws fields
            pilot_id = p.get("id", "")
            pilot_xws = pilot_id.lower().replace(" ", "")
            ship_name_raw = p.get("ship_name", "")
            ship_icon = ship_name_raw.lower().replace(" ", "").replace("-", "")
            
            pilots.append(PilotData(
                name=p.get("name", ""),
                xws=pilot_xws,
                ship_name=ship_name_raw,
                ship_icon=ship_icon,
                points=p.get("points", 0),
                loadout=p.get("loadout", 0),
                upgrades=upgrades
            ))
            
        faction_raw = l.get("faction", "")
        faction_xws = faction_raw.lower().replace(" ", "").replace("-", "")

        items.append(ListData(
            signature=l["signature"],
            name=l.get("name", "Untitled"),
            faction=faction_raw,
            faction_xws=faction_xws,
            points=l.get("points", 0),
            original_points=l.get("points", 0),
            count=l.get("popularity", 0),
            games=l.get("games", 0),
            win_rate=l.get("win_rate", 0.0),
            total_loadout=0,
            pilots=pilots
        ))
        
    return PaginatedListsResponse(items=items, total=total, page=filters.page, size=filters.size)
