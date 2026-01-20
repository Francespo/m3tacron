import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from m3tacron.backend.scrapers.longshanks import LongshanksScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugGrandpa")

def run_debug():
    tid = "26633" # Grandpa's Cup
    sub = "xwing-legacy"
    
    print(f"Scraping Squad Event {tid}...")
    scraper = LongshanksScraper(subdomain=sub)
    try:
        matches = scraper.get_matches(tid)
        
        print(f"Total Individual Matches: {len(matches)}")
        
        if len(matches) > 0:
            print("Sample Matches:")
            for m in matches[:5]:
                print(f"R{m.round_number}: P1_ID:{m.player1_id} vs P2_ID:{m.player2_id} ({m.player1_score}-{m.player2_score})")
                
            # Verify we have IDs
            ids_count = sum(1 for m in matches if m.player1_id or m.player2_id > 0)
            print(f"Matches with at least one ID: {ids_count}/{len(matches)}")
            
            round_counts = {}
            for m in matches:
                round_counts[m.round_number] = round_counts.get(m.round_number, 0) + 1
            print("Matches per Round:", round_counts)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_debug()
