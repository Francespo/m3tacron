"""
Squadron Analytics - Aggregation Logic for Squadron (Ship Composition).
"""
from sqlmodel import Session
from sqlalchemy import text

from ..database import engine
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..utils.xwing_data.pilots import load_all_pilots


def aggregate_squadron_stats(
    filters: dict,
    sort_metric: SortingCriteria = SortingCriteria.GAMES,
    sort_direction: SortDirection = SortDirection.DESCENDING,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for squadrons (combinations of ship chassis).

    Uses SQL GROUP BY over the full list_json to avoid loading all
    PlayerStanding rows into Python. Ship resolution happens in Python
    on the much smaller grouped result set, since the squadron signature
    is just the sorted ship list.
    """
    # Build WHERE clauses
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

    fmts = filters.get("allowed_formats")
    if fmts:
        where_clauses.append("t.format = ANY(:formats)")
        params["formats"] = list(fmts)

    facs = filters.get("factions")
    if facs:
        normalized = [f.lower().replace(" ", "").replace("-", "") for f in facs]
        where_clauses.append("ps.faction_xws_normalized = ANY(:factions)")
        params["factions"] = normalized

    if filters.get("ships"):
        where_clauses.append(
            "EXISTS (SELECT 1 FROM jsonb_array_elements(ps.list_json->'pilots') p "
            "WHERE p->>'ship' = ANY(:ships))"
        )
        params["ships"] = list(filters["ships"])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = text(
        f"""
        SELECT
            ps.list_json->>'faction' as faction,
            md5(ps.list_json::text) as list_hash,
            COUNT(*) as games,
            SUM(COALESCE(ps.swiss_wins, 0) + COALESCE(ps.cut_wins, 0)) as wins,
            (array_agg(ps.list_json))[1] as sample_list
        FROM playerstanding ps
        JOIN tournament t ON t.id = ps.tournament_id
        WHERE {where_sql}
        GROUP BY ps.list_json->>'faction', list_hash
        ORDER BY games DESC
        """
    )

    with Session(engine) as session:
        result = session.execute(sql, params).fetchall()

    # Pre-load pilot data for ship resolution. lru_cached, so this is cheap.
    all_pilots = load_all_pilots(data_source)

    # Phase 2: Extract ship compositions and aggregate into squadron buckets.
    # Note: we have to re-derive "games" here (the SQL query counts *rows*,
    # not actual games played by the player), so the original semantics from
    # the Python implementation are preserved.
    squadron_stats: dict[str, dict] = {}

    for row in result:
        faction = row[0] or "unknown"
        games_count = row[2] or 0
        wins_count = row[3] or 0
        xws = row[4]

        if not xws or not isinstance(xws, dict):
            continue

        pilots = xws.get("pilots", [])
        if not pilots:
            continue

        # Resolve ships from pilot ids.
        ships = []
        for p in pilots:
            pid = p.get("id") or p.get("name")
            if pid and pid in all_pilots:
                s_xws = all_pilots[pid].get("ship_xws") or "unknown"
            else:
                # Fall back to the ship key on the pilot if the pilot is unknown.
                s_xws = p.get("ship") or "unknown"
            ships.append(s_xws)

        ships.sort()
        signature = ", ".join(ships)

        if signature in squadron_stats:
            s = squadron_stats[signature]
            s["wins"] += wins_count
            s["games"] += games_count
            s["count"] += 1
        else:
            squadron_stats[signature] = {
                "faction": faction,
                "signature": signature,
                "wins": wins_count,
                "games": games_count,
                "count": 1,
                "ships": ships,
            }

    results = []
    for data in squadron_stats.values():
        win_rate = (
            round((data["wins"] / data["games"]) * 100, 1) if data["games"] > 0 else 0.0
        )
        results.append(
            {
                "signature": data["signature"],
                "faction": data["faction"],
                "win_rate": win_rate,
                "popularity": data["count"],
                "games": data["games"],
                "wins": data["wins"],
                "count": data["count"],
                "ships": data["ships"],
            }
        )

    # Defaults to sorting by games desc (matches previous behavior).
    results.sort(key=lambda x: x["games"], reverse=True)
    return results
