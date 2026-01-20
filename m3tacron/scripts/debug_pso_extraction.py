import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from m3tacron.backend.scrapers.longshanks import LongshanksScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugPSO")

def run_debug():
    tid = "30230"
    sub = "xwing"
    
    print(f"Scraping {tid}...")
    scraper = LongshanksScraper(subdomain=sub)
    try:
        matches = scraper.get_matches(tid)
        
        print(f"Total Matches: {len(matches)}")
        
        round_counts = {}
        for m in matches:
            r = m.round_number
            round_counts[r] = round_counts.get(r, 0) + 1
            
        print("Matches per round:")
        for r in sorted(round_counts.keys()):
            print(f"Round {r}: {round_counts[r]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_debug()
