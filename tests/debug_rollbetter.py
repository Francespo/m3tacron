"""Debug Rollbetter player data structure."""
import asyncio
import json
import sys
sys.path.insert(0, '.')

from m3tacron.backend.scrapers import rollbetter


async def main():
    tid = 2474
    
    players = await rollbetter.fetch_players(tid)
    print(f"Players found: {len(players)}")
    
    if players:
        # Save raw player data
        with open("rollbetter_raw_player.json", "w", encoding="utf-8") as f:
            json.dump(players[0], f, indent=2, ensure_ascii=False)
        print("First player raw data saved to rollbetter_raw_player.json")
        
        # Check for lists field
        p = players[0]
        print(f"\nPlayer keys: {list(p.keys())}")
        
        if "lists" in p:
            print(f"Lists count: {len(p['lists'])}")
            if p['lists']:
                print(f"First list keys: {list(p['lists'][0].keys())}")
                with open("rollbetter_first_list.json", "w", encoding="utf-8") as f:
                    json.dump(p['lists'][0], f, indent=2, ensure_ascii=False)
                print("First list saved to rollbetter_first_list.json")


if __name__ == "__main__":
    asyncio.run(main())
