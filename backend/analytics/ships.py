"""
Ship Analytics - Aggregation Logic for Ships.

Aggregates statistics (win rate, popularity, games) per ship per faction.
"""
from sqlmodel import Session
from sqlalchemy import text
from ..database import engine
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection


def aggregate_ship_stats(
    filters: dict,
    sort_criteria: SortingCriteria = SortingCriteria.POPULARITY,
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
    fmts = filters.get("allowed_formats")
    if fmts:
        where_clauses.append("t.format = ANY(:formats)"); params["formats"] = list(fmts)
    # Push faction filter to SQL
    facs = filters.get("factions") or filters.get("faction")
    if facs:
        if isinstance(facs, str): facs = [facs]
        normalized = [f.lower().replace(" ", "").replace("-", "") for f in facs]
        where_clauses.append("ps.faction_xws_normalized = ANY(:factions)"); params["factions"] = normalized
    # Push ship filter to SQL
    ship_filter = filters.get("ship") or filters.get("ships")
    if ship_filter:
        if isinstance(ship_filter, str): ship_filter = [ship_filter]
        where_clauses.append("psm.ship_xws = ANY(:ship_filter)"); params["ship_filter"] = ship_filter
    # Push search filter to SQL (search by ship name via pilot_ship_mapping)
    search = filters.get("search_name")
    if search:
        where_clauses.append("psm.ship_xws ILIKE :search"); params["search"] = f"%{search}%"

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = text(f"""
        SELECT
            psm.ship_xws,
            array_remove(array_agg(DISTINCT ps.list_json->>'faction'), NULL) as factions,
            COUNT(DISTINCT ps.id) as list_count,
            SUM(COALESCE(ps.swiss_wins, 0) + COALESCE(ps.cut_wins, 0)) as wins,
            SUM(COALESCE(ps.swiss_wins, 0) + COALESCE(ps.swiss_losses, 0) + COALESCE(ps.swiss_draws, 0)
                + COALESCE(ps.cut_wins, 0) + COALESCE(ps.cut_losses, 0) + COALESCE(ps.cut_draws, 0)) as games,
            COUNT(DISTINCT md5(ps.list_json::text)) as different_lists_count
        FROM playerstanding ps
        JOIN tournament t ON t.id = ps.tournament_id
        JOIN jsonb_array_elements(ps.list_json->'pilots') p ON true
        JOIN pilot_ship_mapping psm ON psm.pilot_xws = (p->>'id') AND psm.source = :source
        WHERE {where_sql}
        GROUP BY psm.ship_xws
        ORDER BY games DESC
    """)

    # SQL execution inside a tight session scope — no Python processing
    # happens while the connection is held. This prevents pool exhaustion
    # under concurrent load.
    with Session(engine) as session:
        result = session.execute(sql, params).fetchall()

    # Python processing (no database connection needed)
    results = []
    for row in result:
        ship_xws = row[0]
        factions = row[1] or ["unknown"]
        list_count = row[2] or 0
        wins = row[3] or 0
        games = row[4] or 0
        different_lists = row[5] or 0

        # Use first faction for display, store all factions
        primary_faction = factions[0] if factions else "unknown"
        try:
            faction_enum = Faction.from_xws(primary_faction)
        except (ValueError, AttributeError):
            faction_enum = Faction.UNKNOWN

        results.append({
            "xws": ship_xws,
            "faction_xws": faction_enum,
            "factions": factions,
            "games_count": games,
            "list_count": list_count,
            "different_lists_count": different_lists,
            "wins": wins,
        })

    # Sort
    def sort_key(item):
        if sort_criteria == SortingCriteria.POPULARITY:
            return (item["list_count"], item["games_count"])
        elif sort_criteria == SortingCriteria.GAMES:
            return item["games_count"]
        elif sort_criteria == SortingCriteria.WINRATE:
            return item["wins"] / item["games_count"] if item["games_count"] > 0 else 0
        elif sort_criteria == SortingCriteria.NAME:
            return item["xws"]
        return 0

    results.sort(key=sort_key, reverse=(sort_direction == SortDirection.DESCENDING))
    return results
