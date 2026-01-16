import importlib.util
import sys
import os
import asyncio
import json

# Put m3tacron in path for internal imports
sys.path.insert(0, os.path.abspath('.'))

# Load rollbetter module directly by path to bypass package issues
file_path = os.path.abspath("m3tacron/backend/scrapers/rollbetter.py")
spec = importlib.util.spec_from_file_location("m3tacron.backend.scrapers.rollbetter", file_path)
rollbetter = importlib.util.module_from_spec(spec)
sys.modules["m3tacron.backend.scrapers.rollbetter"] = rollbetter
spec.loader.exec_module(rollbetter)

async def main():
    tid = 2474
    print(f"Testing Rollbetter scraper implementation for tournament {tid}...")
    
    try:
        data = await rollbetter.scrape_tournament(tid)
        
        if not data:
            print("No data returned.")
            return

        tournament = data.get("tournament", {})
        players = data.get("players", [])
        
        print(f"\nTournament: {tournament.get('name')}")
        print(f"Platform: {tournament.get('platform')}")
        print(f"Players found with XWS: {len(players)}")
        
        if players:
            print("\nSample XWS from first player:")
            p = players[0]
            xws = p.get("xws", {})
            print(f"Name: {p.get('name')}")
            print(f"Faction: {xws.get('faction')}")
            print(f"Points: {xws.get('points')}")
            print(f"Pilots: {len(xws.get('pilots', []))}")
            
            # Save dump for verification
            with open("rollbetter_playwright_test.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("\nFull dump saved to rollbetter_playwright_test.json")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
