from datetime import timedelta
import logging
from sqlalchemy import select
from sqlmodel import Session
from ..models import Tournament, PlayerStanding
from ..data_structures.source import Source
from ..utils.deduplication import DedupService

logger = logging.getLogger(__name__)
dedup_service = DedupService()

def check_for_duplicates(session: Session, new_tournament: Tournament, new_players: list[PlayerStanding], overwrite: bool = False) -> Tournament | None:
    """Identify if a tournament is a duplicate of another source.
    
    Logic:
    1. Find existing tournaments within +/- 5 days.
    2. Check for similarity using DedupService.
    3. If a match is found:
       - If overwrite=True AND the match has the SAME source, it's NOT a duplicate (it's an update). Return None.
       - Otherwise, it is a duplicate. Return the existing tournament.
    """
    if not new_tournament.date:
        return None
    
    start_date = new_tournament.date - timedelta(days=5)
    end_date = new_tournament.date + timedelta(days=5)
    
    stmt = select(Tournament).where(Tournament.date >= start_date, Tournament.date <= end_date)
    candidates = session.execute(stmt).scalars().all()
    
    if not candidates:
        return None
        
    candidate_ids = [c.id for c in candidates]
    
    stmt_players = select(PlayerStanding).where(PlayerStanding.tournament_id.in_(candidate_ids))
    all_candidate_players = session.execute(stmt_players).scalars().all()
    
    from collections import defaultdict
    players_map = defaultdict(list)
    for p in all_candidate_players:
        if p.tournament_id:
            players_map[p.tournament_id].append(p)
        
    duplicate = dedup_service.find_duplicate(
        target=new_tournament,
        candidates=list(candidates),
        target_players=new_players,
        candidate_players_map=players_map
    )
    
    if duplicate:
        # Special case: If we are in overwrite mode and the source matches, 
        # we treat it as an update rather than a duplicate rejection.
        if overwrite and duplicate.source == new_tournament.source:
            logger.info(f"Tournament '{new_tournament.name}' exists with same source ({duplicate.source}). Allowing overwrite.")
            return None
            
    return duplicate
