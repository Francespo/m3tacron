"""
Ship Analytics - Aggregation Logic for Ships.

Aggregates statistics (win rate, popularity, games) per ship per faction.

Counting rules (see ``backend.utils.stats.merge_ship_faction_rows`` for the
testable spec):

1. A ship appearing multiple times in the SAME list counts as ONE list.
2. Games/wins are counted once per list-side — one count per (match, list)
   pair. A list containing N copies of a ship that played M matches
   contributes exactly M games (the playerstanding record is summed once,
   not once per pilot that maps to the ship).
3. If both opposing lists in a match contain the same ship, the match
   counts twice for that ship (once per side), because each side is its
   own playerstanding row.

The SQL below guarantees these rules: the ``ship_lists`` CTE collapses the
pilots-array join to DISTINCT (playerstanding, ship) pairs before any
record values are summed, so a duplicated ship in a list can never
multiply games/wins/list counts.

Faction attribution: each (playerstanding, ship) pair is attributed to the
PILOT's faction (``pilot_ship_mapping.faction``), not the list's faction.
Cross-faction squads therefore attribute each ship to the faction it
actually played as, and the per-faction stats always sum exactly to the
ship's total.
"""
from sqlmodel import Session
from sqlalchemy import text
from ..database import engine
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..utils.stats import merge_ship_faction_rows


