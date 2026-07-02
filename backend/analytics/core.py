"""
Card Analytics - Aggregation Logic for Pilots and Upgrades.

Phase 1 (catalog filter) operates on the in-memory pilot/upgrade catalog
(~700 entries) and remains in Python. Phase 2 (aggregation over 96K+
list_json rows) is now a single SQL GROUP BY query for performance.
"""
from sqlmodel import Session, select
from sqlalchemy import text
import json
from ..database import engine
from ..models import PlayerStanding, Tournament
from ..utils.xwing_data.pilots import load_all_pilots
from ..utils.xwing_data.upgrades import load_all_upgrades
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from .filters import filter_query, get_active_formats, apply_tournament_filters
from ..data_structures.sorting_order import SortingCriteria, SortDirection


def aggregate_card_stats(
    filters: dict,
    sort_criteria: SortingCriteria = SortingCriteria.POPULARITY,
    sort_direction: SortDirection = SortDirection.DESCENDING,
    mode: str = "pilots",  # pilots, upgrades
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for pilots or upgrades.
    Returns list of dicts matching PilotStats or UpgradeStats schema.

    Catalog filtering (cost, faction, format legality, hull/shields/agility,
    text search, ship, initiative, upgrade type) is done in Python over the
    in-memory pilot/upgrade catalog. Per-list aggregation (counting games,
    wins, distinct lists) is done with a single SQL GROUP BY query.
    """
    # Pre-load Data
    all_pilots = load_all_pilots(data_source)
    all_upgrades = load_all_upgrades(data_source)

    allowed_formats = get_active_formats(filters.get("allowed_formats", None))
    faction_filter = filters.get("faction")
    type_filter = filters.get("upgrade_type")
    text_filter = filters.get("search_text", "").lower()
    ship_filter = filters.get("ship")
    initiative_filter = filters.get("initiative")

    filter_pilot_id = filters.get("pilot_id")
    if filter_pilot_id:
        filter_pilot_id = filter_pilot_id.strip('"').strip("'")

    filter_upgrade_id = filters.get("upgrade_id")
    if filter_upgrade_id:
        filter_upgrade_id = filter_upgrade_id.strip('"').strip("'")

    # Filter conversions (kept from original)
    allowed_initiatives = set()
    if initiative_filter and initiative_filter != "all":
        if isinstance(initiative_filter, list):
            for i_str in initiative_filter:
                try:
                    allowed_initiatives.add(int(i_str))
                except ValueError:
                    pass
        else:
            try:
                allowed_initiatives.add(int(initiative_filter))
            except ValueError:
                pass

    allowed_ships = set()
    if ship_filter and ship_filter != "all":
        if isinstance(ship_filter, list):
            allowed_ships = set(ship_filter)
        # legacy string search handled below (catalog filter)

    allowed_factions = set()
    if faction_filter and faction_filter != "all":
        if isinstance(faction_filter, list):
            allowed_factions = set(faction_filter)
        else:
            allowed_factions = {faction_filter}

    allowed_types = set()
    if type_filter and type_filter != "all":
        if isinstance(type_filter, list):
            allowed_types = set(t.lower() for t in type_filter)
        else:
            allowed_types = {type_filter.lower()}

    def _int_or(val, fallback):
        return val if val is not None else fallback

    points_min = _int_or(filters.get("points_min"), 0)
    points_max = _int_or(filters.get("points_max"), 200)
    loadout_min = _int_or(filters.get("loadout_min"), 0)
    loadout_max = _int_or(filters.get("loadout_max"), 99)
    hull_min = _int_or(filters.get("hull_min"), 0)
    hull_max = _int_or(filters.get("hull_max"), 20)
    shields_min = _int_or(filters.get("shields_min"), 0)
    shields_max = _int_or(filters.get("shields_max"), 20)
    agility_min = _int_or(filters.get("agility_min"), 0)
    agility_max = _int_or(filters.get("agility_max"), 10)
    attack_min = _int_or(filters.get("attack_min"), 0)
    attack_max = _int_or(filters.get("attack_max"), 10)
    init_min = _int_or(filters.get("init_min"), 0)
    init_max = _int_or(filters.get("init_max"), 8)

    is_unique = filters.get("is_unique", False)
    is_limited = filters.get("is_limited", False)
    is_not_limited = filters.get("is_not_limited", False)
    base_sizes = filters.get("base_sizes", {})

    # --- PHASE 1: Filter the in-memory catalog -------------------------------
    # Builds the `stats` dict with zeroed counts for eligible cards.
    # This block is preserved exactly as in the original implementation —
    # it operates on ~700 in-memory entries and is sub-millisecond.
    stats: dict = {}

    if mode == "pilots":
        for pid, p_info in all_pilots.items():
            # Filter Logic (copied and simplified)
            p_cost = int(p_info.get("cost", 0) or 0)
            p_loadout = int(p_info.get("loadout", 0) or 0)

            if p_cost < points_min or p_cost > points_max:
                continue
            if data_source == DataSource.XWA and (p_loadout < loadout_min or p_loadout > loadout_max):
                continue

            is_legal = p_info.get("valid_in_standard", False)
            is_wild = p_info.get("wildspace", False)
            is_epic = p_info.get("epic", False)
            show_card = False

            if allowed_formats:
                if ("xwa" in allowed_formats or "amg" in allowed_formats) and is_legal:
                    show_card = True
                if "wildspace" in allowed_formats and is_wild:
                    show_card = True
                if ("xwa_epic" in allowed_formats or "legacy_epic" in allowed_formats) and is_epic:
                    show_card = True
                if data_source == DataSource.LEGACY:
                    legacy_keys = {"legacy_x2po", "legacy_xlc", "ffg"}
                    if not legacy_keys.isdisjoint(allowed_formats):
                        show_card = True
            else:
                if data_source == DataSource.XWA and is_legal:
                    show_card = True
                elif data_source == DataSource.LEGACY:
                    show_card = True

            if not show_card:
                continue

            # Stat ranges
            p_hull = int(p_info.get("hull") or 0)
            p_shields = int(p_info.get("shields") or 0)
            p_agility = int(p_info.get("agility") or 0)
            p_attack = int(p_info.get("attack") or 0)
            p_init = int(p_info.get("initiative") or 0)

            if p_hull < hull_min or p_hull > hull_max:
                continue
            if p_shields < shields_min or p_shields > shields_max:
                continue
            if p_agility < agility_min or p_agility > agility_max:
                continue
            if p_attack < attack_min or p_attack > attack_max:
                continue
            if p_init < init_min or p_init > init_max:
                continue

            # Base Size
            active_sizes = [s for s, v in base_sizes.items() if v]
            if active_sizes:
                p_size = p_info.get("size", "Small")
                size_map = {"S": "Small", "M": "Medium", "L": "Large", "H": "Huge"}
                allowed_sizes_set = {size_map.get(s, s) for s in active_sizes}
                if p_size not in allowed_sizes_set:
                    continue

            # Faction
            if allowed_factions:
                p_faction = p_info.get("faction", "")
                p_f_norm = p_faction.lower().replace(" ", "").replace("-", "")
                allowed_norm = {f.lower().replace(" ", "").replace("-", "") for f in allowed_factions}
                if p_f_norm not in allowed_norm:
                    continue

            # Ship
            p_ship_xws = p_info.get("ship_xws", "")
            if allowed_ships and p_ship_xws not in allowed_ships:
                continue

            # Text Filter
            if text_filter:
                p_name = p_info.get("name", pid).lower()
                p_ability = p_info.get("ability", "").lower()
                p_ship_name = p_info.get("ship", "").lower()
                p_caption = p_info.get("caption", "").lower()
                match = (
                    (text_filter in p_name)
                    or (text_filter in p_ability)
                    or (text_filter in p_ship_name)
                    or (text_filter in p_caption)
                )
                if not match:
                    continue

            stats[pid] = {
                "xws": pid,
                "games_count": 0,
                "list_count": 0,
                "different_lists_count": 0,
                "wins": 0,
                "_signatures": set(),
            }

    elif mode == "upgrades":
        for u_xws, u_info in all_upgrades.items():
            u_cost = int(
                u_info.get("cost", {}).get("value", 0)
                if isinstance(u_info.get("cost"), dict)
                else (u_info.get("cost") or 0)
            )
            if u_cost < points_min or u_cost > points_max:
                continue

            if allowed_factions:
                u_restrictions = u_info.get("restrictions", [])
                u_factions = set()
                for r in u_restrictions:
                    if "factions" in r:
                        for f in r["factions"]:
                            u_factions.add(f.lower().replace(" ", "").replace("-", ""))

                match_faction = False
                if "unrestricted" in allowed_factions and not u_factions:
                    match_faction = True
                if not match_faction:
                    real_allowed = {f for f in allowed_factions if f != "unrestricted"}
                    if not u_factions.isdisjoint(real_allowed):
                        match_faction = True
                if not match_faction:
                    continue

            # Validity Check
            is_legal = u_info.get("valid_in_standard", False)
            is_wild = u_info.get("wildspace", False)
            is_epic = u_info.get("epic", False)
            show_card = False
            if allowed_formats:
                if ("xwa" in allowed_formats or "amg" in allowed_formats) and is_legal:
                    show_card = True
                if "wildspace" in allowed_formats and is_wild:
                    show_card = True
                if ("xwa_epic" in allowed_formats or "legacy_epic" in allowed_formats) and is_epic:
                    show_card = True
                if data_source == DataSource.LEGACY:
                    legacy_keys = {"legacy_x2po", "legacy_xlc", "ffg"}
                    if not legacy_keys.isdisjoint(allowed_formats):
                        show_card = True
            else:
                if data_source == DataSource.XWA and is_legal:
                    show_card = True
                elif data_source == DataSource.LEGACY:
                    show_card = True

            if not show_card:
                continue

            # Types
            types = set()
            sides = u_info.get("sides", [])
            if sides and isinstance(sides, list):
                for side in sides:
                    if "type" in side:
                        types.add(side["type"].lower())
            else:
                if "type" in u_info:
                    types.add(u_info["type"].lower())

            if allowed_types and types.isdisjoint(allowed_types):
                continue

            # Text Filter
            if text_filter:
                u_name = u_info.get("name", u_xws).lower()
                u_text = ""
                if sides:
                    for side in sides:
                        u_text += " " + side.get("ability", "").lower()
                else:
                    u_text = u_info.get("text", "").lower()
                match = (text_filter in u_name) or (text_filter in u_text)
                if not match:
                    continue

            stats[u_xws] = {
                "xws": u_xws,
                "games_count": 0,
                "list_count": 0,
                "different_lists_count": 0,
                "wins": 0,
                "_signatures": set(),
            }

    # --- PHASE 2: SQL aggregation -------------------------------------------
    # Single GROUP BY query that filters the joined playerstanding/tournament
    # data, unnests the pilots array, and counts per-card metrics in one pass.
    # This replaces the previous Python loop that loaded every row.

    # Build WHERE clauses (pure Python, no DB connection needed).
    where_clauses: list[str] = ["p->>'id' IS NOT NULL"]
    params: dict[str, object] = {}

    if filters.get("date_start"):
        where_clauses.append("t.date >= :date_start")
        params["date_start"] = filters["date_start"]
    if filters.get("date_end"):
        where_clauses.append("t.date <= :date_end")
        params["date_end"] = filters["date_end"]

    sources = filters.get("sources") or filters.get("platforms") or []
    if sources:
        where_clauses.append("t.source = ANY(:sources)")
        params["sources"] = list(sources)
    if filters.get("player_count_min") is not None:
        where_clauses.append("t.player_count >= :pc_min")
        params["pc_min"] = int(filters["player_count_min"])
    if filters.get("player_count_max") is not None:
        where_clauses.append("t.player_count <= :pc_max")
        params["pc_max"] = int(filters["player_count_max"])
    fmts = filters.get("allowed_formats")
    if fmts:
        fmts_list = fmts if isinstance(fmts, (list, set)) else [fmts]
        if fmts_list:
            where_clauses.append("t.format = ANY(:formats)")
            params["formats"] = list(fmts_list)

    # Faction filter — push to SQL via the generated faction_xws_normalized
    # column. Matches the same normalization the catalog filter uses.
    if allowed_factions:
        normalized = [
            f.lower().replace(" ", "").replace("-", "")
            for f in allowed_factions
            if f and f != "all"
        ]
        if normalized:
            where_clauses.append("ps.faction_xws_normalized = ANY(:factions)")
            params["factions"] = normalized

    # Location filters — tournament.location is stored as JSON; access via
    # JSONB ->> operator on the text representation of each sub-field.
    filter_continents = filters.get("continent")
    filter_countries = filters.get("country")
    filter_cities = filters.get("city")
    if filter_continents:
        where_clauses.append("t.location->>'continent' = ANY(:continents)")
        params["continents"] = list(filter_continents)
    if filter_countries:
        where_clauses.append("t.location->>'country' = ANY(:countries)")
        params["countries"] = list(filter_countries)
    if filter_cities:
        where_clauses.append("t.location->>'city' = ANY(:cities)")
        params["cities"] = list(filter_cities)

    # Ship filter (when present) — push to SQL via the pilot_ship_mapping
    # table, which provides a fast lookup from pilot_xws -> ship_xws.
    ship_filter_sql = filters.get("ship") or filters.get("ships")
    if ship_filter_sql:
        if isinstance(ship_filter_sql, str):
            ship_filter_sql = [ship_filter_sql]
        if ship_filter_sql:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM jsonb_array_elements(ps.list_json->'pilots') sp "
                "JOIN pilot_ship_mapping psm ON psm.pilot_xws = (sp->>'id') "
                "WHERE psm.ship_xws = ANY(:ship_filter) "
                "AND psm.source = :ship_source)"
            )
            params["ship_filter"] = list(ship_filter_sql)
            params["ship_source"] = "xwa" if data_source == DataSource.XWA else "legacy"

    # If filter_pilot_id is set, restrict to lists containing that pilot.
    # Achieved with the same list_json->'pilots' containment trick.
    if filter_pilot_id:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM jsonb_array_elements(ps.list_json->'pilots') sp "
            "WHERE sp->>'id' = :filter_pilot_id)"
        )
        params["filter_pilot_id"] = filter_pilot_id

    where_sql = " AND ".join(where_clauses)

    if mode == "pilots":
        sql = text(f"""
            SELECT
                p->>'id' as card_xws,
                COUNT(DISTINCT ps.id) as list_count,
                SUM(COALESCE(ps.swiss_wins, 0) + COALESCE(ps.cut_wins, 0)) as wins,
                SUM(
                    COALESCE(ps.swiss_wins, 0) + COALESCE(ps.swiss_losses, 0) + COALESCE(ps.swiss_draws, 0)
                    + COALESCE(ps.cut_wins, 0) + COALESCE(ps.cut_losses, 0) + COALESCE(ps.cut_draws, 0)
                ) as games,
                COUNT(DISTINCT ps.list_id) as different_lists_count
            FROM playerstanding ps
            JOIN tournament t ON t.id = ps.tournament_id
            JOIN list l ON l.id = ps.list_id
            JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') p ON true
            WHERE {where_sql}
            GROUP BY p->>'id'
        """)
    elif mode == "upgrades":
        # Flatten upgrades: each pilot's `upgrades` may be an object
        # (`{"talent": ["predator"], ...}`) or an array. Use a CTE
        # to first unnest pilots, then flatten upgrades per pilot.
        sql = text(f"""
            WITH pilot_data AS (
                SELECT
                    ps.id as ps_id,
                    ps.list_id,
                    l.list_json,
                    ps.swiss_wins, ps.swiss_losses, ps.swiss_draws,
                    ps.cut_wins, ps.cut_losses, ps.cut_draws,
                    p
                FROM playerstanding ps
                JOIN tournament t ON t.id = ps.tournament_id
                JOIN list l ON l.id = ps.list_id
                JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') p ON true
                WHERE {where_sql}
            ),
            upgrade_values AS (
                SELECT
                    ps_id, list_id,
                    swiss_wins, swiss_losses, swiss_draws,
                    cut_wins, cut_losses, cut_draws,
                    CASE
                        WHEN jsonb_typeof(p->'upgrades') = 'array' THEN p->'upgrades'
                        WHEN jsonb_typeof(p->'upgrades') = 'object' THEN
                            COALESCE(
                                (SELECT jsonb_agg(v)
                                 FROM jsonb_each(p->'upgrades') e,
                                      jsonb_array_elements_text(e.value) v
                                 WHERE jsonb_typeof(e.value) = 'array'),
                                '[]'::jsonb
                            )
                        ELSE '[]'::jsonb
                    END as upgrades_json
                FROM pilot_data
            )
            SELECT
                u_elem as card_xws,
                COUNT(DISTINCT ps_id) as list_count,
                SUM(COALESCE(swiss_wins, 0) + COALESCE(cut_wins, 0)) as wins,
                SUM(
                    COALESCE(swiss_wins, 0) + COALESCE(swiss_losses, 0) + COALESCE(swiss_draws, 0)
                    + COALESCE(cut_wins, 0) + COALESCE(cut_losses, 0) + COALESCE(cut_draws, 0)
                ) as games,
                COUNT(DISTINCT list_id) as different_lists_count
            FROM upgrade_values, jsonb_array_elements_text(upgrades_json) u_elem
            WHERE u_elem IS NOT NULL
            GROUP BY u_elem
        """)
    else:
        # Unknown mode — return whatever the catalog produced.
        return _finalize_results(stats, sort_criteria, sort_direction)

    # SQL execution inside a tight session scope — no Python processing
    # happens while the connection is held. This prevents pool exhaustion
    # under concurrent load.
    with Session(engine) as session:
        result = session.execute(sql, params).fetchall()

    # Map SQL results back into the stats dict (no DB connection needed).
    for row in result:
        card_xws = row[0]
        if not card_xws or card_xws not in stats:
            continue
        s = stats[card_xws]
        s["list_count"] = int(row[1] or 0)
        s["wins"] = int(row[2] or 0)
        s["games_count"] = int(row[3] or 0)
        s["different_lists_count"] = int(row[4] or 0)
        # No per-list signature is collected in SQL — the
        # different_lists_count is already an exact count from the DB.
        s.pop("_signatures", None)

    # Any catalog entries that weren't touched by the SQL still hold a
    # stale `_signatures` set from initialization. Clear it so the
    # finalize step doesn't try to compute len() on it.
    for xws_id, s_data in stats.items():
        s_data.pop("_signatures", None)

    return _finalize_results(stats, sort_criteria, sort_direction)


def _finalize_results(
    stats: dict,
    sort_criteria: SortingCriteria,
    sort_direction: SortDirection,
) -> list[dict]:
    """Finalize stats into a sorted list of result dicts."""
    results: list[dict] = []
    for xws_id, s_data in stats.items():
        results.append(s_data)

    def sort_key(item):
        if sort_criteria == SortingCriteria.POPULARITY:
            return (item["list_count"], item["games_count"])
        elif sort_criteria == SortingCriteria.GAMES:
            return item["games_count"]
        elif sort_criteria == SortingCriteria.WINRATE:
            return item["wins"] / item["games_count"] if item["games_count"] > 0 else 0
        elif sort_criteria == SortingCriteria.NAME:
            return item["xws"]
        elif sort_criteria == SortingCriteria.COST:
            return 0  # Cost not stored in aggregated stats; rely on catalog
        return 0

    results.sort(key=sort_key, reverse=(sort_direction == SortDirection.DESCENDING))
    return results
