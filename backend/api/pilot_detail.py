"""
Pilot Detail API endpoints.

Provides pilot info, compatible upgrade stats, temporal usage chart,
and top upgrade configurations for a given pilot.
"""
from collections import defaultdict
from fastapi import APIRouter, Query
from sqlmodel import Session
from sqlalchemy import text

from ..analytics.core import aggregate_card_stats
from ..analytics.charts import get_card_usage_history
from ..analytics.lists import aggregate_list_stats_for_pilot, fetch_list_pilots
from ..analytics.precompute import get_snapshot
from ..cache import get_cached_or_compute
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
    """Return static pilot info (name, image, ship, faction, cost, loadout) + header stats (SQ/LISTS/ENTRIES/GAMES/WR)."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    all_pilots = load_all_pilots(ds)
    info = all_pilots.get(pilot_xws, {"name": pilot_xws, "xws": pilot_xws, "image": "", "slots": []})
    # Header stats from precomputed snapshot (paid once per data_version at scrape time)
    header = (get_snapshot(ds).get("header") or {}).get(pilot_xws, {}) or {}
    return {**info, "_headerStats": header}


@router.get("/{pilot_xws}/upgrades")
def get_pilot_upgrades(
    pilot_xws: str,
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Lists"),
    sort_direction: str = Query("desc"),
    page: int = Query(0, ge=0),
    size: int = Query(50, ge=1, le=200),
    formats: list[str] | None = Query(None),
    search_text: str = Query(""),
    upgrade_types: list[str] | None = Query(None),
):
    """Return upgrade stats filtered to this pilot's lists, restricted to upgrades compatible with this pilot's ship (precomputed snapshot)."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA

    # Pilot's legal slots (from manifest) — used to filter out upgrades that cannot be equipped on this ship
    pilot_slots: set[str] | None = None
    pilot_info = load_all_pilots(ds).get(pilot_xws)
    if pilot_info and pilot_info.get("slots"):
        pilot_slots = set(s.lower() for s in pilot_info["slots"])

    all_upgrades = load_all_upgrades(ds)
    snap = get_snapshot(ds)

    # Aggregate across matching formats from snapshot (no SQL per card)
    merged: dict[str, dict] = {}
    for f in snap["pilot_upgrades"]:
        if formats and f not in formats:
            continue
        for upg_xws, st in (snap["pilot_upgrades"][f].get(pilot_xws) or {}).items():
            m = merged.setdefault(upg_xws, {"lists": 0, "games": 0, "wins": 0})
            m["lists"] += st["lists"]
            m["games"] += st["games"]
            m["wins"] += st["wins"]

    # Add compatible-but-unused upgrades (zero counts) so "compatible upgrades" is complete,
    # matching the previous aggregate_card_stats semantics (all catalog upgrades whose slot fits).
    if pilot_slots is not None:
        for upg_xws, u in all_upgrades.items():
            if upg_xws in merged:
                continue
            sides = u.get("sides") or []
            required_slots = set()
            if sides and isinstance(sides, list):
                for side in sides:
                    for sl in (side.get("slots") or []):
                        required_slots.add(str(sl).strip().lower())
            if required_slots and not required_slots.isdisjoint(pilot_slots):
                merged[upg_xws] = {"lists": 0, "games": 0, "wins": 0}

    rows: list[dict] = []
    for upg_xws, st in merged.items():
        u = all_upgrades.get(upg_xws, {})
        sides = u.get("sides") or []
        required_slots = set()
        if sides and isinstance(sides, list):
            for side in sides:
                for sl in (side.get("slots") or []):
                    required_slots.add(str(sl).strip().lower())
        # slot compatibility (keep if unknown slot or overlaps pilot slots)
        if pilot_slots is not None and required_slots and required_slots.isdisjoint(pilot_slots):
            continue
        slot = ""
        if sides and isinstance(sides, list) and sides[0].get("slots"):
            slot = sides[0]["slots"][0]
        elif u.get("slot_category"):
            slot = u["slot_category"]
        else:
            slot = u.get("type", "")
        cost_obj = u.get("cost", {})
        cost_val = cost_obj.get("value") if isinstance(cost_obj, dict) else cost_obj
        rows.append({
            "xws": upg_xws,
            "name": u.get("name", upg_xws),
            "image": u.get("image", ""),
            "type": slot,
            "type_xws": str(slot).lower() if slot else "",
            "slot_xws": str(slot).lower() if slot else "",
            "cost": cost_val,
            "games_count": st["games"],
            "list_count": st["lists"],
            "different_lists_count": st["lists"],
            "wins": st["wins"],
        })

    # Sort by list_count desc (neutral), then by games
    rows.sort(key=lambda r: (r["list_count"], r["games_count"]), reverse=True)
    total = len(rows)
    start = page * size
    items = rows[start:start + size]
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/{pilot_xws}/chart")
def get_pilot_chart(
    pilot_xws: str,
    data_source: str = Query("xwa"),
    formats: list[str] | None = Query(None),
    comparison: list[str] | None = Query(None),
):
    """Return monthly usage history for the pilot and optional comparisons (precomputed snapshot)."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    if not comparison:
        key = f"pilot_chart_snap|{pilot_xws}|{data_source}|{','.join(sorted(formats or []))}"
        def _compute():
            snap = get_snapshot(ds)
            months = defaultdict(int)
            for f in snap["pilot_chart"]:
                if formats and f not in formats:
                    continue
                for m, v in (snap["pilot_chart"][f].get(pilot_xws) or {}).items():
                    months[m] += v
            data = [{"date": m, pilot_xws: months[m]} for m in sorted(months)]
            return {"data": data, "series": [pilot_xws]}
        return get_cached_or_compute(key, _compute)
    # comparisons — rare path, live
    key = (
        f"pilot_chart|{pilot_xws}|{data_source}"
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
            pilot_xws,
            comparison or [],
            is_upgrade=False,
        )
        return {"data": chart_data, "series": [pilot_xws] + (comparison or [])}
    return get_cached_or_compute(key, _compute)


@router.get("/{pilot_xws}/configurations")
def get_pilot_configurations(
    pilot_xws: str,
    data_source: str = Query("xwa"),
    formats: list[str] | None = Query(None),
    limit: int = Query(10, ge=1, le=200),
):
    """
    Return top upgrade configurations for this pilot (precomputed snapshot).
    """
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    all_upgrades = load_all_upgrades(ds)
    snap = get_snapshot(ds)

    # Merge configs across formats
    by_combo: dict[str, dict] = {}
    for f in snap["pilot_configs"]:
        if formats and f not in formats:
            continue
        for combo, cfg in (snap["pilot_configs"][f].get(pilot_xws) or {}).items():
            if combo not in by_combo:
                by_combo[combo] = {
                    "upgrade_ids": list(cfg.get("upgrade_ids") or []),
                    "count": 0,
                    "lists": 0,
                    "games": 0,
                    "wins": 0,
                }
            by_combo[combo]["count"] += cfg["count"]
            by_combo[combo]["lists"] += cfg["lists"]
            by_combo[combo]["games"] += cfg["games"]
            by_combo[combo]["wins"] += cfg["wins"]

    sorted_configs = sorted(by_combo.values(), key=lambda x: x["count"], reverse=True)[:limit]

    # Enrich with upgrade images/costs
    results = []
    for cfg in sorted_configs:
        enriched_upgrades = []
        for uid in cfg["upgrade_ids"]:
            info = all_upgrades.get(uid, {})
            cost_obj = info.get("cost", {})
            cost_val = cost_obj.get("value") if isinstance(cost_obj, dict) else cost_obj
            enriched_upgrades.append({
                "xws": uid,
                "name": info.get("name", uid),
                "type": info.get("type", ""),
                "image": info.get("image", ""),
                "cost": cost_val,
            })
        wr = round((cfg["wins"] / cfg["count"]) * 100, 1) if cfg["count"] > 0 else 0
        results.append({
            "upgrades": enriched_upgrades,
            "count": cfg["count"],
            "lists": cfg["count"],
            "lists_with_games": cfg["lists"],
            "games": cfg["games"],
            "wins": cfg["wins"],
            "win_rate": wr,
        })

    return {"configurations": results, "total": len(by_combo)}


@router.get("/{pilot_xws}/lists")
def get_pilot_lists(
    pilot_xws: str,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Games"),
    sort_direction: str = Query("desc"),
    epic: bool = Query(False),
    min_games: int = Query(0, ge=0),
    points_min: int = Query(0, ge=0),
    points_max: int = Query(200, ge=0),
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    platforms: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
    search_text: str = Query(""),
):
    """Top lists featuring this pilot — reuses the existing ListRowCard shape.

    Aggregates over playerstandings whose list_json contains the pilot id
    (same primitive the chart/configurations endpoints use), then shapes
    rows via the shared lists aggregator + fetch_list_pilots. Cached by
    (pilot_xws, filters, sort).
    """
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    filters = {
        "platforms": platforms,
        "continent": continent,
        "country": country,
        "city": city,
        "date_start": date_start,
        "date_end": date_end,
        "player_count_min": player_count_min,
        "player_count_max": player_count_max,
        "ships": ships,
        "factions": factions,
        "epic": epic,
    }
    if formats:
        filters["allowed_formats"] = formats

    def _sort(rows: list[dict]) -> list[dict]:
        reverse = sort_direction == "desc"
        if sort_metric == "Win Rate":
            return sorted(rows, key=lambda r: (r["wins"] / r["games"] if r["games"] else 0.0), reverse=reverse)
        if sort_metric == "Points Cost":
            return sorted(rows, key=lambda r: r.get("points", 0), reverse=reverse)
        return sorted(rows, key=lambda r: r.get("games", 0), reverse=reverse)

    def _compute() -> list[dict]:
        return aggregate_list_stats_for_pilot(filters, pilot_xws, data_source=ds_enum, search_text=search_text)

    sanitized_search = (search_text or "").lower()
    cache_key = (
        f"pilot_lists|{pilot_xws}|{data_source}"
        f"|f={','.join(sorted(formats or []))}"
        f"|fa={','.join(sorted(factions or []))}"
        f"|s={','.join(sorted(ships or []))}"
        f"|p={','.join(sorted(platforms or []))}"
        f"|co={','.join(sorted(continent or []))}|cn={','.join(sorted(country or []))}|ci={','.join(sorted(city or []))}"
        f"|ds={date_start}|de={date_end}|pcmin={player_count_min}|pcmax={player_count_max}"
        f"|mg={min_games}|pmin={points_min}|pmax={points_max}|epic={epic}"
        f"|q={sanitized_search}|sm={sort_metric}|sd={sort_direction}"
    )

    raw = get_cached_or_compute(cache_key, _compute)

    # Post-filter on min_games / points (same as /api/lists), then sort
    filtered = [
        r for r in raw
        if r.get("games", 0) >= min_games and points_min <= (r.get("points") or 0) <= points_max
    ]
    sorted_rows = _sort(filtered)
    total = len(sorted_rows)
    page_items = sorted_rows[page * size : (page + 1) * size]

    signatures = [r["signature"] for r in page_items if r.get("signature")]
    pilots_map = fetch_list_pilots(signatures) if signatures else {}
    items = [{**r, "pilots": pilots_map.get(r["signature"], [])} for r in page_items if r.get("signature")]

    return {"items": items, "total": total, "page": page, "size": size}
