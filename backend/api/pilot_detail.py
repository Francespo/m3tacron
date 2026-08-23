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
from ..analytics.lists import aggregate_list_stats_for_pilot, fetch_list_pilots
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
    size: int = Query(50, ge=1, le=200),
    formats: list[str] | None = Query(None),
    search_text: str = Query(""),
    upgrade_types: list[str] | None = Query(None),
):
    """Return upgrade stats filtered to this pilot's lists, restricted to upgrades compatible with this pilot's ship."""
    ds = DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA
    criteria = SortingCriteria.from_label(sort_metric)
    direction = SortDirection(sort_direction)

    # Pilot's legal slots (from manifest) — used to filter out upgrades that cannot be equipped on this ship
    pilot_slots: set[str] | None = None
    pilot_info = load_all_pilots(ds).get(pilot_xws)
    if pilot_info and pilot_info.get("slots"):
        pilot_slots = set(s.lower() for s in pilot_info["slots"])

    filters = {
        "allowed_formats": formats,
        "search_text": search_text,
        "upgrade_type": upgrade_types or [],
        "pilot_id": pilot_xws,
        "include_epic": False,
    }
    data = aggregate_card_stats(filters, criteria, direction, "upgrades", ds)

    # Filter to only upgrades whose slot is compatible with this pilot (real GAMES/LISTS/WR on this pilot, but not nonsense like Crew on a TIE Advanced)
    all_upgrades = load_all_upgrades(ds)
    if pilot_slots is not None:
        compatible: list[dict] = []
        for row in data:
            u = all_upgrades.get(row["xws"], {})
            sides = u.get("sides") or []
            required_slots = set()
            if sides and isinstance(sides, list):
                for side in sides:
                    for sl in (side.get("slots") or []):
                        required_slots.add(str(sl).strip().lower())
            # If upgrade has no slot info (should not happen), keep it; if it does, require overlap with pilot's slots
            if not required_slots or not required_slots.isdisjoint(pilot_slots):
                compatible.append(row)
        data = compatible

    # Enrich with human-friendly data so frontend doesn't depend solely on xwingData manifest being loaded
    enriched: list[dict] = []
    for row in data:
        u = all_upgrades.get(row["xws"], {})
        name = u.get("name", row["xws"])
        image = u.get("image", "")
        sides = u.get("sides") or []
        slot = ""
        if sides and isinstance(sides, list) and sides[0].get("slots"):
            slot = sides[0]["slots"][0]
        elif u.get("slot_category"):
            slot = u["slot_category"]
        else:
            slot = u.get("type", "")
        cost_obj = u.get("cost", {})
        cost_val = cost_obj.get("value") if isinstance(cost_obj, dict) else cost_obj
        enriched.append({
            **row,
            "name": name,
            "image": image,
            "type": slot,
            "type_xws": str(slot).lower() if slot else "",
            "slot_xws": str(slot).lower() if slot else "",
            "cost": cost_val,
        })
    data = enriched

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
    limit: int = Query(10, ge=1, le=200),
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
                    "games": 0,
                    "lists": 0,
                    "wins": 0,
                }
            games = max(0, swiss_wins) + max(0, swiss_losses) + max(0, swiss_draws) + max(0, cut_wins) + max(0, cut_losses) + max(0, cut_draws)
            has_game = games > 0
            config_stats[key]["count"] += 1
            config_stats[key]["games"] += games
            if has_game:
                config_stats[key]["lists"] += 1
            total_wins = swiss_wins + cut_wins
            if total_wins > 0:
                config_stats[key]["wins"] += total_wins

    # Sort by count desc, take top N
    sorted_configs = sorted(config_stats.values(), key=lambda x: x["count"], reverse=True)[:limit]

    # Enrich with upgrade images/costs (no name needed — readable on PNG)
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
        # WR as wins / total lists that had this config (matches old count-based WR: 49/74=66.2, not 49/38=128%)
        wr = round((cfg["wins"] / cfg["count"]) * 100, 1) if cfg["count"] > 0 else 0
        results.append({
            "upgrades": enriched_upgrades,
            "count": cfg["count"],
            # expose both for frontend: count == total standings, lists == only game-played lists, games == sum games
            "lists": cfg["count"],
            "lists_with_games": cfg["lists"],
            "games": cfg["games"],
            "wins": cfg["wins"],
            "win_rate": wr,
        })

    return {"configurations": results, "total": len(config_stats)}


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
