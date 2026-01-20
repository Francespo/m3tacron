import sys
import os
import logging
from playwright.sync_api import sync_playwright
from sqlmodel import Session, select, delete

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from m3tacron.backend.database import create_db_and_tables, engine
from m3tacron.backend.models import Tournament, PlayerResult, Match
from m3tacron.backend.scrapers.rollbetter import RollbetterScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImportRollbetter")

# Using the main DB
DB_PATH = "metacron_v2.db"

def clean_database():
    logger.info("Cleaning database (recreating)...")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception as e:
            logger.warning(f"Could not delete DB file: {e}")
            
    create_db_and_tables()
    logger.info("Database recreated.")

def discover_recent_tournaments(limit=10):
    """
    Scrape rollbetter.gg index for recent completed X-Wing tournaments.
    """
    logger.info("Discovering recent tournaments...")
    ids = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Search page for X-Wing 2.5
        # The URL structure for search/filter might need adjustment if this fails, 
        # but let's try the main list and filtering or a specific search URL if known.
        # Exploring 'https://rollbetter.gg/tournaments' and filtering by Game system is interacting with UI.
        # Let's try to go to the filtered URL if possible. 
        # https://rollbetter.gg/tournaments?game=xwing25 seems to be a valid guess or similar.
        # Actually, let's just go to /tournaments and hope we can filter or find useful data.
        # Better: let's try to find "Recent" or "Past" events.
        
        # Based on manual observation of such sites, usually there is a list.
        # Let's try: https://rollbetter.gg/tournaments
        # And we look for links like /tournaments/{id}
        
        page.goto("https://rollbetter.gg/tournaments?game=x-wing-2-5-edition", wait_until="domcontentloaded")
        page.wait_for_timeout(3000) # Wait for JS
        
        # We need "Past" tournaments usually. 
        # Rollbetter UI has tabs "Upcoming", "In Progress", "Completed".
        # We want "Completed".
        try:
            page.locator("button:has-text('Completed')").click()
            page.wait_for_timeout(2000)
        except:
            logger.warning("Could not find 'Completed' tab, scraping whatever is visible.")

        # Extract links
        # Links are usually <a href="/tournaments/123">
        # Extract links using evaluate
        hrefs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll("a[href^='/tournaments/']")).map(a => a.getAttribute('href'));
        }""")
        
        seen = set()
        for h in hrefs:
            # format /tournaments/123
            parts = h.split("/")
            if len(parts) >= 3 and parts[2].isdigit():
                tid = parts[2]
                if tid not in seen:
                    ids.append(tid)
                    seen.add(tid)
                    if len(ids) >= limit:
                        break
        
        browser.close()
    
    logger.info(f"Discovered IDs: {ids}")
    return ids

def save_to_db(session, tournament, players, matches):
    logger.info(f"Saving Tournament: {tournament.name} ({tournament.date})")
    
    # Tournament is already an object, but we need to ensure it's attached or just add it
    # We scraped objects but they are detached.
    # Also need to handle relations.
    
    # Add tournament
    session.add(tournament)
    session.commit()
    session.refresh(tournament) # Get ID if auto-generated (though we manually set it)
    
    # Add Players
    # Accessing tournament.id is safe now
    player_map = {}
    for p in players:
        p.tournament_id = tournament.id
        session.add(p)
        session.commit()
        session.refresh(p)
        player_map[p.player_name] = p.id
        
    # Add Matches
    for m in matches:
        m.tournament_id = tournament.id
        m.player1_id = player_map.get(m.p1_name_temp, 0)
        m.player2_id = player_map.get(m.p2_name_temp, 0)
        m.winner_id = player_map.get(getattr(m, 'winner_name_temp', None), 0)
        if m.is_bye: m.player2_id = None # Set to None for DB if nullable, or 0? Model says int|None
        
        session.add(m)
    
    session.commit()
    logger.info(f"Saved {len(matches)} matches.")

def run():
    clean_database()
    
    ids = discover_recent_tournaments(limit=5) # Reduced limit to save time
    if "2538" not in ids:
        ids.append("2538")
    
    scraper = RollbetterScraper()
    
    try:
        with Session(engine) as session:
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
