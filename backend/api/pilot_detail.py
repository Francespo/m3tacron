"""
Pilot Detail API endpoints.

Provides pilot info, compatible upgrade stats, temporal usage chart,
and top upgrade configurations for a given pilot.
"""
from fastapi import APIRouter, Query
from sqlmodel import Session
from sqlalchemy import text

from ..analytics.core import aggregate_card_stats
from ..analytics.charts import get_card_usage_history
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from ..utils.xwing_data.pilots import load_all_pilots
from ..utils.xwing_data.upgrades import load_all_upgrades
from ..database import engine

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

    Uses a SQL-side filter on the joined list table — we only fetch
    rows whose list_json contains the requested pilot, then aggregate
    upgrade combos and wins in Python (still N matches, but no full
    table scan).
    """
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    all_upgrades = load_all_upgrades(ds)

    config_stats: dict[str, dict] = {}

    with Session(engine) as session:
        params: dict = {"pilot_xws": pilot_xws}
        fmt_clause = ""
        if formats:
            fmt_clause = " AND t.format = ANY(:formats)"
            params["formats"] = list(formats)

        # Filter at the SQL level via the list table JOIN and the
        # list_json->'pilots' containment check. We do this in raw SQL
        # (matches the pattern in analytics/core.py) so the query planner
        # can use the playerstanding.list_id index.
        sql = text(
            f"""
            SELECT
                ps.swiss_wins, ps.swiss_losses, ps.swiss_draws,
                ps.cut_wins, ps.cut_losses, ps.cut_draws,
                p
            FROM playerstanding ps
            JOIN list l ON l.id = ps.list_id
            JOIN tournament t ON t.id = ps.tournament_id
            JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') p ON true
            WHERE p->>'id' = :pilot_xws{fmt_clause}
            """
        )
        rows = session.execute(sql, params).fetchall()

        for row in rows:
            swiss_wins = row[0] or 0
            swiss_losses = row[1] or 0
            swiss_draws = row[2] or 0
            cut_wins = row[3] or 0
            cut_losses = row[4] or 0
            cut_draws = row[5] or 0

            pilot_obj = row[6]
            if not pilot_obj or not isinstance(pilot_obj, dict):
                continue

            # Extract upgrade combo from the JSONB pilot element.
            raw_upgrades = pilot_obj.get("upgrades", {}) or {}
            upgrade_ids = []
            if isinstance(raw_upgrades, dict):
                for slot_list in raw_upgrades.values():
                    if isinstance(slot_list, list):
                        upgrade_ids.extend(str(x) for x in slot_list)
            elif isinstance(raw_upgrades, list):
                upgrade_ids.extend(str(x) for x in raw_upgrades)
            upgrade_ids.sort()

            key = "|".join(upgrade_ids)

            if key not in config_stats:
                config_stats[key] = {
                    "upgrade_ids": upgrade_ids,
                    "count": 0,
                    "wins": 0,
                }
            config_stats[key]["count"] += 1
            # Win detection: a player wins if they won at least one game in
            # this match (swiss + cut wins > 0). This is the closest we can
            # get to a per-match win indicator without a `winner` column.
            # The old code attempted to use `row.winner` and `swiss_standing`
            # but neither existed on PlayerStanding, so wins were always 0.
            total_wins = swiss_wins + cut_wins
            if total_wins > 0:
                config_stats[key]["wins"] += total_wins

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
