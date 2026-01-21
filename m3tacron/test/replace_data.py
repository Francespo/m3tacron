
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
        from sqlalchemy import text
        session.exec(text("DELETE FROM match WHERE tournament_id > 14"))
        session.exec(text("DELETE FROM playerresult WHERE tournament_id > 14"))
        session.exec(text("DELETE FROM tournament WHERE id > 14"))
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
            try: page.click("#cookie_permission .accept", timeout=2000)
            except: pass
            page.wait_for_timeout(3000)
            
            ids = page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href*="/event/"]'));
                const distinctIds = new Set();
                anchors.forEach(a => {
                    const m = a.getAttribute('href').match(/\/event\/(\d+)/);
                    if (m && parseInt(m[1]) > 5000) distinctIds.add(m[1]); 
                    // Filter > 5000 to avoid ancient event weirdness if any
                });
                return Array.from(distinctIds).slice(0, 12);
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
                return Array.from(distinctIds).slice(0, 12);
            }""")
            found_ids["xwing-legacy"] = ids
            print(f"Found Legacy IDs: {ids}")
        except Exception as e:
            print(f"Error finding Legacy IDs: {e}")
            
        browser.close()
        
    return found_ids

def scrape_and_save():
    # 1. Cleanup
    cleanup_mock_data()
    
    # 2. Find IDs
    ids_map = find_ids_via_playwright()
    
    # 3. Scrape
    for subdomain, ids in ids_map.items():
        if not ids: continue
        
        scraper = LongshanksScraper(subdomain=subdomain)
        
        count = 0
        for tid in ids:
            if count >= 10: break # Limit to 10 per subdomain
            
            # Skip if exists
            with Session(engine) as session:
                exists = session.get(Tournament, int(tid))
                if exists:
                    print(f"Tournament {tid} already exists. Skipping.")
                    continue
            
            try:
                print(f"Scraping Tournament {tid} ({subdomain})...")
                # Use run_full_scrape to get everything
                # Note: run_full_scrape might fail on small empty events, scraper throws ValueError
                
                try:
                    t_data, participants, matches = scraper.run_full_scrape(tid)
                except ValueError as ve:
                    print(f"Skipping {tid}: {ve}")
                    continue
                except Exception as e:
                    print(f"Error scraping {tid}: {e}")
                    continue

                # Save to DB
                with Session(engine) as session:
                    # 1. Tournament
                    # Check again for existence (race condition safety)
                    if session.get(Tournament, t_data.id):
                         print(f"Tournament {tid} already exists (race check).")
                         continue

                    session.add(t_data)
                    session.commit()
                    session.refresh(t_data)
                    
                    # 2. Players
                    player_map = {} # Name -> DB ID
                    
                    for p in participants:
                        p.tournament_id = t_data.id # Ensure link
                        session.add(p)
                    session.commit()
                    
                    # refresh players to get IDs
                    # We need to query them back because we lost the object ref association to ID potentially
                    # Or iteration might update them.
                    # Let's query
                    db_players = session.exec(select(PlayerResult).where(PlayerResult.tournament_id == t_data.id)).all()
                    for db_p in db_players:
                        player_map[db_p.player_name] = db_p.id
                        # Also map cleaned names if needed? 
                        # Scraper cleans names. Match names should match scraper names.
                    
                    # 3. Matches
                    matched_count = 0
                    for m in matches:
                        m.tournament_id = t_data.id
                        
                        # Link Players
                        p1_id = player_map.get(getattr(m, 'p1_name_temp', ''))
                        p2_id = player_map.get(getattr(m, 'p2_name_temp', ''))
                        winner_id = player_map.get(getattr(m, 'winner_name_temp', ''))
                        
                        if p1_id: m.player1_id = p1_id
                        if p2_id: m.player2_id = p2_id
                        if winner_id: m.winner_id = winner_id
                        
                        # Only add if at least P1 is identified
                        if m.player1_id:
                            session.add(m)
                            matched_count += 1
                    
                    session.commit()
                    print(f"Saved {t_data.name} with {len(participants)} players and {matched_count} matches.")
                    count += 1
                    
            except Exception as e:
                print(f"Critical error processing {tid}: {e}")
                
if __name__ == "__main__":
    scrape_and_save()