def aggregate_ship_stats(
    filters: dict,
    sort_criteria: SortingCriteria = SortingCriteria.LISTS,
    sort_direction: SortDirection = SortDirection.DESCENDING,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for ships using SQL GROUP BY with pilot_ship_mapping.
    Returns list of dicts matching ShipStats schema.
    """
    source_str = "xwa" if data_source == DataSource.XWA else "legacy"

    where_clauses = ["p->>'id' IS NOT NULL"]
    params: dict[str, object] = {"source": source_str}

    if filters.get("date_start"):
        where_clauses.append("t.date >= :date_start"); params["date_start"] = filters["date_start"]
    if filters.get("date_end"):
        where_clauses.append("t.date <= :date_end"); params["date_end"] = filters["date_end"]
    sources = filters.get("sources") or filters.get("platforms") or []
    if sources:
        where_clauses.append("t.source = ANY(:sources)"); params["sources"] = sources
    if filters.get("player_count_min") is not None:
        where_clauses.append("t.player_count >= :pc_min"); params["pc_min"] = int(filters["player_count_min"])
    if filters.get("player_count_max") is not None:
        where_clauses.append("t.player_count <= :pc_max"); params["pc_max"] = int(filters["player_count_max"])
    # Location filters — tournament.location is stored as JSON; access via
    # JSONB ->> operator on the text representation of each sub-field.
    filter_continents = filters.get("continent")
    if filter_continents:
        where_clauses.append("t.location->>'continent' = ANY(:continents)"); params["continents"] = list(filter_continents)
    filter_countries = filters.get("country")
    if filter_countries:
        where_clauses.append("t.location->>'country' = ANY(:countries)"); params["countries"] = list(filter_countries)
    filter_cities = filters.get("city")
    if filter_cities:
        where_clauses.append("t.location->>'city' = ANY(:cities)"); params["cities"] = list(filter_cities)
    fmts = filters.get("allowed_formats")
    if fmts:
        where_clauses.append("t.format = ANY(:formats)"); params["formats"] = list(fmts)
    # Push faction filter to SQL
    facs = filters.get("factions") or filters.get("faction")
    if facs:
        if isinstance(facs, str): facs = [facs]
        normalized = [f.lower().replace(" ", "").replace("-", "") for f in facs]
        where_clauses.append("ps.faction_xws_normalized = ANY(:factions)"); params["factions"] = normalized
    ship_filter = filters.get("ship") or filters.get("ships")
    ship_mode = filters.get("ship_mode", "any")
    if ship_filter:
        if isinstance(ship_filter, str): ship_filter = [ship_filter]
        if ship_mode == "all":
            for i, s in enumerate(ship_filter):
                k = f"ship_all_{i}"
                where_clauses.append(f"EXISTS (SELECT 1 FROM jsonb_array_elements(l.list_json::jsonb->'pilots') sp2 JOIN pilot_ship_mapping psm2 ON psm2.pilot_xws=(sp2->>'id') AND psm2.source=:source WHERE psm2.ship_xws=:{k} AND ps.id=ps.id)")
                params[k] = s
        else:
            where_clauses.append("psm.ship_xws = ANY(:ship_filter)"); params["ship_filter"] = ship_filter
    # Push search filter to SQL (search by ship name via pilot_ship_mapping)
    search = filters.get("search_name")
    if search:
        where_clauses.append("psm.ship_xws ILIKE :search"); params["search"] = f"%{search}%"

    # User wants unknown/multi-faction lists excluded from BOTH overview and
    # detail — not even in multi-faction ships' "all" aggregate. HMP Droid
    # Gunship 763→760 gap is exactly 3 unknown-faction lists.
    # Normalize to catch "Unknown", "unknown ", etc.
    _unknown = "NULLIF(lower(replace(replace(%s, ' ', ''), '-', '')), '') IS NOT NULL AND lower(replace(replace(%s, ' ', ''), '-', '')) <> 'unknown'"
    where_clauses.append(_unknown % ("ps.faction_xws_normalized", "ps.faction_xws_normalized"))
    where_clauses.append(_unknown % ("psm.faction", "psm.faction"))
    where_clauses.append(_unknown % ("l.faction_xws_normalized", "l.faction_xws_normalized"))
    # Multi-faction (mixed) squad: pilots in the list span >1 distinct pilot faction
    where_clauses.append(
        "(SELECT COUNT(DISTINCT lower(replace(replace(COALESCE(NULLIF(mpsm2.faction, ''), 'unknown'), ' ', ''), '-', '')))"
        " FROM jsonb_array_elements(l.list_json::jsonb->'pilots') mp2"
        " JOIN pilot_ship_mapping mpsm2 ON mpsm2.pilot_xws = (mp2->>'id') AND mpsm2.source = :source"
        ") = 1"
    )

    where_clauses.append("(NOT t.is_team_event OR ps.is_team_member)")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # The ship_lists CTE is the core of the counting rules: it collapses the
    # pilots-array join to DISTINCT (playerstanding, ship) pairs BEFORE any
    # record values are summed. Without this, a list containing the same ship
    # twice (e.g. 4 T-65s) would join once per pilot and multiply games/wins.
    #
    # The faction comes from the PILOT (pilot_ship_mapping.faction), not from
    # the list's faction: cross-faction squads (e.g. "battle of" lists mixing
    # Republic + Rebel + Empire ships) must attribute each ship's appearances
    # to the faction the ship itself played as. Using list.faction would dump
    # those mixed lists into "unknown" and make the per-faction stats not sum
    # to the ship's total (the ARC-170 case: 460 + 2166 + 2 != 2628).
    sql = text(f"""
        WITH ship_lists AS (
            SELECT DISTINCT
                ps.id AS ps_id,
                COALESCE(NULLIF(psm.faction, ''), 'unknown') AS faction,
                psm.ship_xws AS ship_xws
            FROM playerstanding ps
            JOIN tournament t ON t.id = ps.tournament_id
            JOIN list l ON l.id = ps.list_id
            JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') p ON true
            JOIN pilot_ship_mapping psm ON psm.pilot_xws = (p->>'id') AND psm.source = :source
            WHERE {where_sql}
        )
        SELECT
            sl.ship_xws,
            sl.faction,
            COUNT(DISTINCT sl.ps_id) as list_count,
            COUNT(DISTINCT ps.list_id) as different_lists_count,
            COUNT(DISTINCT ps.id) as entries_count,
            COUNT(DISTINCT l.ship_list) as squadron_count,
            COALESCE(SUM(GREATEST(0, COALESCE(ps.swiss_wins, 0)) + GREATEST(0, COALESCE(ps.cut_wins, 0))), 0) as wins,
            COALESCE(SUM(GREATEST(0, COALESCE(ps.swiss_wins, 0)) + GREATEST(0, COALESCE(ps.swiss_losses, 0)) + GREATEST(0, COALESCE(ps.swiss_draws, 0))
                + GREATEST(0, COALESCE(ps.cut_wins, 0)) + GREATEST(0, COALESCE(ps.cut_losses, 0)) + GREATEST(0, COALESCE(ps.cut_draws, 0))), 0) as games
        FROM ship_lists sl
        JOIN playerstanding ps ON ps.id = sl.ps_id
        JOIN list l ON l.id = ps.list_id
        GROUP BY sl.ship_xws, sl.faction
    """)

    # SQL execution inside a tight session scope — no Python processing
    # happens while the connection is held. This prevents pool exhaustion
    # under concurrent load.
    with Session(engine) as session:
        result = session.execute(sql, params).fetchall()

    # Python processing (no database connection needed). Per-faction rows
    # are merged into per-ship stats by merge_ship_faction_rows, which
    # preserves the per-faction breakdown for the ships-page faction toggle.
    faction_rows = [
        {
            "ship_xws": row[0],
            "faction": row[1] or "unknown",
            "list_count": row[2] or 0,
            "different_lists_count": row[3] or 0,
            "entries_count": row[4] or 0,
            "squadron_count": row[5] or 0,
            "wins": row[6] or 0,
            "games": row[7] or 0,
        }
        for row in result
    ]
    results = merge_ship_faction_rows(faction_rows)

    for item in results:
        primary_faction = item["factions"][0] if item["factions"] else "unknown"
        try:
            faction_enum = Faction.from_xws(primary_faction)
        except (ValueError, AttributeError):
            faction_enum = Faction.UNKNOWN
        item["faction_xws"] = faction_enum

    # Sort
    def sort_key(item):
        if sort_criteria == SortingCriteria.LISTS:
            return (item["list_count"], item["games_count"])
        elif sort_criteria == SortingCriteria.UNIQUE_LISTS:
            return (item["different_lists_count"], item["games_count"])
        elif sort_criteria == SortingCriteria.GAMES:
            return item["games_count"]
        elif sort_criteria == SortingCriteria.WINRATE:
            return item["wins"] / item["games_count"] if item["games_count"] > 0 else 0
        elif sort_criteria == SortingCriteria.NAME:
            return item["xws"]
        return 0

    results.sort(key=sort_key, reverse=(sort_direction == SortDirection.DESCENDING))
    return results
