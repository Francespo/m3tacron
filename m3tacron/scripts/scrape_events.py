import argparse
import sys
import json
import logging
from sqlmodel import Session, create_engine, select

# Append project root directory to path to allow importing m3tacron and rxconfig
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

# Local imports
from m3tacron.backend.scrapers.longshanks import LongshanksScraper
from m3tacron.backend.scrapers.rollbetter import RollbetterScraper
from m3tacron.backend.models import Tournament, PlayerResult, Match
from m3tacron.backend.database import create_db_and_tables

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default Database
DEFAULT_DB_URL = "sqlite:///github_scraped.db"

def scrape_tournament(event, engine):
    """
    Scrape a single tournament and save to DB.
    """
    tid = event['id']
    platform = event['platform']
    url = event.get('url', '')
    
    logger.info(f"Processing {platform} tournament {tid}...")
    
    # Check if exists
    with Session(engine) as session:
        statement = select(Tournament).where(Tournament.id == int(tid)).where(Tournament.platform == platform)
        existing = session.exec(statement).first()
        if existing:
            logger.info(f"Tournament {tid} already exists. Skipping.")
            return

    # Initialize Scraper
    scraper = None
    if platform == "longshanks":
        # Check URL for legacy
        subdomain = "xwing-legacy" if "legacy" in url else "xwing"
        scraper = LongshanksScraper(subdomain=subdomain)
    elif platform == "rollbetter":
        scraper = RollbetterScraper()
    else:
        logger.warning(f"Unknown platform {platform} for ID {tid}")
        return

    try:
        # Run Full Scrape
        t_data, players, matches = scraper.run_full_scrape(tid)
        
        # Save to DB
        with Session(engine) as session:
            # Add Tournament
            session.add(t_data)
            session.commit()
            session.refresh(t_data)
            
            # Add Players
            for p in players:
                p.tournament_id = t_data.id
                session.add(p)
            
            # Add Matches
            for m in matches:
                m.tournament_id = t_data.id
                session.add(m)
                
            session.commit()
            logger.info(f"Successfully saved Tournament {tid} with {len(players)} players and {len(matches)} matches.")
            
    except Exception as e:
        logger.error(f"Failed to scrape {tid}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scrape tournaments from JSON input.")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file with events")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_URL, help="Database URL")
    
    args = parser.parse_args()
    
    # Initialize DB
    logger.info(f"Connecting to database: {args.db}")
    engine = create_engine(args.db)
    # Create tables if not exist (using imported helper, but ensuring it uses OUR engine if different)
    # create_db_and_tables relies on global engine in m3tacron.backend.database
    # Here we should manually create tables on the specific engine
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    
    # Load Events
    try:
        with open(args.input, "r") as f:
            events = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        sys.exit(1)
        
    logger.info(f"Found {len(events)} events to process.")
    
    for event in events:
        scrape_tournament(event, engine)
        
    logger.info("Scraping completed.")

if __name__ == "__main__":
    main()
