from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from ..database import engine
from ..models import Tournament
from ..analytics.filters import filter_query
from ..data_structures.data_source import DataSource
from ..data_structures.formats import Format
from .schemas import PaginatedTournamentsResponse, TournamentRow, TournamentDetailResponse, PlayerStandingsRow, MatchRow
from .filters import TournamentFilterParams

router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])

@router.get("", response_model=PaginatedTournamentsResponse)
def get_tournaments(
    filters: TournamentFilterParams = Depends(),
):
    with Session(engine) as session:
        query = select(Tournament)
        
        # Apply filters
        query = filter_query(query, filters.dict())
        
        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = session.exec(count_query).one()
        
        # Sorting
        reverse = filters.sort_direction == "desc"
        if filters.sort_metric == "Players":
            query = query.order_by(Tournament.player_count.desc() if reverse else Tournament.player_count.asc())
        else: # Default to Date
            query = query.order_by(Tournament.date.desc() if reverse else Tournament.date.asc())
            
        # Pagination
        query = query.offset(filters.page * filters.size).limit(filters.size)
        results = session.exec(query).all()
        
        def format_location(loc):
            if not loc: return "Online"
            parts = [p for p in [loc.city, loc.country] if p]
            return ", ".join(parts) if parts else "Global"

        items = []
        for t in results:
            format_obj = t.format if isinstance(t.format, Format) else (Format(t.format) if t.format in [f.value for f in Format] else Format.OTHER)
            
            items.append(TournamentRow(
                id=t.id,
                name=t.name,
                date=t.date.strftime("%Y-%m-%d"),
                players=t.player_count,
                format_label=format_obj.label,
                badge_l1=format_obj.badge_label if format_obj != Format.OTHER else "STD",
                badge_l2=format_obj.macro.badge_label if format_obj != Format.OTHER else "???",
                platform_label=t.platform.value if hasattr(t.platform, 'value') else (t.platform or "unknown"),
                location=format_location(t.location),
                url=t.url or "#"
            ))
            
        return PaginatedTournamentsResponse(items=items, total=total, page=filters.page, size=filters.size)
@router.get("/locations")
def get_locations():
    """Returns a list of unique tournament locations (city, country)."""
    with Session(engine) as session:
        # This is a bit complex with SQLModel's Location type, so we'll do it in memory or with a raw select
        # For simplicity and correctness with the custom type:
        all_tournaments = session.exec(select(Tournament)).all()
        locations = set()
        for t in all_tournaments:
            if t.location:
                formatted = f"{t.location.city}, {t.location.country}"
                if t.location.city != "Unknown":
                    locations.add(formatted)
        
        return sorted(list(locations))

@router.get("/{tournament_id}", response_model=TournamentDetailResponse)
def get_tournament_detail(tournament_id: int):
    """Returns full details for a specific tournament."""
    from ..models import PlayerResult, Match
    
    with Session(engine) as session:
        t = session.get(Tournament, tournament_id)
        if not t:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Tournament not found")
            
        def format_location(loc):
            if not loc: return "Online"
            parts = [p for p in [loc.city, loc.country] if p]
            return ", ".join(parts) if parts else "Global"

        format_obj = t.format if isinstance(t.format, Format) else (Format(t.format) if t.format in [f.value for f in Format] else Format.OTHER)

        tournament_row = TournamentRow(
            id=t.id,
            name=t.name,
            date=t.date.strftime("%Y-%m-%d"),
            players=t.player_count,
            format_label=format_obj.label,
            badge_l1=format_obj.badge_label if format_obj != Format.OTHER else "STD",
            badge_l2=format_obj.macro.badge_label if format_obj != Format.OTHER else "???",
            platform_label=t.platform.value if hasattr(t.platform, 'value') else (t.platform or "unknown"),
            location=format_location(t.location),
            url=t.url or "#"
        )
        
        # Get players
        from sqlalchemy import case
        players_query = select(PlayerResult).where(PlayerResult.tournament_id == tournament_id).order_by(
            case((PlayerResult.cut_rank != None, PlayerResult.cut_rank), else_=999), 
            PlayerResult.swiss_rank
        )
        players = session.exec(players_query).all()
        
            
        
        # Helper for player names
        p_names = {p.id: p.player_name for p in players}
        
        match_rows = []
        for m in matches:
            match_rows.append(MatchRow(
                round=m.round_number,
                type=m.round_type.value if hasattr(m.round_type, 'value') else str(m.round_type),
                player1=p_names.get(m.player1_id, "Unknown"),
                player2=p_names.get(m.player2_id, "Unknown"),
                player1_id=m.player1_id or 0,
                player2_id=m.player2_id or 0,
                score1=m.player1_score,
                score2=m.player2_score,
                winner_id=m.winner_id or 0,
                scenario=m.scenario.value if hasattr(m.scenario, 'value') else str(m.scenario)
            ))
            
        return TournamentDetailResponse(
            tournament=tournament_row,
            players_swiss=[p for p in player_rows if p.cut_rank is None],
            players_cut=[p for p in player_rows if p.cut_rank is not None],
            matches=match_rows
        )
