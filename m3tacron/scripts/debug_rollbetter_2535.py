
import logging
import sys
import os

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from m3tacron.backend.scrapers.rollbetter import RollbetterScraper
from m3tacron.backend.enums.formats import infer_format_from_xws

def debug_2535():
    logging.basicConfig(level=logging.INFO)
    scraper = RollbetterScraper()
    print("Fetching participants for tournament 2535...")
    players = scraper.get_participants("2535")
    
    print(f"Found {len(players)} players.")
    
    count = 0
    for p in players:
        if p.list_json:
            count += 1
            print(f"--- Player: {p.player_name} ---")
            # print(f"XWS: {p.list_json}")
            fmt = infer_format_from_xws(p.list_json)
            print(f"Inferred Format: {fmt}")
            
            # Print specific fields relevant to inference
            print(f"Format field: {p.list_json.get('format')}")
            print(f"Ruleset field: {p.list_json.get('ruleset')}")
            vendor = p.list_json.get('vendor', {})
            print(f"Vendor: {vendor}")
            
            if count >= 20:
                break

if __name__ == "__main__":
    debug_2535()
