from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from ..database import engine
from ..models import Tournament
from ..analytics.filters import filter_query
from ..data_structures.data_source import DataSource
from .schemas import PaginatedTournamentsResponse, TournamentRow
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
            items.append(TournamentRow(
                id=t.id,
                name=t.name,
                date=t.date.strftime("%Y-%m-%d"),
                players=t.player_count,
                format_label=t.format.value if hasattr(t.format, 'value') else (t.format or "other"),
                badge_l1="Standard" if t.player_count > 50 else ("Small" if t.player_count < 10 else "Medium"),
                badge_l2=format_location(t.location),
                platform_label=t.platform.value if hasattr(t.platform, 'value') else (t.platform or "unknown"),
                location=format_location(t.location),
                url=t.url or "#"
            ))
            
        return PaginatedTournamentsResponse(items=items, total=total, page=filters.page, size=filters.size)
