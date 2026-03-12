from .filters import BaseFilterParams
from fastapi import APIRouter, Query, Depends
from .schemas import (
    ShipDetailResponse, ShipPilotsResponse, ShipListsResponse, 
    ShipSquadronsResponse, PilotRow, SquadronRow
)

router = APIRouter(prefix="/api/ship", tags=["Ship Detail"])

@router.get("/{ship_xws}", response_model=ShipDetailResponse)
def get_ship_info(
    ship_xws: str,
    filters: BaseFilterParams = Depends(),
):
    ds = DataSource(filters.data_source) if filters.data_source in ("xwa", "legacy") else DataSource.XWA
    all_ships = load_all_ships(ds)
    info = all_ships.get(ship_xws, {"name": ship_xws, "xws": ship_xws, "factions": []})
    stats = aggregate_ship_stats({"ship": [ship_xws]}, SortingCriteria.GAMES, SortDirection.DESCENDING, ds)
    stat_info = stats[0] if stats else {}
    return ShipDetailResponse(info=info, stats=stat_info)

@router.get("/{ship_xws}/pilots", response_model=ShipPilotsResponse)
def get_ship_pilots(
    ship_xws: str,
    filters: BaseFilterParams = Depends(),
    sort_metric: str = Query("Popularity"),
    sort_direction: str = Query("desc"),
):
    ds = DataSource(filters.data_source) if filters.data_source in ("xwa", "legacy") else DataSource.XWA
    criteria = SortingCriteria.from_label(sort_metric)
    direction = SortDirection.DESCENDING if sort_direction == "desc" else SortDirection.ASCENDING
    data = aggregate_card_stats({"ship": [ship_xws], "include_epic": False}, criteria, direction, "pilots", ds)
    return ShipPilotsResponse(pilots=[PilotRow(**p) for p in data])

@router.get("/{ship_xws}/lists", response_model=ShipListsResponse)
def get_ship_lists(
    ship_xws: str,
    filters: BaseFilterParams = Depends(),
    limit: int = Query(10, ge=1, le=50),
):
    ds = DataSource(filters.data_source) if filters.data_source in ("xwa", "legacy") else DataSource.XWA
    data = aggregate_list_stats({"ship": [ship_xws]}, limit=50, sort_metric="win_rate", sort_direction="desc", data_source=ds)
    filtered_data = [d for d in data if d.get("games", 0) >= 5]
    if not filtered_data: filtered_data = data
    return ShipListsResponse(lists=[enrich_list_data(l, source=ds) for l in filtered_data[:limit]])

@router.get("/{ship_xws}/squadrons", response_model=ShipSquadronsResponse)
def get_ship_squadrons(
    ship_xws: str,
    filters: BaseFilterParams = Depends(),
    limit: int = Query(10, ge=1, le=50),
):
    ds = DataSource(filters.data_source) if filters.data_source in ("xwa", "legacy") else DataSource.XWA
    data = aggregate_squadron_stats({"ship": [ship_xws]}, SortingCriteria.WINRATE, SortDirection.DESCENDING, ds)
    filtered_data = [d for d in data if d.get("games", 0) >= 5]
    if not filtered_data: filtered_data = data
    return ShipSquadronsResponse(squadrons=[SquadronRow(**s) for s in filtered_data[:limit]])
