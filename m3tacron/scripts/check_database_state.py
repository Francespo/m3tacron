import sys
import os
import logging
from sqlmodel import Session, select, func

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

from m3tacron.backend.database import engine
from m3tacron.backend.models import Tournament, PlayerResult, Match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_db():
    with Session(engine) as session:
        tournaments = session.exec(select(Tournament)).all()
        logger.info(f"Total Tournaments: {len(tournaments)}")
        
        for t in tournaments:
            logger.info("--------------------------------------------------")
            logger.info(f"Tournament: {t.name} (ID: {t.id})")
            logger.info(f"  Date: {t.date}") # Check format here
            logger.info(f"  Format: {t.format}")
            logger.info(f"  Player Count Field: {t.player_count}")
            
            # Count actual players
            p_count = session.exec(select(func.count(PlayerResult.id)).where(PlayerResult.tournament_id == t.id)).one()
            logger.info(f"  Actual Players in DB: {p_count}")
            
            # Check Rounds
            matches = session.exec(select(Match).where(Match.tournament_id == t.id)).all()
            round_nums = sorted(list(set(m.round_number for m in matches)))
            logger.info(f"  Total Matches: {len(matches)}")
            logger.info(f"  Rounds Found: {round_nums}")

if __name__ == "__main__":
    check_db()
