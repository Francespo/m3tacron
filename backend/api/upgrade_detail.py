"""
Upgrade Detail API endpoints.

Provides upgrade info, compatible pilot stats, ship stats, and temporal usage chart.
"""
from collections import defaultdict
from fastapi import APIRouter, Query
from sqlmodel import Session
from sqlalchemy import text

from ..analytics.charts import get_card_usage_history
from ..analytics.precompute import get_snapshot
from ..cache import get_cached_or_compute
from ..data_structures.data_source import DataSource
from ..utils.xwing_data.pilots import load_all_pilots
from ..utils.xwing_data.upgrades import load_all_upgrades, get_upgrade_info
from ..database import engine

router = APIRouter(prefix="/api/upgrade", tags=["Upgrade Detail"])


@router.get("/{upgrade_xws}")
def get_upgrade_info_endpoint(
    upgrade_xws: str,
    data_source: str = Query("xwa"),
):
    """Return static upgrade info (name, image, cost, limited)."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    info = get_upgrade_info(upgrade_xws, ds)
    if not info:
        info = {"name": upgrade_xws, "xws": upgrade_xws, "image": "", "sides": []}
    return info


@router.get("/{upgrade_xws}/pilots")
def get_upgrade_pilots(
    upgrade_xws: str,
    data_source: str = Query("xwa"),
    formats: list[str] | None = Query(None),
):
    """Return stats for pilots who equip this upgrade (reads precomputed snapshot)."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    key = f"upg_pilots_snap|{upgrade_xws}|{data_source}|{','.join(sorted(formats or []))}"
    def _compute():
        return _pilots_from_snapshot(upgrade_xws, ds, formats)
    return get_cached_or_compute(key, _compute)


def _pilots_from_snapshot(upgrade_xws, ds, formats):
    snap = get_snapshot(ds)
    fmt_keys = [f for f in snap["upgrade_pilots"] if not formats or f in formats]
    by_pilot = {}
    for f in fmt_keys:
        for p_xws, st in (snap["upgrade_pilots"][f].get(upgrade_xws) or {}).items():
            if p_xws not in by_pilot:
                by_pilot[p_xws] = {"lists": 0, "games": 0, "wins": 0}
            by_pilot[p_xws]["lists"] += st["lists"]
            by_pilot[p_xws]["games"] += st["games"]
            by_pilot[p_xws]["wins"] += st["wins"]
    all_pilots = load_all_pilots(ds)
    results = []
    for p_xws, st in by_pilot.items():
        p_info = all_pilots.get(p_xws, {})
        wr = round((st["wins"] / st["games"]) * 100, 1) if st["games"] > 0 else 0
        results.append({
            "xws": p_xws,
            "name": p_info.get("name", p_xws),
            "ship": p_info.get("ship", "Unknown Ship"),
            "ship_xws": p_info.get("ship_xws", ""),
            "faction_xws": p_info.get("faction", "").lower().replace(" ", "").replace("-", ""),
            "image": p_info.get("image", ""),
            "cost": p_info.get("cost", 0),
            "loadout": p_info.get("loadout", 0),
            "list_count": st["lists"],
            "games": st["games"],
            "wins": st["wins"],
            "win_rate": wr,
        })
    results.sort(key=lambda x: x["list_count"], reverse=True)
    return results
    
    pilot_stats = {}
    with Session(engine) as session:
        params: dict = {"upgrade_xws": upgrade_xws}
        fmt_clause = ""
        if formats:
            fmt_clause = " AND t.format = ANY(:formats)"
            params["formats"] = list(formats)
            
        sql = text(f"""
            SELECT
                p->>'id' AS pilot_xws,
                COUNT(DISTINCT CASE WHEN (COALESCE(ps.swiss_wins,0)+COALESCE(ps.swiss_losses,0)+COALESCE(ps.swiss_draws,0)+COALESCE(ps.cut_wins,0)+COALESCE(ps.cut_losses,0)+COALESCE(ps.cut_draws,0)) > 0 THEN ps.id END) AS list_count,
                SUM(GREATEST(0, COALESCE(ps.swiss_wins, 0)) + GREATEST(0, COALESCE(ps.cut_wins, 0))) AS wins,
                SUM(
                    GREATEST(0, COALESCE(ps.swiss_wins, 0)) + GREATEST(0, COALESCE(ps.swiss_losses, 0)) + GREATEST(0, COALESCE(ps.swiss_draws, 0))
                    + GREATEST(0, COALESCE(ps.cut_wins, 0)) + GREATEST(0, COALESCE(ps.cut_losses, 0)) + GREATEST(0, COALESCE(ps.cut_draws, 0))
                ) AS games
            FROM playerstanding ps
            JOIN tournament t ON t.id = ps.tournament_id
            JOIN list l ON l.id = ps.list_id
            JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') p ON true
            WHERE (
                (jsonb_typeof(p->'upgrades') = 'object' AND 
                 EXISTS (
                     SELECT 1 FROM jsonb_each(p->'upgrades') e, 
                     jsonb_array_elements_text(e.value) v 
                     WHERE jsonb_typeof(e.value) = 'array' AND v = :upgrade_xws
                 ))
                OR
                (jsonb_typeof(p->'upgrades') = 'array' AND 
                 EXISTS (
                     SELECT 1 FROM jsonb_array_elements_text(p->'upgrades') u 
                     WHERE u = :upgrade_xws
                 ))
            ) AND (NOT t.is_team_event OR ps.is_team_member) {fmt_clause}
            GROUP BY p->>'id'
        """)
        
        rows = session.execute(sql, params).fetchall()
        
        for row in rows:
            p_xws = row[0]
            if not p_xws:
                continue
            list_count = int(row[1] or 0)
            wins = int(row[2] or 0)
            games = int(row[3] or 0)
            
            pilot_stats[p_xws] = {
                "pilot_xws": p_xws,
                "list_count": list_count,
                "wins": wins,
                "games": games,
            }
            
    # Enrich with static metadata and compute win rate
    results = []
    for p_xws, stats in pilot_stats.items():
        p_info = all_pilots.get(p_xws, {})
        wr = round((stats["wins"] / stats["games"]) * 100, 1) if stats["games"] > 0 else 0
        results.append({
            "xws": p_xws,
            "name": p_info.get("name", p_xws),
            "ship": p_info.get("ship", "Unknown Ship"),
            "ship_xws": p_info.get("ship_xws", ""),
            "faction_xws": p_info.get("faction", "").lower().replace(" ", "").replace("-", ""),
            "image": p_info.get("image", ""),
            "cost": p_info.get("cost", 0),
            "loadout": p_info.get("loadout", 0),
            "list_count": stats["list_count"],
            "games": stats["games"],
            "wins": stats["wins"],
            "win_rate": wr,
        })
        
    results.sort(key=lambda x: x["list_count"], reverse=True)
    return results


