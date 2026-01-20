import sys
import os
import logging
from sqlmodel import Session

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

from m3tacron.backend.database import engine, create_db_and_tables
from m3tacron.backend.scrapers.rollbetter import RollbetterScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of 4 IDs
TOURNAMENT_IDS = [
    "2477", "2505", "2540", "2542"
]

def reset_database():
    """Drop and recreate all tables."""
    logger.info("Resetting database...")
    from sqlmodel import SQLModel
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()
    logger.info("Database reset complete.")

def import_tournaments():
    reset_database()
    scraper = RollbetterScraper()
    
    with Session(engine) as session:
        for tid in TOURNAMENT_IDS:
            try:
                logger.info(f"Scraping Tournament {tid}...")
                # Run updated full scrape (with format inference)
                t_model, players, matches = scraper.run_full_scrape(tid)
                
                # Log Verify
                logger.info(f"Tournament: {t_model.name}")
                logger.info(f"Date: {t_model.date}")
                logger.info(f"Count: {t_model.player_count}")
                logger.info(f"Format: {t_model.format}")
                
                # Save Tournament
                session.add(t_model)
                session.commit()
                session.refresh(t_model)
                
                # Save Players
                player_map = {}
                for p in players:
                    p.tournament_id = t_model.id
                    session.add(p)
                session.commit()
                
                for p in players:
                    # Update local map for match resolution
                    player_map[p.player_name] = p.id
                    
                logger.info(f"Saved {len(players)} players.")

                # Save Matches
                match_count = 0
                for m in matches:
                    m.tournament_id = t_model.id
                    
                    # Resolve IDs from Scraper's temporary name fields
                    p1_name = getattr(m, 'p1_name_temp', '')
                    p2_name = getattr(m, 'p2_name_temp', '')
                    w_name = getattr(m, 'winner_name_temp', '')
                    
                    p1_id = player_map.get(p1_name)
                    p2_id = player_map.get(p2_name)
                    
                    if p1_id:
                        m.player1_id = p1_id
                        
                        if p2_id:
                            m.player2_id = p2_id
                        elif m.is_bye:
                            m.player2_id = None
                        else:
                            m.player2_id = None 
                        
                        # Resolve Winner
                        if w_name in player_map:
                             m.winner_id = player_map[w_name]
                        elif m.player1_score > m.player2_score:
                             m.winner_id = p1_id
                        elif m.player2_score > m.player1_score and p2_id:
                             m.winner_id = p2_id
                        else:
                             m.winner_id = None
                             
                        session.add(m)
                        match_count += 1
                
                session.commit()
                logger.info(f"Saved {match_count} matches.")
                
            except Exception as e:
                logger.error(f"Failed to import {tid}: {e}")
                continue

if __name__ == "__main__":
    import_tournaments()
