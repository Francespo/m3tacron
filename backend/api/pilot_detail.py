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


def _normalize_slot(name: str) -> str:
    """Normalize a slot name for case-insensitive, space/hyphen-agnostic comparison."""
    return name.lower().replace(" ", "").replace("-", "")


def _get_upgrade_slot_type(upgrade_info: dict) -> str:
    """Get the primary slot type for an upgrade from its sides data."""
    sides = upgrade_info.get("sides", [])
    if sides and isinstance(sides, list) and len(sides) > 0:
        side_type = sides[0].get("type", "")
        if side_type:
            return side_type
    return upgrade_info.get("slot_category", "")


def _get_upgrade_slots(upgrade_info: dict) -> list[str]:
    """Get the full slot list for an upgrade (may be 1 or 2 slots, e.g. Synced Laser Cannons)."""
    sides = upgrade_info.get("sides", [])
    if sides and isinstance(sides, list) and len(sides) > 0:
        slots = sides[0].get("slots", [])
        if slots:
            return list(slots)
    primary = _get_upgrade_slot_type(upgrade_info)
    return [primary] if primary else []


def _get_upgrade_cost(upgrade_info: dict) -> int:
    """Extract the numeric point cost from an upgrade's cost field."""
    cost = upgrade_info.get("cost", {})
    if isinstance(cost, (int, float)):
        return int(cost)
    if isinstance(cost, dict):
        val = cost.get("value")
        if val is not None:
            return int(val)
        # Initiative-keyed costs: pick the cheapest for conservative filtering
        numeric = [int(v) for k, v in cost.items() if str(k).isdigit()]
        if numeric:
            return min(numeric)
    return 0


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
    sort_metric: str = Query("Lists"),
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

    # Filter upgrades to only those compatible with the pilot's actual slots.
    # The SQL query finds co-occurrence (any upgrade in any list with this pilot),
    # but we need to validate against the pilot's legal upgrade slots.
    all_pilots_for_slots = load_all_pilots(ds)
    pilot_info = all_pilots_for_slots.get(pilot_xws, {})
    pilot_slots = {_normalize_slot(s) for s in pilot_info.get("slots", [])}
    if pilot_slots:
        all_upgrades_for_filter = load_all_upgrades(ds)
        filtered = []
        for item in data:
            u_info = all_upgrades_for_filter.get(item["xws"], {})
            u_type = _get_upgrade_slot_type(u_info)
            if u_type and _normalize_slot(u_type) in pilot_slots:
                item["type"] = u_type
                item["type_xws"] = _normalize_slot(u_type)
                item["name"] = u_info.get("name", item["xws"])
                item["image"] = u_info.get("image", "")
                filtered.append(item)
        data = filtered

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
    currently_playable: bool = Query(False),
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
                    "games": 0,
                }
            config_stats[key]["count"] += 1
            # Track total games played (wins + losses + draws) so we can
            # compute a proper win-rate that never exceeds 100%.
            total_games = swiss_wins + swiss_losses + swiss_draws + cut_wins + cut_losses + cut_draws
            config_stats[key]["games"] += total_games
            total_wins = swiss_wins + cut_wins
            if total_wins > 0:
                config_stats[key]["wins"] += total_wins

    # Sort by count desc, take top N
    sorted_configs = sorted(config_stats.values(), key=lambda x: x["count"], reverse=True)

    # If currently_playable is requested, load pilot slot/loadout info and filter
    if currently_playable:
        all_pilots_info = load_all_pilots(ds)
        pilot_info = all_pilots_info.get(pilot_xws, {})
        pilot_slots = {_normalize_slot(s) for s in pilot_info.get("slots", [])}
        pilot_loadout = int(pilot_info.get("loadout", 0) or 0)
        is_xwa = ds == DataSource.XWA

        playable_configs = []
        for cfg in sorted_configs:
            # Check slot compatibility: every upgrade's slot type must be in pilot's slots
            if pilot_slots:
                slot_ok = True
                total_cost = 0
                for uid in cfg["upgrade_ids"]:
                    u_info = all_upgrades.get(uid, {})
                    u_type = _get_upgrade_slot_type(u_info)
                    if not u_type or _normalize_slot(u_type) not in pilot_slots:
                        slot_ok = False
                        break
                    if is_xwa:
                        total_cost += _get_upgrade_cost(u_info)
                if not slot_ok:
                    continue
                # For XWA, check loadout budget
                if is_xwa and pilot_loadout > 0 and total_cost > pilot_loadout:
                    continue
            playable_configs.append(cfg)
        sorted_configs = playable_configs

    sorted_configs = sorted_configs[:limit]

    # Enrich with upgrade names/images and slot types
    results = []
    for cfg in sorted_configs:
        enriched_upgrades = []
        for uid in cfg["upgrade_ids"]:
            info = all_upgrades.get(uid, {})
            slot_type = _get_upgrade_slot_type(info)
            enriched_upgrades.append({
                "xws": uid,
                "name": info.get("name", uid),
                "type": slot_type,
                "type_xws": _normalize_slot(slot_type) if slot_type else "",
                "slots": _get_upgrade_slots(info),
                "image": info.get("image", ""),
                "cost": _get_upgrade_cost(info),
            })
        wr = round((cfg["wins"] / cfg["games"]) * 100, 1) if cfg["games"] > 0 else 0
        results.append({
            "upgrades": enriched_upgrades,
            "count": cfg["count"],
            "wins": cfg["wins"],
            "games": cfg["games"],
            "win_rate": wr,
        })

    return {"configurations": results, "total": len(config_stats)}
