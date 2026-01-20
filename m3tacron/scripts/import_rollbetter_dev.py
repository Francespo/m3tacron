import sys
import os
import logging
from playwright.sync_api import sync_playwright
from sqlmodel import Session, select, delete, create_engine, SQLModel

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import models
from m3tacron.backend.models import Tournament, PlayerResult, Match
from m3tacron.backend.scrapers.rollbetter import RollbetterScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImportRollbetterDev")

# DEV DB Configuration
DB_PATH = "rollbetter_dev.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"
dev_engine = create_engine(DATABASE_URL)

def create_dev_db():
    SQLModel.metadata.create_all(dev_engine)

def clean_database():
    logger.info("Cleaning dev database (recreating)...")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception as e:
            logger.warning(f"Could not delete DB file: {e}")
            
    create_dev_db()
    logger.info("Dev Database recreated.")

def save_to_db(session, tournament, players, matches):
    logger.info(f"Saving Tournament: {tournament.name} ({tournament.date})")
    
    session.add(tournament)
    session.commit()
    session.refresh(tournament)
    
    player_map = {}
    for p in players:
        p.tournament_id = tournament.id
        session.add(p)
        session.commit()
        session.refresh(p)
        player_map[p.player_name] = p.id
        
    for m in matches:
        m.tournament_id = tournament.id
        m.player1_id = player_map.get(m.p1_name_temp, 0)
        m.player2_id = player_map.get(m.p2_name_temp, 0)
        m.winner_id = player_map.get(getattr(m, 'winner_name_temp', None), 0)
        if m.is_bye: m.player2_id = None
        
        session.add(m)
    
    session.commit()
    logger.info(f"Saved {len(matches)} matches.")

def run():
    clean_database()
    
    # Test IDs: 2535 (Confirmed Scenarios), 2538 (Standard)
    ids = ["2535", "2538"]
    
    scraper = RollbetterScraper()
    
    try:
        with Session(dev_engine) as session:
            for t_id in ids:
                try:
                    logger.info(f"Importing {t_id}...")
                    tournament, players, matches = scraper.run_full_scrape(t_id)
                    save_to_db(session, tournament, players, matches)
                except Exception as e:
                    logger.error(f"Failed to import {t_id}: {e}")
                    import traceback
                    traceback.print_exc()
    except Exception as e:
        logger.error(f"Session error: {e}")
        
    logger.info("Import process finished.")

if __name__ == "__main__":
    run()
