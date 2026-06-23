from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session
from sqlalchemy import text

from ..database import engine
from ..data_structures.data_source import DataSource
from .formatters import enrich_list_data

router = APIRouter(prefix="/api/squadron", tags=["Squadron Detail"])


def _normalize_ship_signature(signature: str) -> str:
    """
    Normalize a squadron URL signature (e.g. 'btla4ywing, t65xwing')
    to the DB ship_list format (comma-joined, no space: 'btla4ywing,t65xwing').
    """
    if not signature:
        return ""
    return signature.replace(" ", "")


def _add_format_clause(filters: dict, params: dict) -> str:
    """Return an extra SQL fragment for format filter, mutating params."""
    fmts = filters.get("allowed_formats")
    if isinstance(fmts, (list, set)) and fmts:
        params["formats"] = list(fmts)
        return " AND t.format = ANY(:formats)"
    return ""


@router.get("/{signature:path}/stats")
def get_squadron_stats(
    signature: str,
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    allowed_formats: list[str] = Query(None, description="List of allowed formats")
):
    """
    Get aggregated statistics for a specific squadron signature.

    Uses the normalized `list.ship_list` field for a SQL-side filter,
    so we only process rows that match the requested squadron.
    """
    filters = {"allowed_formats": allowed_formats}
    ship_sig = _normalize_ship_signature(signature)

    with Session(engine) as session:
        # Pre-computed faction lives on the list row.
        list_row = session.execute(
            text("SELECT faction FROM list WHERE ship_list = :ship_sig LIMIT 1"),
            {"ship_sig": ship_sig},
        ).first()
        faction = list_row[0] if list_row and list_row[0] else "Unknown"

        params: dict = {"ship_sig": ship_sig}
        fmt_clause = _add_format_clause(filters, params)

        sql = text(
            f"""
            SELECT
                COUNT(*) as count,
                SUM(
                    COALESCE(ps.swiss_wins, 0) + COALESCE(ps.swiss_losses, 0) +
                    COALESCE(ps.swiss_draws, 0) + COALESCE(ps.cut_wins, 0) +
                    COALESCE(ps.cut_losses, 0) + COALESCE(ps.cut_draws, 0)
                ) as games,
                SUM(COALESCE(ps.swiss_wins, 0) + COALESCE(ps.cut_wins, 0)) as wins
            FROM playerstanding ps
            JOIN list l ON l.id = ps.list_id
            JOIN tournament t ON t.id = ps.tournament_id
            WHERE l.ship_list = :ship_sig{fmt_clause}
            """
        )
        row = session.execute(sql, params).first()
        count = int(row[0] or 0) if row else 0
        games = int(row[1] or 0) if row else 0
        wins = int(row[2] or 0) if row else 0

        if games == 0:
            raise HTTPException(status_code=404, detail="Squadron not found or has no games")

        return {
            "signature": signature,
            "faction": faction,
            "games": games,
            "wins": wins,
            "win_rate": round(wins / games * 100, 1),
            "popularity": count
        }


