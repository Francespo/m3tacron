import sys
import os
import sqlite3
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from m3tacron.backend.scrapers.longshanks import LongshanksScraper
from m3tacron.backend.models import Tournament, PlayerResult, Match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BulkImport")

DB_PATH = "longshanks_dev.db"

TOURNAMENTS = [
    # Legacy (Standard/X2PO) - Proxies for XLC mixed if not explicit
    {"id": "30504", "subdomain": "xwing-legacy"}, # Dec Aces League
    {"id": "29336", "subdomain": "xwing-legacy"}, # The Italian Job
    {"id": "27819", "subdomain": "xwing-legacy"}, # Torneo X-Wing Legacy Ludic
    {"id": "26633", "subdomain": "xwing-legacy"}, # Grandpa's Cup
    {"id": "22357", "subdomain": "xwing-legacy"}, # Ratmayer Jan
    {"id": "31423", "subdomain": "xwing-legacy"}, # Mercoledignocchi

    # XWA (2.5)
    {"id": "30230", "subdomain": "xwing"}, # PSO Lomza
    {"id": "31565", "subdomain": "xwing"}, 
    {"id": "31461", "subdomain": "xwing"},
]

def clean_event(cursor, t_id):
    logger.info(f"Cleaning existing data for event {t_id}...")
    url_pattern = f"%{t_id}%"
    cursor.execute("SELECT id FROM tournament WHERE url LIKE ?", (url_pattern,))
    ids = [row[0] for row in cursor.fetchall()]
    ids.append(int(t_id))
    
    for tid in set(ids):
        cursor.execute("DELETE FROM match WHERE tournament_id=?", (tid,))
        cursor.execute("DELETE FROM playerresult WHERE tournament_id=?", (tid,))
        cursor.execute("DELETE FROM tournament WHERE id=?", (tid,))
    
    logger.info("Cleaned.")

def save_to_db(cursor, tournament, players, matches):
    logger.info(f"Saving Tournament: {tournament.name} ({tournament.date})")
    
    t_platform = tournament.platform
    t_format = tournament.format
    if hasattr(t_platform, 'value'): t_platform = t_platform.value
    if hasattr(t_format, 'value'): t_format = t_format.value

    cursor.execute("""
        INSERT INTO tournament (id, name, date, player_count, url, platform, format)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tournament.id, tournament.name, tournament.date, tournament.player_count, tournament.url, t_platform, t_format))
    
    player_map = {}
    eid_map = {}
    for p in players:
        import json
        list_json_str = json.dumps(p.list_json) if p.list_json else "{}"
        cursor.execute("""
            INSERT INTO playerresult (tournament_id, player_name, rank, swiss_rank, swiss_wins, swiss_losses, swiss_draws, points_at_event, list_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tournament.id, p.player_name, p.rank, p.swiss_rank, p.swiss_wins, p.swiss_losses, p.swiss_draws, p.points_at_event, list_json_str))
        player_map[p.player_name] = cursor.lastrowid
        
        # Map External ID if available
        if hasattr(p, 'external_id') and p.external_id:
            eid_map[p.external_id] = cursor.lastrowid
        
    for m in matches:
        # Try linking by External ID first, then Name
        p1_id = 0
        if hasattr(m, 'p1_external_id') and m.p1_external_id:
            p1_id = eid_map.get(m.p1_external_id, 0)
        if p1_id == 0:
            p1_id = player_map.get(m.p1_name_temp, 0)
            
        p2_id = 0
        if hasattr(m, 'p2_external_id') and m.p2_external_id:
            p2_id = eid_map.get(m.p2_external_id, 0)
        if p2_id == 0:
            p2_id = player_map.get(m.p2_name_temp, 0)
            
        # Refine Winner ID logic
        winner_id = 0
        if m.is_bye:
             winner_id = p1_id
        elif m.player1_score > m.player2_score:
             winner_id = p1_id
        elif m.player2_score > m.player1_score:
             winner_id = p2_id
        # Draw = 0
        
        if m.is_bye: p2_id = 0
            
        if m.is_bye: p2_id = 0
            
        # First Player Resolution
        first_player_id = 0
        if hasattr(m, 'first_player_temp_index'):
            if m.first_player_temp_index == 0:
                first_player_id = p1_id
            elif m.first_player_temp_index == 1:
                first_player_id = p2_id
                
        # Scenario
        scenario_val = None
        if m.scenario:
            scenario_val = m.scenario.value if hasattr(m.scenario, 'value') else m.scenario
        
        # Ensure regex enum is converted to string for SQLite
        r_type = m.round_type
        if hasattr(r_type, 'value'): r_type = r_type.value
            
        cursor.execute("""
            INSERT INTO match (tournament_id, round_number, round_type, player1_id, player2_id, winner_id, player1_score, player2_score, is_bye, first_player_id, scenario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tournament.id, m.round_number, r_type, p1_id, p2_id, winner_id, m.player1_score, m.player2_score, m.is_bye, first_player_id, scenario_val))
        
    logger.info(f"Saved {len(matches)} matches.")

def init_dev_db():
    logger.info(f"Initializing {DB_PATH} with explicit schema...")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tournament
    c.execute("""
        CREATE TABLE IF NOT EXISTS tournament (
            id INTEGER PRIMARY KEY,
            name TEXT,
            date TEXT,
            player_count INTEGER,
            url TEXT,
            platform TEXT,
            format TEXT
        )
    """)
    
    # PlayerResult
    c.execute("""
        CREATE TABLE IF NOT EXISTS playerresult (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            player_name TEXT,
            rank INTEGER,
            swiss_rank INTEGER,
            swiss_wins INTEGER,
            swiss_losses INTEGER,
            swiss_draws INTEGER,
            points_at_event INTEGER,
            list_json TEXT,
            FOREIGN KEY(tournament_id) REFERENCES tournament(id)
        )
    """)
    
    # Match
    c.execute("""
        CREATE TABLE IF NOT EXISTS match (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            round_number INTEGER,
            round_type TEXT,
            player1_id INTEGER,
            player2_id INTEGER,
            winner_id INTEGER,
            player1_score INTEGER,
            player2_score INTEGER,
            is_bye INTEGER,
            first_player_id INTEGER,
            scenario TEXT,
            FOREIGN KEY(tournament_id) REFERENCES tournament(id)
        )
    """)
    
    # Clear data from target tables to ensure fresh import
    tables = ["match", "playerresult", "tournament"]
    for t in tables:
        try:
            c.execute(f"DELETE FROM {t}")
        except:
            pass
            
    conn.commit()
    conn.close()
    logger.info(f"{DB_PATH} initialized.")

def run():
    init_dev_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for t in TOURNAMENTS:
        t_id = t["id"]
        sub = t["subdomain"]
        logger.info(f"--- Processing {t_id} ({sub}) ---")
        
        try:
            clean_event(cursor, t_id)
            conn.commit()
            
            scraper = LongshanksScraper(subdomain=sub)
            tournament, players, matches = scraper.run_full_scrape(t_id, subdomain=sub)
            
            save_to_db(cursor, tournament, players, matches)
            conn.commit()
            logger.info(f"Successfully Imported {t_id}")
            
        except Exception as e:
            logger.error(f"Failed to import {t_id}: {e}")
            import traceback
            traceback.print_exc()
            
    conn.close()

if __name__ == "__main__":
    run()
