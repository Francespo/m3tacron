from fastapi import APIRouter, Depends
from ..analytics.core import aggregate_card_stats
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from .schemas import PaginatedPilotsResponse, PaginatedUpgradesResponse, PilotRow, UpgradeRow
from .filters import PilotFilterParams, BaseFilterParams

router = APIRouter(prefix="/api/cards", tags=["Cards"])

@router.get("/pilots", response_model=PaginatedPilotsResponse)
def get_pilots(
    filters: PilotFilterParams = Depends(),
):
    try:
        ds_enum = DataSource(filters.data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    # Map filter params to analytics engine
    a_filters = {}
    if filters.factions:
        a_filters["faction"] = filters.factions
    if filters.ships:
        a_filters["ship"] = filters.ships
    if filters.points_min is not None:
        a_filters["points_min"] = filters.points_min
    if filters.points_max is not None:
        a_filters["points_max"] = filters.points_max

    raw_data = aggregate_card_stats(a_filters, mode="pilots", data_source=ds_enum)
    
    # Sort and Paginate
    reverse = filters.sort_direction == "desc"
    # Sorting is already done in aggregate_card_stats, but we can override if needed
    # For now we trust the engine or keep our manual override if we want consistency with schemas
    if filters.sort_metric == "Win Rate":
        def sort_key(x):
            wr = x.get("win_rate", 0)
            return float(wr) if wr != "NA" else -1.0
        raw_data.sort(key=sort_key, reverse=reverse)
    elif filters.sort_metric == "Games":
        raw_data.sort(key=lambda x: x.get("games", 0), reverse=reverse)
    else: # Popularity / Count
        raw_data.sort(key=lambda x: x.get("count", 0), reverse=reverse)
        
    total = len(raw_data)
    items_raw = raw_data[filters.page * filters.size : (filters.page + 1) * filters.size]
    
    items = []
    for p in items_raw:
        items.append(PilotRow(
            name=p["name"],
            xws=p["xws"],
            count=p["count"],
            popularity=p["count"],
            wins=p["wins"],
            games=p["games"],
            lists=p["count"],
            faction=p.get("faction", "Unknown"),
            faction_xws=p.get("faction_xws", ""),
            ship=p.get("ship", "Unknown"),
            ship_xws=p.get("ship_xws", ""),
            ship_icon=p.get("ship_icon", ""),
            image=p.get("image", ""),
            cost=p.get("cost", 0),
            loadout=p.get("loadout", 0),
            win_rate=p.get("win_rate", 0.0) if p.get("win_rate") != "NA" else 0.0,
            icon_char=p.get("icon_char", "")
        ))
        
    return PaginatedPilotsResponse(items=items, total=total, page=filters.page, size=filters.size)

@router.get("/upgrades", response_model=PaginatedUpgradesResponse)
def get_upgrades(
    filters: BaseFilterParams = Depends(),
):
    try:
        ds_enum = DataSource(filters.data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    raw_data = aggregate_card_stats({}, mode="upgrades", data_source=ds_enum)
    
    # Simple default sort for upgrades in generic view
    raw_data.sort(key=lambda x: x.get("count", 0), reverse=True)
    
    total = len(raw_data)
    items_raw = raw_data[filters.page * filters.size : (filters.page + 1) * filters.size]
    
    items = []
    for u in items_raw:
        items.append(UpgradeRow(
            name=u["name"],
            xws=u["xws"],
            type=u.get("type", "Unknown"),
            count=u["count"],
            popularity=u["count"],
            wins=u["wins"],
            games=u["games"],
            lists=u["count"],
            image=u.get("image", ""),
            cost=u.get("cost", 0),
            win_rate=u.get("win_rate", 0.0) if u.get("win_rate") != "NA" else 0.0
        ))
        
    return PaginatedUpgradesResponse(items=items, total=total, page=filters.page, size=filters.size)
