"""
Pilot Detail API endpoints.

Provides pilot info, compatible upgrade stats, temporal usage chart,
and top upgrade configurations for a given pilot.
"""
from fastapi import APIRouter, Query
from collections import defaultdict

from ..analytics.core import aggregate_card_stats
from ..analytics.charts import get_card_usage_history
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from ..utils.xwing_data.pilots import load_all_pilots
from ..utils.xwing_data.upgrades import load_all_upgrades
from ..database import engine
from ..models import PlayerResult, Tournament
from sqlmodel import Session, select

router = APIRouter(prefix="/api/pilot", tags=["Pilot Detail"])


@router.get("/{pilot_xws}")
def get_pilot_info(
    pilot_xws: str,
    data_source: str = Query("xwa"),
):
    """Return static pilot info (name, image, ship, faction, cost, loadout)."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    all_pilots = load_all_pilots(ds)
    info = all_pilots.get(pilot_xws, {"name": pilot_xws, "xws": pilot_xws, "image": ""})
    return info


@router.get("/{pilot_xws}/upgrades")
def get_pilot_upgrades(
    pilot_xws: str,
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Popularity"),
    sort_direction: str = Query("desc"),
    page: int = Query(0, ge=0),
    size: int = Query(50, ge=1, le=100),
    formats: list[str] | None = Query(None),
    search_text: str = Query(""),
    upgrade_types: list[str] | None = Query(None),
):
    """Return upgrade stats filtered to this pilot's lists."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    criteria = SortingCriteria.from_label(sort_metric)
    direction = SortDirection(sort_direction)

    filters = {
        "allowed_formats": formats,
        "search_text": search_text,
        "upgrade_type": upgrade_types or [],
        "pilot_id": pilot_xws,
        "include_epic": False,
    }
    data = aggregate_card_stats(filters, criteria, direction, "upgrades", ds)
    total = len(data)
    start = page * size
    items = data[start:start + size]
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/{pilot_xws}/chart")
def get_pilot_chart(
    pilot_xws: str,
    data_source: str = Query("xwa"),
    formats: list[str] | None = Query(None),
    comparison: list[str] | None = Query(None),
):
    """Return monthly usage history for the pilot and optional comparisons."""
    filters = {
        "allowed_formats": formats,
        "include_epic": False,
    }
    chart_data = get_card_usage_history(
        filters,
        pilot_xws,
        comparison or [],
        is_upgrade=False,
    )
    return {"data": chart_data, "series": [pilot_xws] + (comparison or [])}


@router.get("/{pilot_xws}/configurations")
def get_pilot_configurations(
    pilot_xws: str,
    data_source: str = Query("xwa"),
    formats: list[str] | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Return top upgrade configurations for this pilot.

    Aggregates the exact upgrade loadouts used with this pilot,
    counts frequency and calculates win rate per unique combo.
    """
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    all_upgrades = load_all_upgrades(ds)

    # Build format filter set
    allowed = set(formats) if formats else None

    # Scan database for lists containing this pilot
    config_stats: dict[str, dict] = {}  # frozen_key -> {count, wins, upgrades_list}

    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        rows = session.exec(query).all()

        for result, tournament in rows:
            # Format check
            t_fmt = tournament.format
            fmt_val = t_fmt.value if hasattr(t_fmt, "value") else (t_fmt or "other")
            if allowed and fmt_val not in allowed:
                continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue

            # Find this pilot in the list
            for p in xws.get("pilots", []):
                pid = p.get("id") or p.get("name")
                if pid != pilot_xws:
                    continue

                # Extract upgrade combo
                raw_upgrades = p.get("upgrades", {}) or {}
                upgrade_ids = []
                for slot_list in raw_upgrades.values():
                    upgrade_ids.extend(slot_list)
                upgrade_ids.sort()

                key = "|".join(upgrade_ids)

                if key not in config_stats:
                    config_stats[key] = {
                        "upgrade_ids": upgrade_ids,
                        "count": 0,
                        "wins": 0,
                    }
                config_stats[key]["count"] += 1
                # Win detection
                won = False
                if hasattr(result, "winner") and result.winner:
                    won = True
                elif hasattr(result, "swiss_standing") and result.swiss_standing == 1:
                    won = True
                if won:
                    config_stats[key]["wins"] += 1

    # Sort by count desc, take top N
    sorted_configs = sorted(config_stats.values(), key=lambda x: x["count"], reverse=True)[:limit]

    # Enrich with upgrade names/images
    results = []
    for cfg in sorted_configs:
        enriched_upgrades = []
        for uid in cfg["upgrade_ids"]:
            info = all_upgrades.get(uid, {})
            enriched_upgrades.append({
                "xws": uid,
                "name": info.get("name", uid),
                "type": info.get("type", ""),
                "image": info.get("image", ""),
            })
        wr = round((cfg["wins"] / cfg["count"]) * 100, 1) if cfg["count"] > 0 else 0
        results.append({
            "upgrades": enriched_upgrades,
            "count": cfg["count"],
            "wins": cfg["wins"],
            "win_rate": wr,
        })

    return {"configurations": results, "total": len(config_stats)}
