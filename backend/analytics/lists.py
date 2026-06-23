"""
List Analytics - Aggregation Logic for Squad Lists.

Uses the normalized `list` table for fast list-level aggregation.
GROUP BY list.canonical_signature replaces the old md5() computation
and the Python canonicalization step.
"""
from sqlmodel import Session
from sqlalchemy import text
from ..database import engine
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource


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
    if filters.get("allowed_formats"):
        fmts = filters["allowed_formats"]
        if isinstance(fmts, (list, set)) and fmts:
            where_clauses.append("t.format = ANY(:formats)")
            params["formats"] = list(fmts)
    if filters.get("factions"):
        facs = filters["factions"]
        if isinstance(facs, (list, set)) and facs:
            normalized = [
                f.lower().replace(" ", "").replace("-", "") for f in facs
            ]
            where_clauses.append("l.faction_xws_normalized = ANY(:factions)")
            params["factions"] = normalized
    if filters.get("ships"):
        ships = list(filters["ships"])
        ship_or_parts = []
        for s in ships:
            key = s.replace('-', '_')
            ship_or_parts.append(
                "(l.ship_list = :ship_" + key +
                " OR l.ship_list LIKE :ship_" + key + "_start"
                " OR l.ship_list LIKE :ship_" + key + "_mid"
                " OR l.ship_list LIKE :ship_" + key + "_end)"
            )
            params[f"ship_{key}"] = s
            params[f"ship_{key}_start"] = f"{s},%"
            params[f"ship_{key}_mid"] = f"%,{s},%"
            params[f"ship_{key}_end"] = f"%,{s}"
        where_clauses.append("(" + " OR ".join(ship_or_parts) + ")")

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
        # Transform pilots to match Pydantic schema
        raw_pilots = list_json.get("pilots", [])
        pilots_out = []
        for p in raw_pilots:
            pid = p.get("id") or p.get("name") or ""
            upgrades_list = []
            raw_up = p.get("upgrades", {})
            if isinstance(raw_up, dict):
                for slot, items in raw_up.items():
                    if isinstance(items, list):
                        for item in items:
                            upgrades_list.append({"xws": str(item)})
                    else:
                        upgrades_list.append({"xws": str(items)})
            elif isinstance(raw_up, list):
                for item in raw_up:
                    upgrades_list.append({"xws": str(item)})
            pilots_out.append({"xws": pid, "upgrades": upgrades_list})
        final_list.append({
            "signature": row[0],
            "name": row[3] or "",
            "points": row[4] or 0,
            "original_points": 0,
            "faction_xws": f_enum,
            "pilots": pilots_out,
            "wins": int(row[8] or 0),
            "games": int(row[7] or 0),
        })

    final_list.sort(key=lambda x: x["games"], reverse=True)
    return final_list
