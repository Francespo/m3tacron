from fastapi import APIRouter, Query
from sqlmodel import Session, select, or_
from sqlalchemy import text
from ..database import engine
from ..models import List
from ..data_structures.data_source import DataSource
from .formatters import enrich_list_data

router = APIRouter(prefix="/api/list", tags=["List Detail"])


@router.get("/{list_id:path}/stats")
def get_list_stats(
    list_id: str,
    data_source: str = Query("xwa", description="Data source: xwa or legacy"),
    allowed_formats: list[str] = Query(None, description="List of allowed formats")
):
    """
    Get aggregated statistics and full composition for a specific list.
    """
    with Session(engine) as session:
        # 1. Try to find the list row directly by canonical_signature OR name.
        # This is a single small lookup instead of a full table scan.
        list_row = session.exec(
            select(List).where(
                or_(
                    List.canonical_signature == list_id,
                    List.name == list_id,
                )
            )
        ).first()

        if not list_row:
            # Match old behavior: return zero-stats response with placeholders
            try: ds_enum = DataSource(data_source)
            except: ds_enum = DataSource.XWA
            return enrich_list_data({
                "signature": list_id,
                "name": "Unknown List",
                "faction": "unknown",
                "games": 0,
                "wins": 0,
                "win_rate": 0.0,
                "popularity": 0,
                "points": 0,
                "pilots": []
            }, source=ds_enum)

        # 2. SQL-side aggregation — match the pattern in squadron_detail.py.
        # We use a single COUNT/SUM query against playerstanding joined with
        # tournament, so the format filter is applied at the SQL level without
        # a Cartesian product. The filter_query helper is not used here because
        # it would either return ORM rows (slow, no aggregation) or require
        # a JOIN we'd then throw away.
        params: dict = {"list_id": list_row.id}
        fmt_clause = ""
        if allowed_formats:
            params["formats"] = list(allowed_formats)
            fmt_clause = " AND t.format = ANY(:formats)"

        stats = session.execute(text(f"""
            SELECT
                COUNT(*) as count,
                SUM(COALESCE(ps.swiss_wins, 0) + COALESCE(ps.cut_wins, 0)) as wins,
                SUM(
                    COALESCE(ps.swiss_wins, 0) + COALESCE(ps.swiss_losses, 0) +
                    COALESCE(ps.swiss_draws, 0) + COALESCE(ps.cut_wins, 0) +
                    COALESCE(ps.cut_losses, 0) + COALESCE(ps.cut_draws, 0)
                ) as total_games
            FROM playerstanding ps
            JOIN tournament t ON t.id = ps.tournament_id
            WHERE ps.list_id = :list_id{fmt_clause}
        """), params).fetchone()

        wins = int(stats[1] or 0) if stats else 0
        games = int(stats[2] or 0) if stats else 0
        count = int(stats[0] or 0) if stats else 0

        pilots = (list_row.list_json or {}).get("pilots", []) if list_row.list_json else []

        raw_stats = {
            "signature": list_row.canonical_signature,
            "name": list_row.name or f"Untitled {list_row.faction} List",
            "faction": list_row.faction or "unknown",
            "games": games,
            "wins": wins,
            "win_rate": round(wins / games * 100, 1) if games > 0 else 0.0,
            "popularity": count,
            "points": list_row.points or 0,
            "pilots": pilots
        }

        try: ds_enum = DataSource(data_source)
        except: ds_enum = DataSource.XWA

        return enrich_list_data(raw_stats, source=ds_enum)