@router.get("/{upgrade_xws}/ships")
def get_upgrade_ships(
    upgrade_xws: str,
    data_source: str = Query("xwa"),
    formats: list[str] | None = Query(None),
):
    """Return stats for ships whose pilots equip this upgrade (reads precomputed snapshot)."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    key = f"upg_ships_snap|{upgrade_xws}|{data_source}|{','.join(sorted(formats or []))}"
    def _compute():
        return _ships_from_snapshot(upgrade_xws, ds, formats)
    return get_cached_or_compute(key, _compute)


def _ships_from_snapshot(upgrade_xws, ds, formats):
    pilots_data = _pilots_from_snapshot(upgrade_xws, ds, formats)
    return _build_upgrade_ships(pilots_data)


def _build_upgrade_ships(pilots_data):
    
    ship_stats = {}
    for p in pilots_data:
        s_xws = p["ship_xws"]
        if not s_xws:
            continue
        if s_xws not in ship_stats:
            ship_stats[s_xws] = {
                "ship_xws": s_xws,
                "name": p["ship"],
                "faction_xws": p["faction_xws"],
                "list_count": 0,
                "games": 0,
                "wins": 0,
            }
        ship_stats[s_xws]["list_count"] += p["list_count"]
        ship_stats[s_xws]["games"] += p["games"]
        ship_stats[s_xws]["wins"] += p["wins"]
        
    results = []
    for s_xws, stats in ship_stats.items():
        wr = round((stats["wins"] / stats["games"]) * 100, 1) if stats["games"] > 0 else 0
        results.append({
            "xws": s_xws,
            "name": stats["name"],
            "faction_xws": stats["faction_xws"],
            "list_count": stats["list_count"],
            "games": stats["games"],
            "wins": stats["wins"],
            "win_rate": wr,
        })
        
    results.sort(key=lambda x: x["list_count"], reverse=True)
    return results


@router.get("/{upgrade_xws}/chart")
def get_upgrade_chart(
    upgrade_xws: str,
    data_source: str = Query("xwa"),
    formats: list[str] | None = Query(None),
    comparison: list[str] | None = Query(None),
):
    """Return monthly usage history for the upgrade (reads precomputed snapshot; comparisons fall back to live)."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    if not comparison:
        key = f"upg_chart_snap|{upgrade_xws}|{data_source}|{','.join(sorted(formats or []))}"
        def _compute():
            snap = get_snapshot(ds)
            months = defaultdict(int)
            for f in snap["upgrade_chart"]:
                if formats and f not in formats:
                    continue
                for m, v in (snap["upgrade_chart"][f].get(upgrade_xws) or {}).items():
                    months[m] += v
            data = [{"date": m, upgrade_xws: months[m]} for m in sorted(months)]
            return {"data": data, "series": [upgrade_xws]}
        return get_cached_or_compute(key, _compute)
    # comparisons — fall back to live computation (rare path)
    key = (
        f"upg_chart|{upgrade_xws}|{data_source}"
        f"|{','.join(sorted(formats or []))}"
        f"|{','.join(sorted(comparison or []))}"
    )
    def _compute():
        filters = {
            "allowed_formats": formats,
            "include_epic": False,
        }
        chart_data = get_card_usage_history(
            filters,
            upgrade_xws,
            comparison or [],
            is_upgrade=True,
        )
        return {"data": chart_data, "series": [upgrade_xws] + (comparison or [])}
    return get_cached_or_compute(key, _compute)
