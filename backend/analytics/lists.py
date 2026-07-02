"""
List Analytics - Aggregation Logic for Squad Lists.

=============================================================================
NAVIGATION MAP
=============================================================================
This file is part of the analytics layer that powers the 4 "heavy" pages:

    /lists     → aggregate_list_stats (this file)
    /squadrons → aggregate_squadron_stats (analytics/squadrons.py)
    /ships     → aggregate_ship_stats (analytics/ships.py)
    /cards/*   → aggregate_card_stats (analytics/core.py)

=============================================================================
DATA MODEL
=============================================================================
Lists live in a normalized `list` table (see backend/models.py) with one row
per unique squad list. The key columns used here are:

    canonical_signature  — md5(list_json::text) hash, UNIQUE, used for GROUP BY
    faction              — XWS faction string ('rebelalliance', etc.)
    faction_xws_normalized — lower(replace(replace(faction, ' ', ''), '-', ''))
                             matches the legacy generated column on playerstanding
    list_json            — the full XWS list as JSONB (read for pilot data)
    points, name, pilot_count, ship_list — pre-extracted metadata

`playerstanding.list_id` is the FK back to this table. Every analytics query
here JOINs `playerstanding ps` → `list l` to aggregate stats per unique list.

=============================================================================
HOW THIS WORKS
=============================================================================
1. `aggregate_list_stats` receives a `filters` dict from the API layer.
2. It builds a dynamic WHERE clause (with shared helpers in filter_helpers.py)
   that pushes filtering to SQL.
3. A single GROUP BY query aggregates games/wins across all matching
   playerstanding rows per list.
4. Python only re-shapes pilots from raw JSON to the Pydantic PilotData schema
   (via _reformat_pilots in api/formatters.py) and computes faction enums.
   No canonicalization, no JSON parsing in the hot path.

=============================================================================
PERFORMANCE
=============================================================================
Pre-normalization, this query was O(96K playerstanding rows) with Python
iteration for canonicalization (~10-15s cold). Post-normalization, the GROUP
BY runs on the ~63K list table rows. With caching (see backend/cache.py), the
second request for the same filter set is instant.

For lazy pagination, add LIMIT/OFFSET to the SQL below — the data is already
fully filtered and aggregated.
"""
from sqlmodel import Session
from sqlalchemy import text
from ..database import engine
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from ..api.formatters import _reformat_pilots
from .filter_helpers import format_filter_clause, ship_list_filter_clause


def aggregate_list_stats(
    filters: dict,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for squad lists using SQL GROUP BY on the
    normalized list table.

    No Python canonicalization needed — list.canonical_signature is
    pre-computed at insert time.
    """
    where_clauses: list[str] = []
    params: dict = {}

    if filters.get("date_start"):
        where_clauses.append("t.date >= :date_start")
        params["date_start"] = filters["date_start"]
    if filters.get("date_end"):
        where_clauses.append("t.date <= :date_end")
        params["date_end"] = filters["date_end"]
    if filters.get("sources") or filters.get("platforms"):
        sources = filters.get("sources") or filters.get("platforms", [])
        if sources:
            where_clauses.append("t.source = ANY(:sources)")
            params["sources"] = list(sources)
    if filters.get("player_count_min") is not None:
        where_clauses.append("t.player_count >= :pc_min")
        params["pc_min"] = int(filters["player_count_min"])
    if filters.get("player_count_max") is not None:
        where_clauses.append("t.player_count <= :pc_max")
        params["pc_max"] = int(filters["player_count_max"])

    fmt_clause = format_filter_clause(filters.get("allowed_formats"), params, leading_and=False)
    if fmt_clause:
        where_clauses.append(fmt_clause)

    if filters.get("factions"):
        facs = filters["factions"]
        if isinstance(facs, (list, set)) and facs:
            normalized = [
                f.lower().replace(" ", "").replace("-", "") for f in facs
            ]
            where_clauses.append("l.faction_xws_normalized = ANY(:factions)")
            params["factions"] = normalized

    # Ship filter — accept both "ship" (singular, used by ship_detail.py)
    # and "ships" (plural, used by the broader API surface).
    #
    # mode="all" → AND semantics: a list matches only when EVERY
    # selected ship is present in its ship_list. Matches the
    # squadrons page behavior: selecting X-wing + A-wing should
    # return lists that contain BOTH, not the union.
    ship_clause = ship_list_filter_clause(
        filters.get("ship") or filters.get("ships"),
        params,
        mode="all",
    )
    if ship_clause:
        where_clauses.append(ship_clause)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    with Session(engine) as session:
        sql = text(
            f"""
            SELECT
                l.canonical_signature,
                l.faction,
                l.faction_xws_normalized,
                l.name,
                l.points,
                l.list_json,
                COUNT(*) as games,
                SUM(
                    COALESCE(ps.swiss_wins, 0) + COALESCE(ps.swiss_losses, 0) +
                    COALESCE(ps.swiss_draws, 0) + COALESCE(ps.cut_wins, 0) +
                    COALESCE(ps.cut_losses, 0) + COALESCE(ps.cut_draws, 0)
                ) as total_games,
                SUM(COALESCE(ps.swiss_wins, 0) + COALESCE(ps.cut_wins, 0)) as wins
            FROM playerstanding ps
            JOIN tournament t ON t.id = ps.tournament_id
            JOIN list l ON l.id = ps.list_id
            WHERE {where_sql}
            GROUP BY l.id, l.canonical_signature, l.faction, l.faction_xws_normalized,
                     l.name, l.points, l.list_json
            """
        )
        result = session.execute(sql, params).fetchall()

    # Build result list — no Python canonicalization, but transform pilots
    # to match the expected Pydantic schema (xws, upgrades as list of {xws}).
    #
    # Row tuple column order:
    #   0 canonical_signature, 1 faction, 2 faction_xws_normalized,
    #   3 name, 4 points, 5 list_json, 6 games, 7 total_games, 8 wins
    final_list = []
    for row in result:
        faction = row[1] or "unknown"
        list_json = row[5]
        if not list_json or not isinstance(list_json, dict):
            continue
        try:
            f_enum = Faction.from_xws(faction)
        except (ValueError, AttributeError):
            f_enum = Faction.UNKNOWN
        pilots_out = _reformat_pilots(list_json.get("pilots", []))
        wins = int(row[8] or 0)
        games = int(row[7] or 0)
        # win_rate as a percentage (0-100), one decimal place. Avoid
        # division-by-zero — empty groups surface as 0.0.
        win_rate = round((wins / games) * 100, 1) if games else 0.0
        final_list.append({
            "signature": row[0],
            "name": row[3] or "",
            "points": row[4] or 0,
            "original_points": 0,
            "faction_xws": f_enum,
            "pilots": pilots_out,
            "wins": wins,
            "games": games,
            "win_rate": win_rate,
        })

    final_list.sort(key=lambda x: x["games"], reverse=True)
    return final_list
