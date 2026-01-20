import sys
import os
import json
import logging
from collections import Counter

# Add path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from m3tacron.backend.scrapers.longshanks import LongshanksScraper
from m3tacron.backend.models import Tournament, PlayerResult, Match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeepDebug")

def run():
    scraper = LongshanksScraper(subdomain="xwing")
    t_id = "30230"
    
    logger.info(f"Running FULL Scrape for {t_id}")
    try:
        tournament, players, matches = scraper.run_full_scrape(t_id, subdomain="xwing")
    except Exception as e:
        logger.error(f"Scrape crashed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n--- TOURNAMENT ---")
    print(f"Name: {tournament.name}")
    print(f"Format: {tournament.format} (Enum Value: {getattr(tournament.format, 'value', tournament.format)})")
    print(f"Platform: {tournament.platform}")
    
    print(f"\n--- PLAYERS ({len(players)}) ---")
    player_names = set()
    xws_count = 0
    
    # Dump first XWS to inspect
    if players and players[0].list_json:
        print("Sample XWS (First Player):")
        print(json.dumps(players[0].list_json, indent=2)[:500] + "...")
        with open("debug_xws_sample.json", "w") as f:
            json.dump(players[0].list_json, f, indent=2)
    
    for p in players:
        player_names.add(p.player_name)
        if p.list_json and p.list_json != {}:
            xws_count += 1
            
    print(f"Players with XWS: {xws_count}")
    
    print(f"\n--- MATCHES ({len(matches)}) ---")
    
    unmatched_p1 = 0
    unmatched_p2 = 0
    draws = 0
    
    print("Sample Matches:")
    for i, m in enumerate(matches[:15]):
        # Check matching
        p1_found = m.p1_name_temp in player_names
        p2_found = m.p2_name_temp in player_names or m.p2_name_temp == "BYE"
        
        status = "OK"
        if not p1_found: status = f"P1 MISSING ({m.p1_name_temp})"
        if not p2_found: status = f"P2 MISSING ({m.p2_name_temp})"
        if not p1_found and not p2_found: status = "BOTH MISSING"
        
        print(f"[{i}] R{m.round_number} '{m.p1_name_temp}' vs '{m.p2_name_temp}' ({m.player1_score}-{m.player2_score}) -> Winner: {m.winner_name_temp} | Status: {status}")
        
        if not p1_found: unmatched_p1 += 1
        if not p2_found: unmatched_p2 += 1
        if m.winner_name_temp is None: draws += 1
            
    print(f"\nUnmatched P1 Names: {unmatched_p1}")
    print(f"Unmatched P2 Names: {unmatched_p2}")
    print(f"Draws (None Winner): {draws}")
    
    if unmatched_p1 > 0:
        print("\nName Analysis (First 5 Mismatches):")
        count = 0
        for m in matches:
            if m.p1_name_temp not in player_names and count < 5:
                print(f"Match Name: '{m.p1_name_temp}' (Len: {len(m.p1_name_temp)})")
                print("  vs Player Names:")
                for pn in list(player_names)[:5]:
                    print(f"  - '{pn}' (Len: {len(pn)})")
                count += 1

if __name__ == "__main__":
    run()
