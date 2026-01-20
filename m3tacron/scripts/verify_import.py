import sys
import os
import sqlite3
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from m3tacron.backend.scrapers.longshanks import LongshanksScraper
from m3tacron.backend.models import Tournament, PlayerResult, Match

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_import")

DB_PATH = "metacron.db"

def clean_event(cursor, t_id):
    logger.info(f"Cleaning existing data for event {t_id}...")
    # Delete match/player by tournament_id (which strictly matches the Foreign Keys)
    # BUT first find the IDs associated with this event URL to clean them all
    
    url_pattern = f"%{t_id}%"
    cursor.execute("SELECT id FROM tournament WHERE url LIKE ?", (url_pattern,))
    ids = [row[0] for row in cursor.fetchall()]
    ids.append(int(t_id)) # Ensure the verified ID is included
    
    for tid in set(ids):
        logger.info(f"Deleting Tournament ID {tid}")
        cursor.execute("DELETE FROM match WHERE tournament_id=?", (tid,))
        cursor.execute("DELETE FROM playerresult WHERE tournament_id=?", (tid,))
        cursor.execute("DELETE FROM tournament WHERE id=?", (tid,))
    
    logger.info("Cleaned.")

def save_to_db(cursor, tournament, players, matches):
    logger.info(f"Saving Tournament: {tournament.name} ({tournament.date})")
    
    # Tournament
    # Convert Enum objects to values if needed
    t_platform = tournament.platform
    t_format = tournament.format
    
    # If they are strings, great. If Enums, use .value
    if hasattr(t_platform, 'value'): t_platform = t_platform.value
    if hasattr(t_format, 'value'): t_format = t_format.value

    cursor.execute("""
        INSERT INTO tournament (id, name, date, player_count, url, platform, format)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tournament.id, tournament.name, tournament.date, tournament.player_count, tournament.url, t_platform, t_format))
    
    # Players
    # We need to map Player Name -> ID for Matches
    player_map = {} # Name -> DB ID
    
    for p in players:
        # Convert list dict to json string handling
        import json
        list_json_str = json.dumps(p.list_json) if p.list_json else "{}"
        
        cursor.execute("""
            INSERT INTO playerresult (tournament_id, player_name, rank, swiss_rank, swiss_wins, swiss_losses, swiss_draws, points_at_event, list_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tournament.id, p.player_name, p.rank, p.swiss_rank, p.swiss_wins, p.swiss_losses, p.swiss_draws, p.points_at_event, list_json_str))
        
        player_map[p.player_name] = cursor.lastrowid
        
    logger.info(f"Saved {len(players)} players.")
    
    # Matches
    saved_matches = 0
    for m in matches:
        p1_id = player_map.get(m.p1_name_temp, 0)
        p2_id = player_map.get(m.p2_name_temp, 0)
        winner_id = player_map.get(m.winner_name_temp, 0)
        
        # If BYE, p2_id is 0
        if m.is_bye:
             p2_id = 0 # No opponent
        
        cursor.execute("""
            INSERT INTO match (tournament_id, round_number, round_type, player1_id, player2_id, winner_id, player1_score, player2_score, is_bye)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tournament.id, m.round_number, m.round_type, p1_id, p2_id, winner_id, m.player1_score, m.player2_score, m.is_bye))
        saved_matches += 1
        
    logger.info(f"Saved {saved_matches} matches.")

def verify():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    t_id = "29336" # The Italian Job (Legacy)
    
    try:
        clean_event(cursor, t_id)
        
        scraper = LongshanksScraper(subdomain="xwing-legacy")
        logger.info(f"Scraping event {t_id}...")
        
        # Run scraping
        tournament = scraper.get_tournament_data(t_id)
        players = scraper.get_participants(t_id)
        matches = scraper.get_matches(t_id)
        
        # Save
        save_to_db(cursor, tournament, players, matches)
        conn.commit()
        
        # Validation
        logger.info("--- VALIDATION ---")
        
        # Check Enums
        cursor.execute("SELECT platform, format FROM tournament WHERE id=?", (t_id,))
        row = cursor.fetchone()
        logger.info(f"DB Platform: '{row[0]}' (Should be 'longshanks')")
        logger.info(f"DB Format: '{row[1]}' (Should be 'legacy')")
        
        # Check Matches
        cursor.execute("SELECT count(*) FROM match WHERE tournament_id=?", (t_id,))
        total_m = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM match WHERE tournament_id=? AND is_bye=1", (t_id,))
        bye_m = cursor.fetchone()[0]
        
        logger.info(f"Total Matches: {total_m}")
        logger.info(f"Total BYEs: {bye_m}")
        
        if total_m > 20 and bye_m < total_m / 2:
            logger.info("SUCCESS: Match extraction looks healthy.")
        else:
            logger.error("FAILURE: Suspicious match counts.")

    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    verify()