@router.get("/{signature:path}/pilots")
def get_squadron_pilots(
    signature: str,
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    allowed_formats: list[str] = Query(None, description="List of allowed formats")
):
    """
    Get pilot breakdown for a specific squadron signature.

    Uses JOIN on the list table so we only process rows that match
    the requested ship composition, and reads pilots directly from
    list.list_json (one row per signature, not N rows in playerstanding).
    """
    filters = {"allowed_formats": allowed_formats}
    ship_sig = _normalize_ship_signature(signature)

    with Session(engine) as session:
        params: dict = {"ship_sig": ship_sig}
        fmt_clause = _add_format_clause(filters, params)

        # GROUP BY list_id so we de-duplicate the JSON work; aggregate stats
        # from playerstanding in SQL.
        sql = text(
            f"""
            SELECT
                l.list_json,
                COUNT(*) as count,
                SUM(
                    COALESCE(ps.swiss_wins, 0) + COALESCE(ps.swiss_losses, 0) +
                    COALESCE(ps.swiss_draws, 0) + COALESCE(ps.cut_wins, 0) +
                    COALESCE(ps.cut_losses, 0) + COALESCE(ps.cut_draws, 0)
                ) as games,
                SUM(COALESCE(ps.swiss_wins, 0) + COALESCE(ps.cut_wins, 0)) as wins
            FROM playerstanding ps
            JOIN list l ON l.id = ps.list_id
            JOIN tournament t ON t.id = ps.tournament_id
            WHERE l.ship_list = :ship_sig{fmt_clause}
            GROUP BY l.id, l.list_json
            """
        )
        rows = session.execute(sql, params).fetchall()

    pilot_stats: dict[str, dict] = {}
    total_games = 0

    for row in rows:
        list_json = row[0]
        if not list_json or not isinstance(list_json, dict):
            continue
        pilots = list_json.get("pilots", [])
        if not pilots:
            continue

        games = int(row[2] or 0)
        wins = int(row[3] or 0)
        total_games += games

        for p in pilots:
            p_id = p.get("id") or p.get("name") or "unknown"
            if p_id not in pilot_stats:
                pilot_stats[p_id] = {
                    "pilot_xws": p_id,
                    "ship_xws": p.get("ship") or "unknown",
                    "name": p.get("name", p_id),
                    "cost": p.get("points", 0),
                    "games": 0,
                    "wins": 0
                }
            pilot_stats[p_id]["games"] += games
            pilot_stats[p_id]["wins"] += wins

    results = []
    for p_id, stats in pilot_stats.items():
        w_g = stats["games"]
        win_rate = round(stats["wins"] / w_g * 100, 1) if w_g > 0 else 0.0
        percent_of_squadron = round(w_g / total_games * 100, 1) if total_games > 0 else 0.0

        results.append({
            "pilot_xws": stats["pilot_xws"],
            "ship_xws": stats["ship_xws"],
            "name": stats["name"],
            "cost": stats["cost"],
            "games": w_g,
            "win_rate": win_rate,
            "percent_of_squadron": percent_of_squadron
        })

    results.sort(key=lambda x: x["games"], reverse=True)
    return results


@router.get("/{signature:path}/lists")
def get_squadron_lists(
    signature: str,
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    allowed_formats: list[str] = Query(None, description="List of allowed formats")
):
    """
    Get top performing lists that use exactly this squadron signature.

    Filters the list table by ship_list at the SQL level instead of
    fetching all lists and re-computing ship signatures in Python.
    """
    try: ds_enum = DataSource(data_source)
    except: ds_enum = DataSource.XWA

    filters = {"allowed_formats": allowed_formats}
    ship_sig = _normalize_ship_signature(signature)

    with Session(engine) as session:
        params: dict = {"ship_sig": ship_sig}
        fmt_clause = _add_format_clause(filters, params)

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
            JOIN list l ON l.id = ps.list_id
            JOIN tournament t ON t.id = ps.tournament_id
            WHERE l.ship_list = :ship_sig{fmt_clause}
            GROUP BY l.id, l.canonical_signature, l.faction, l.faction_xws_normalized,
                     l.name, l.points, l.list_json
            """
        )
        rows = session.execute(sql, params).fetchall()

    squadron_lists = []
    for row in rows:
        list_json = row[5]
        if not list_json or not isinstance(list_json, dict):
            continue
        # enrich_list_data expects upgrades in the original format:
        # {"slot_xws": [upgrade_xws, ...], ...} (slot → list of upgrade IDs).
        # The raw list_json already has this format, so we can pass it through
        # without reformatting.
        l_data = {
            "signature": row[0],
            "name": row[3] or "",
            "points": row[4] or 0,
            "original_points": 0,
            "faction_xws": row[2] or "unknown",
            "pilots": list_json.get("pilots", []),
            "wins": int(row[7] or 0),
            "games": int(row[6] or 0),
        }
        squadron_lists.append(enrich_list_data(l_data, source=ds_enum))

    squadron_lists.sort(key=lambda x: x.games, reverse=True)
    return squadron_lists[:20]
