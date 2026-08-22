"""
Ship Detail API endpoints.

Provides ship info, pilot breakdown, top lists, and top squadrons.
"""
from fastapi import APIRouter, Query
from collections import defaultdict

from ..analytics.ships import aggregate_ship_stats
from ..analytics.lists import aggregate_list_stats, fetch_list_pilots
from ..analytics.squadrons import aggregate_squadron_stats
from ..analytics.core import aggregate_card_stats
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from ..utils.xwing_data.ships import load_all_ships
from .formatters import enrich_list_data

router = APIRouter(prefix="/api/ship", tags=["Ship Detail"])


@router.get("/{ship_xws}")
def get_ship_info(
    ship_xws: str,
    data_source: str = Query("xwa"),
):
    """Return static ship info and top-level stats."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    all_ships = load_all_ships(ds)
    info = all_ships.get(ship_xws, {"name": ship_xws, "xws": ship_xws, "factions": []})
    
    # Get overall stats for this ship
    filters = {"ship": [ship_xws]}
    stats = aggregate_ship_stats(filters, SortingCriteria.GAMES, SortDirection.DESCENDING, ds)
    
    stat_info = stats[0] if stats and len(stats) > 0 else {}
    return {
        "info": info,
        "stats": stat_info
    }


@router.get("/{ship_xws}/pilots")
def get_ship_pilots(
    ship_xws: str,
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Lists"),
    sort_direction: str = Query("desc"),
    epic: bool = Query(False),
):
    """Return pilot stats filtered to this ship."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    criteria_map = {
        "Lists": SortingCriteria.LISTS,
        "Unique Lists": SortingCriteria.UNIQUE_LISTS,
        "Win Rate": SortingCriteria.WINRATE,
        "Games": SortingCriteria.GAMES,
    }
    criteria = criteria_map.get(sort_metric, SortingCriteria.LISTS)
    direction = SortDirection.DESCENDING if sort_direction == "desc" else SortDirection.ASCENDING

    filters = {
        "ship": [ship_xws],
        # Huge-ship pilots are flagged `epic` in the manifest; the ships page
        # only shows them when "Include Epic" is on, so their detail page must
        # include them too or the pilot list comes back empty.
        "include_epic": epic,
    }
    data = aggregate_card_stats(filters, criteria, direction, "pilots", ds)
    return {"pilots": data}


@router.get("/{ship_xws}/lists")
def get_ship_lists(
    ship_xws: str,
    data_source: str = Query("xwa"),
    limit: int = Query(10, ge=1, le=50),
):
    """Return top performing lists containing this ship."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    filters = {"ship": [ship_xws]}
    data = aggregate_list_stats(filters, data_source=ds)
    
    # Take top N that have a minimum number of games to avoid 100% WR outliers
    filtered_data = [d for d in data if d.get("games", 0) >= 5]
    filtered_data.sort(key=lambda x: x.get("win_rate", 0), reverse=True)
    if not filtered_data:
        filtered_data = data  # Fallback if no robust lists

    top = filtered_data[:limit]
    signatures: list[str] = [l["signature"] for l in top if l.get("signature")]
    pilots_map = fetch_list_pilots(signatures) if signatures else {}
    # Attach lazily-fetched pilots (aggregation returns empty pilots now);
    # copy rows so the shared aggregation result is never mutated.
    enriched = [
        {**l, "pilots": pilots_map.get(l["signature"], [])}
        for l in top
        if l.get("signature")
    ]
    return {"lists": [enrich_list_data(l, source=ds) for l in enriched]}


@router.get("/{ship_xws}/squadrons")
def get_ship_squadrons(
    ship_xws: str,
    data_source: str = Query("xwa"),
    limit: int = Query(10, ge=1, le=50),
):
    """Return top performing squadrons containing this ship."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    filters = {"ship": [ship_xws]}
    data = aggregate_squadron_stats(filters, SortingCriteria.WINRATE, SortDirection.DESCENDING, ds)
    
    filtered_data = [d for d in data if d.get("games", 0) >= 5]
    if not filtered_data:
        filtered_data = data
        
    return {"squadrons": filtered_data[:limit]}
