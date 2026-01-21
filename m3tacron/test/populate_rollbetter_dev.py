
import logging
import os
import json
import sqlite3
import sys
from datetime import date
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("populate_v2")

# Ensure we can import from the project
sys.path.append(os.getcwd())

from m3tacron.backend.scrapers.rollbetter_v2 import RollbetterScraperV2

DB_PATH = "rollbetter_dev.db"

def init_db(filename):
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    
    # Create tables matching the app's schema if they don't exist
    c.execute("""CREATE TABLE IF NOT EXISTS tournament (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        player_count INTEGER DEFAULT 0,
        platform TEXT NOT NULL,
        url TEXT NOT NULL,
        format TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS playerresult (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL,
        player_name TEXT NOT NULL,
        rank INTEGER NOT NULL,
        swiss_rank INTEGER,
        points_at_event INTEGER DEFAULT 0,
        list_json TEXT,
        FOREIGN KEY (tournament_id) REFERENCES tournament(id)
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS match (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL,
        round_number INTEGER NOT NULL,
        round_type TEXT DEFAULT 'swiss',
        player1_id INTEGER NOT NULL,
        player2_id INTEGER,
        player1_score INTEGER DEFAULT 0,
        player2_score INTEGER DEFAULT 0,
        winner_id INTEGER,
        is_bye BOOLEAN DEFAULT 0,
        FOREIGN KEY (tournament_id) REFERENCES tournament(id)
    )""")
    
    conn.commit()
    return conn

def save_data(conn, t, p, m):
    c = conn.cursor()
    # Tournament
    c.execute("INSERT OR IGNORE INTO tournament VALUES (?, ?, ?, ?, ?, ?, ?)", 
             (t.id, t.name, str(t.date), t.player_count, "rollbetter", t.url, str(t.format)))
    
    # Players
    pmap = {} # Name -> DB ID
    for ply in p:
        s_list = json.dumps(ply.list_json) if ply.list_json else "{}"
        c.execute("INSERT INTO playerresult (tournament_id, player_name, rank, swiss_rank, points_at_event, list_json) VALUES (?, ?, ?, ?, ?, ?)",
                 (t.id, ply.player_name, ply.rank, ply.swiss_rank, ply.points_at_event, s_list))
        pmap[ply.player_name] = c.lastrowid
        
    # Matches
    for match in m:
        p1n = getattr(match, 'p1_name_temp', None)
        p2n = getattr(match, 'p2_name_temp', None)
        wn = getattr(match, 'winner_name_temp', None)
        
        p1_id = pmap.get(p1n)
        p2_id = pmap.get(p2n)
        w_id = pmap.get(wn)
        
        if p1_id:
            c.execute("INSERT INTO match (tournament_id, round_number, round_type, player1_id, player2_id, player1_score, player2_score, winner_id, is_bye) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (t.id, match.round_number, str(match.round_type.value), p1_id, p2_id, match.player1_score, match.player2_score, w_id, match.is_bye))
    
    conn.commit()

def find_targets(count=300):
    targets = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # BROAD SEARCH: No query, just past events. 
            url = "https://rollbetter.gg/tournaments?past=true"
            print(f"Broad searching for any past tournaments...")
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)
            
            # Deep scroll to get a lot of IDs
            for _ in range(20):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)

            found = page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href*="/tournaments/"]'));
                const s = new Set();
                anchors.forEach(a => {
                    const m = a.getAttribute('href').match(/\/tournaments\/(\d+)$/);
                    if (m) s.add(m[1]);
                });
                return Array.from(s);
            }""")
            targets = found[:count]
        except Exception as e:
            print(f"Error finding IDs: {e}")
        finally:
            browser.close()
    return targets

def main():
    conn = init_db(DB_PATH)
    scraper = RollbetterScraperV2()
    
    targets = find_targets(300)
    print(f"Total unique candidates: {len(targets)}")
    
    # Check current count
    c = conn.cursor()
    success_count = c.execute("SELECT count(*) FROM tournament").fetchone()[0]
    limit = 10
    
    for tid in targets:
        if success_count >= limit:
            break
            
        # Check if exists
        c.execute("SELECT id FROM tournament WHERE id=?", (tid,))
        if c.fetchone():
            continue
        
        print(f"Attempting {tid} with V2...")
        try:
            # V2 will handle game filtering itself
            t, p, m = scraper.run_full_scrape(tid)
            save_data(conn, t, p, m)
            success_count += 1
            print(f"Added {t.name} ({len(p)} players, {len(m)} matches)")
        except Exception as e:
            # We don't print skip reason here, scraper logs it.
            pass
            
    conn.close()
    print(f"Done. Database {DB_PATH} is ready with {success_count} tournaments.")

if __name__ == "__main__":
    main()
