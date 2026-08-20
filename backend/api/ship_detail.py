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
from ..cache import get_cached_or_compute
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from ..utils.xwing_data.ships import load_all_ships
from .formatters import enrich_list_data

router = APIRouter(prefix="/api/ship", tags=["Ship Detail"])


@router.get("/{ship_xws}")
def get_ship_info(
    ship_xws: str,
    data_source: str = Query("xwa"),
    faction: str | None = Query(None),
):
    """Return static ship info and top-level stats.

    `faction` optionally restricts the stats to that faction (same filter
    the /ships page faction toggle uses), so the key metrics recompute when
    the user switches factions on this page.
    """
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    all_ships = load_all_ships(ds)
    info = all_ships.get(ship_xws, {"name": ship_xws, "xws": ship_xws, "factions": []})
    
    # Get overall stats for this ship (optionally faction-scoped), cached.
    cache_key = f"ship_info|{ship_xws}|{ds}|{faction or 'all'}"

    def compute():
        filters = {"ship": [ship_xws]}
        if faction and faction != "all":
            filters["faction"] = faction
        stats = aggregate_ship_stats(filters, SortingCriteria.GAMES, SortDirection.DESCENDING, ds)
        return stats[0] if stats and len(stats) > 0 else {}

    stat_info = get_cached_or_compute(cache_key, compute)
    return {
        "info": info,
        "stats": stat_info,
        "faction": faction or "all",
    }


@router.get("/{ship_xws}/pilots")
def get_ship_pilots(
    ship_xws: str,
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Lists"),
    sort_direction: str = Query("desc"),
    faction: str | None = Query(None),
    epic: bool = Query(False),
):
    """Return pilot stats filtered to this ship.

    `faction` optionally restricts to pilots that flew under that faction
    (lists whose squad faction matches). The faction stats are computed by
    the same SQL aggregation the /ships page uses, so the numbers stay
    consistent with the per-faction toggle there. `epic` controls whether
    Huge-ship pilots are included (matches the ships-page toggle).
    """
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    criteria_map = {
        "Lists": SortingCriteria.LISTS,
        "Unique Lists": SortingCriteria.UNIQUE_LISTS,
        "Win Rate": SortingCriteria.WINRATE,
        "Games": SortingCriteria.GAMES,
    }
    criteria = criteria_map.get(sort_metric, SortingCriteria.LISTS)
    direction = SortDirection.DESCENDING if sort_direction == "desc" else SortDirection.ASCENDING

    cache_key = f"ship_pilots|{ship_xws}|{ds}|{sort_metric}|{sort_direction}|{faction or 'all'}|{epic}"

    def compute():
        filters = {
            "ship": [ship_xws],
            # Huge-ship pilots are flagged `epic` in the manifest; the ships page
            # only shows them when "Include Epic" is on, so their detail page must
            # include them too or the pilot list comes back empty.
            "include_epic": epic,
        }
        if faction and faction != "all":
            filters["faction"] = faction
        return aggregate_card_stats(filters, criteria, direction, "pilots", ds)

    data = get_cached_or_compute(cache_key, compute)
    return {"pilots": data, "faction": faction or "all"}


@router.get("/{ship_xws}/lists")
def get_ship_lists(
    ship_xws: str,
    data_source: str = Query("xwa"),
    limit: int = Query(10, ge=1, le=50),
    faction: str | None = Query(None),
):
    """Return top performing lists containing this ship.

    `faction` optionally restricts to lists whose squad faction matches
    (same filter the /ships page faction toggle uses), so the lists stay
    consistent with the pilots breakdown.
    """
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    cache_key = f"ship_lists|{ship_xws}|{ds}|{limit}|{faction or 'all'}"

    def compute():
        filters = {"ship": [ship_xws]}
        if faction and faction != "all":
            filters["factions"] = [faction]
        return aggregate_list_stats(filters, data_source=ds)

    data = get_cached_or_compute(cache_key, compute)
    
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
    faction: str | None = Query(None),
):
    """Return top performing squadrons containing this ship.

    `faction` optionally restricts to squadrons whose faction matches, so
    the squadrons stay consistent with the pilots/lists when the faction
    toggle changes.
    """
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    cache_key = f"ship_squadrons|{ship_xws}|{ds}|{limit}|{faction or 'all'}"

    def compute():
        filters = {"ship": [ship_xws]}
        if faction and faction != "all":
            filters["factions"] = [faction]
        return aggregate_squadron_stats(filters, SortingCriteria.WINRATE, SortDirection.DESCENDING, ds)

    data = get_cached_or_compute(cache_key, compute)
    
    filtered_data = [d for d in data if d.get("games", 0) >= 5]
    if not filtered_data:
        filtered_data = data
        
    return {"squadrons": filtered_data[:limit]}
