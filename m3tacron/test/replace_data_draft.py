
import logging
import time
from sqlmodel import Session, select
from playwright.sync_api import sync_playwright
from m3tacron.backend.database import engine
from m3tacron.backend.models import Tournament, PlayerResult, Match
from m3tacron.backend.scrapers.longshanks import LongshanksScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("replace_data")

def cleanup_mock_data():
    """Delete mock tournaments (ID > 14)."""
    with Session(engine) as session:
        print("Deleting mock data (ID > 14)...")
        # Delete children first
        session.exec("DELETE FROM match WHERE tournament_id > 14")
        session.exec("DELETE FROM playerresult WHERE tournament_id > 14")
        session.exec("DELETE FROM tournament WHERE id > 14")
        session.commit()
        print("Cleanup complete.")

def find_ids_via_playwright():
    """Find recent IDs from Longshanks history."""
    found_ids = {"xwing": [], "xwing-legacy": []}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 1. 2.5
        url = "https://xwing.longshanks.org/events/history/"
        try:
            print(f"Scraping IDs from {url}...")
            page.goto(url, timeout=60000)
            # Dismiss cookies
            try: page.click("#cookie_permission .accept", timeout=2000)
            except: pass
            
            page.wait_for_timeout(3000)
            
            ids = page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href*="/event/"]'));
                const distinctIds = new Set();
                anchors.forEach(a => {
                    const m = a.getAttribute('href').match(/\/event\/(\d+)/);
                    // Filter for reasonable recent IDs (e.g. > 5000)
                    if (m && parseInt(m[1]) > 5000) distinctIds.add(m[1]);
                });
                return Array.from(distinctIds).slice(0, 15);
            }""")
            found_ids["xwing"] = ids
            print(f"Found 2.5 IDs: {ids}")
        except Exception as e:
            print(f"Error finding 2.5 IDs: {e}")

        # 2. Legacy
        url = "https://xwing-legacy.longshanks.org/events/history/"
        try:
            print(f"Scraping IDs from {url}...")
            page.goto(url, timeout=60000)
             # Dismiss cookies
            try: page.click("#cookie_permission .accept", timeout=2000)
            except: pass
            
            page.wait_for_timeout(3000)
            
            ids = page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href*="/event/"]'));
                const distinctIds = new Set();
                anchors.forEach(a => {
                    const m = a.getAttribute('href').match(/\/event\/(\d+)/);
                    if (m && parseInt(m[1]) > 100) distinctIds.add(m[1]);
                });
                return Array.from(distinctIds).slice(0, 15);
            }""")
            found_ids["xwing-legacy"] = ids
            print(f"Found Legacy IDs: {ids}")
        except Exception as e:
            print(f"Error finding Legacy IDs: {e}")
            
        browser.close()
        
    return found_ids

def scrape_and_save(ids_map):
    """Scrape and save tournaments."""
    
    for subdomain, ids in ids_map.items():
        if not ids: continue
        
        scraper = LongshanksScraper(subdomain=subdomain)
        
        for tid in ids:
            # Skip if exists (to avoid re-scraping if re-run)
            with Session(engine) as session:
                exists = session.get(Tournament, int(tid))
                if exists:
                    print(f"Tournament {tid} already exists. Skipping.")
                    continue
            
            try:
                print(f"Scraping Tournament {tid} ({subdomain})...")
                # Run full scrape
                # Note: run_full_scrape is not in the BaseScraper interface but logic is in specific methods
                # We can construct the object manually
                
                # 1. Tournament Info
                t_data = scraper.get_tournament_data(tid)
                
                # 2. Players
                participants = scraper.get_participants(tid)
                
                # 3. Matches
                matches = scraper.get_matches(tid)
                
                # Save to DB
                with Session(engine) as session:
                    # Merge if ID conflicts? The ID comes from Longshanks, so check again.
                    # We already checked at top of loop.
                    
                    session.add(t_data)
                    session.commit() # Commit T first to get PK (though PK is set manually)
                    
                    for p in participants:
                        session.add(p)
                    session.commit() # Commit players
                    
                    # Mapping player names to IDs for matches
                    # Note: get_matches returns Matches with player IDs if linked, but if unlinked 
                    # we might need to map by name. 
                    # The Longshanks scraper implementation attempts to extract IDs.
                    # But the Match model expects IDs. 
                    # Let's verify if scraper fills IDs.
                    # Scraper uses `p1_id` from link. 
                    
                    # We need to map `p1_id` (longshanks ID) to `PlayerResult.id` (DB ID)?
                    # No, `PlayerResult.id` is autoincrement PK in DB?
                    # Let's check model. `PlayerResult(rx.Model, table=True)`. Yes, `id` is PK.
                    # But Longshanks ID is external.
                    # The scraper returns Matches with `player1_id` field set?
                    # In `longshanks.py`:
                    # m = Match(..., player1_id=p1Id...) 
                    # Wait, `player1_id` in Match model is FK to `PlayerResult.id`.
                    # Longshanks scraper extracts `p1Id` which is the Longshanks User ID.
                    # This is NOT the `PlayerResult.id`.
                    # We must FIX this mapping.
                    
                    # Re-fetching players to build map: (external_id? or name?) -> PlayerResult.id
                    # PlayerResult doesn't have `external_id` field in the visible model in `models.py`.
                    # Wait, I saw `models.py`. It has `player_name` and `rank`.
                    # `LongshanksScraper.get_participants` uses `participants.append(pr)`.
                    # It dynamically adds `.external_id` attribute but it's not in the DB schema.
                    # Matches rely on `p1_id` FK.
                    
                    # Correct Logic:
                    # 1. Save players.
                    # 2. Build map: Name -> PlayerResult.id (Primary Key)
                    # 3. Update matches with these PKs.
                    
                    # Refresh players to get IDs
                    # Or query them.
                    db_players = session.exec(select(PlayerResult).where(PlayerResult.tournament_id == t_data.id)).all()
                    name_map = {p.player_name: p.id for p in db_players}
                    
                    for m in matches:
                        # Matches scraped have scraped names in them? 
                        # `longshanks.py` logic: `extracted.push({ ... p1: p1 ... })`
                        # But `get_matches` returns `list[Match]`. 
                        # Wait, `get_matches` in `longshanks.py` returns a list of DICTS or Objects?
                        # It returns `list[Match]`.
                        # But wait, looking at `longshanks.py` earlier:
                        # It does NOT construct `Match` objects. It is incomplete in the view I saw?
                        # Ah, I need to check `longshanks.py` tail again.
                        # The file view was truncated at line 800.
                        # I must assume it returns something usable or I fix it.
                        
                        # Let's look at `longshanks.py` again to be sure what `get_matches` does.
                        pass # Placeholder
            
            except Exception as e:
                print(f"Failed to scrape {tid}: {e}")
                
if __name__ == "__main__":
    cleanup_mock_data()
    ids = find_ids_via_playwright()
    # Scrape detailed data
    # (I'll implement the loop logic properly in the next step, I need to see `longshanks.py` tail first 
    # to handle Match association correctly)
    print("Pre-computation done. Ready for main scraping logic.")
