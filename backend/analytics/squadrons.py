"""
Squadron Analytics - Aggregation Logic for Squadron (Ship Composition).

Uses the normalized `list` table for fast ship-composition grouping.
GROUP BY list.ship_list (sorted comma-joined ship names) replaces the
old Python re-grouping that iterated every list_json.
"""
from sqlmodel import Session
from sqlalchemy import text

from ..database import engine
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from .filter_helpers import format_filter_clause, ship_list_filter_clause


def aggregate_squadron_stats(
    filters: dict,
    sort_metric: SortingCriteria = SortingCriteria.GAMES,
    sort_direction: SortDirection = SortDirection.DESCENDING,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for squadrons (combinations of ship chassis).

    Joins on the normalized list table — ship composition is already
    pre-computed as list.ship_list, so no Python re-grouping is needed.
    """
    where_clauses = []
    params: dict = {}

    if filters.get("date_start"):
        where_clauses.append("t.date >= :date_start")
        params["date_start"] = filters["date_start"]
    if filters.get("date_end"):
        where_clauses.append("t.date <= :date_end")
        params["date_end"] = filters["date_end"]

    sources = filters.get("sources") or filters.get("platforms")
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

    facs = filters.get("factions")
    if facs:
        normalized = [f.lower().replace(" ", "").replace("-", "") for f in facs]
        where_clauses.append("l.faction_xws_normalized = ANY(:factions)")
        params["factions"] = normalized

    # Ship filter — use list.ship_list (comma-joined) for fast filter.
    # Accept both "ship" (singular, used by ship_detail.py) and "ships"
    # (plural, used by the broader API surface).
    #
    # mode="all" → AND semantics: a squadron matches only when EVERY
    # selected ship is present in its ship_list. This is the natural
    # choice for squadrons — selecting X-wing + A-wing should show
    # squadrons that contain BOTH, not the union.
    ship_clause = ship_list_filter_clause(
        filters.get("ship") or filters.get("ships"),
        params,
        mode="all",
    )
    if ship_clause:
        where_clauses.append(ship_clause)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # GROUP BY ship_list — no Python post-processing needed
    #
    # NB: `games` must be a SUM of swiss + cut rounds (wins + losses + draws),
    # not `COUNT(*)` of playerstanding rows. A single playerstanding row can
    # represent many games (e.g. swiss_wins=5, swiss_losses=3 → 8 games),
    # and `wins` is also a SUM, so dividing one SUM by a COUNT produces the
    # same units-mismatch bug that drove win_rate > 100%.
    sql = text(
        f"""
        SELECT
            l.faction as faction,
            l.ship_list as ship_list,
            COUNT(DISTINCT ps.id) as popularity,
            SUM(GREATEST(0, COALESCE(ps.swiss_wins, 0)) + GREATEST(0, COALESCE(ps.cut_wins, 0))) as wins,
            SUM(
                GREATEST(0, COALESCE(ps.swiss_wins, 0)) + GREATEST(0, COALESCE(ps.swiss_losses, 0)) +
                GREATEST(0, COALESCE(ps.swiss_draws, 0)) + GREATEST(0, COALESCE(ps.cut_wins, 0)) +
                GREATEST(0, COALESCE(ps.cut_losses, 0)) + GREATEST(0, COALESCE(ps.cut_draws, 0))
            ) as games
        FROM playerstanding ps
        JOIN tournament t ON t.id = ps.tournament_id
        JOIN list l ON l.id = ps.list_id
        WHERE {where_sql}
        GROUP BY l.faction, l.ship_list
        """
    )

    with Session(engine) as session:
        rows = session.execute(sql, params).fetchall()

    # Build result list directly from SQL — no Python re-grouping
    results = []
    for row in rows:
        faction = row[0] or "unknown"
        ship_list_str = row[1] or ""
        popularity = int(row[2] or 0)
        wins_count = int(row[3] or 0)
        games_count = int(row[4] or 0)
        ships = ship_list_str.split(",") if ship_list_str else []
        win_rate = round((wins_count / games_count) * 100, 1) if games_count > 0 else 0.0
        results.append({
            "signature": ", ".join(ships),
            "faction": faction,
            "win_rate": win_rate,
            "popularity": popularity,
            "games": games_count,
            "wins": wins_count,
            "count": popularity,
            "ships": ships,
        })

    # Sort (default: games desc)
    reverse = sort_direction == SortDirection.DESCENDING
    if sort_metric == SortingCriteria.WINRATE:
        results.sort(key=lambda x: x["win_rate"], reverse=reverse)
    else:
        results.sort(key=lambda x: x["games"], reverse=reverse)

    return results
