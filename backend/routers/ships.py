"""
Ships API router.

Exposes endpoints used by the frontend Ships / Chassis page.
"""
from fastapi import APIRouter, Query
from ..utils.xwing_data.ships import get_filtered_ships
from ..data_structures.data_source import DataSource

router = APIRouter(tags=["ships"])


@router.get("/ships")
def list_ships(
    faction: str | None = Query(default=None, description="Filter by faction XWS id"),
    source: str = Query(default="xwa", description="Data source: xwa or legacy"),
):
    """
    Return all ships, optionally filtered by faction.

    Each item represents a unique ship chassis with name, xws id, faction,
    size, stats, actions and maneuvers.
    """
    data_source = DataSource.LEGACY if source.lower() == "legacy" else DataSource.XWA

    # get_filtered_ships already handles "all" / faction filtering
    faction_arg = faction if faction else "all"
    ships = get_filtered_ships(faction_filter=faction_arg, source=data_source)
    return ships
