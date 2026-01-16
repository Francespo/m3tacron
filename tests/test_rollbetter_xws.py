"""Test Rollbetter XWS with specific tournament ID."""
import asyncio
import json
import sys
sys.path.insert(0, '.')

from m3tacron.backend.scrapers import rollbetter


async def main():
    tid = 2474  # Windy City tournament with XWA lists
    
    print(f"Testing Rollbetter tournament {tid}...")
    
    tournament = await rollbetter.fetch_tournament(tid)
    if not tournament:
        print("[FAIL] Tournament not found")
        return
    
    print(f"Tournament: {tournament.get('name', tournament.get('title'))}")
    
    players = await rollbetter.fetch_players(tid)
    print(f"Players found: {len(players)}")
    
    # Check XWS for first few players
    xws_count = 0
    results = []
    
    for p in players[:10]:
        xws = rollbetter.extract_xws_from_player(p)
        if xws:
            xws_count += 1
            results.append({
                "name": p.get("name", "Unknown"),
                "faction": xws.get("faction"),
                "pilots": len(xws.get("pilots", [])),
                "xws_keys": list(xws.keys())
            })
            
            if xws_count == 1:  # Show detailed first XWS
                print(f"\nFirst XWS found:")
                print(f"  Player: {p.get('name')}")
                print(f"  Faction: {xws.get('faction')}")
                print(f"  Pilots: {len(xws.get('pilots', []))}")
                if xws.get('pilots'):
                    pilot = xws['pilots'][0]
                    print(f"  First pilot: {pilot.get('id')} on {pilot.get('ship')}")
                    print(f"  Upgrades: {list(pilot.get('upgrades', {}).keys())}")
    
    print(f"\n{xws_count}/{min(10, len(players))} players have XWS")
    
    if xws_count > 0:
        print("\n[OK] Rollbetter returns COMPLETE XWS!")
        
        # Save full XWS for one player
        for p in players:
            xws = rollbetter.extract_xws_from_player(p)
            if xws:
                with open("rollbetter_xws_sample.json", "w", encoding="utf-8") as f:
                    json.dump({"player": p.get("name"), "xws": xws}, f, indent=2, ensure_ascii=False)
                print("Sample saved to rollbetter_xws_sample.json")
                break
    else:
        print("\n[WARN] No XWS found - checking raw player data...")
        if players:
            print(f"First player keys: {list(players[0].keys())}")


if __name__ == "__main__":
    asyncio.run(main())
