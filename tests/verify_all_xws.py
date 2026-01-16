"""Verify XWS extraction from all scrapers - save to file."""
import asyncio
import json
import sys
sys.path.insert(0, '.')

from m3tacron.backend.scrapers import listfortress, rollbetter


async def test_listfortress(output):
    output.append("=" * 60)
    output.append("LISTFORTRESS XWS TEST")
    output.append("=" * 60)
    
    # Get a recent tournament
    tournaments = await listfortress.fetch_tournaments(limit=5)
    if not tournaments:
        output.append("[FAIL] No tournaments found")
        return
    
    output.append(f"Found {len(tournaments)} tournaments")
    
    # Get first tournament with details
    for t in tournaments:
        tid = t.get("id")
        details = await listfortress.fetch_tournament_details(tid)
        if not details:
            continue
        
        participants = details.get("participants", [])
        output.append(f"\nTournament: {details.get('name')}")
        output.append(f"Participants: {len(participants)}")
        
        # Find first participant with XWS
        for p in participants[:10]:
            xws = listfortress.extract_xws_from_participant(p)
            if xws:
                output.append(f"\nPlayer: {p.get('name', p.get('player_name', 'Unknown'))}")
                output.append(f"XWS Keys: {list(xws.keys())}")
                output.append(f"Faction: {xws.get('faction')}")
                output.append(f"Pilots: {len(xws.get('pilots', []))}")
                if xws.get('pilots'):
                    pilot = xws['pilots'][0]
                    output.append(f"First pilot: {pilot.get('id')} on {pilot.get('ship')}")
                    output.append(f"Upgrades: {list(pilot.get('upgrades', {}).keys())}")
                output.append("\n[OK] ListFortress returns COMPLETE XWS!")
                return
        
        output.append("No XWS found in first 10 participants")
        return


async def test_rollbetter(output):
    output.append("\n" + "=" * 60)
    output.append("ROLLBETTER XWS TEST")
    output.append("=" * 60)
    
    # Try known tournament IDs
    test_ids = [12345, 10000, 8000, 5000, 3000]
    
    for tid in test_ids:
        tournament = await rollbetter.fetch_tournament(tid)
        if not tournament:
            continue
        
        output.append(f"\nTournament ID: {tid}")
        output.append(f"Name: {tournament.get('name', tournament.get('title'))}")
        
        players = await rollbetter.fetch_players(tid)
        output.append(f"Players: {len(players)}")
        
        for p in players[:10]:
            xws = rollbetter.extract_xws_from_player(p)
            if xws:
                output.append(f"\nPlayer: {p.get('name', 'Unknown')}")
                output.append(f"XWS Keys: {list(xws.keys())}")
                output.append(f"Faction: {xws.get('faction')}")
                output.append(f"Pilots: {len(xws.get('pilots', []))}")
                if xws.get('pilots'):
                    pilot = xws['pilots'][0]
                    output.append(f"First pilot: {pilot.get('id')} on {pilot.get('ship')}")
                output.append("\n[OK] Rollbetter returns COMPLETE XWS!")
                return
        
        output.append("No XWS found in players for this tournament")
    
    output.append("[WARN] No Rollbetter tournament with XWS found")


async def main():
    output = []
    await test_listfortress(output)
    await test_rollbetter(output)
    output.append("\n" + "=" * 60)
    output.append("VERIFICATION COMPLETE")
    output.append("=" * 60)
    
    # Save to file
    with open("xws_verification_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    
    print("Results saved to xws_verification_results.txt")


if __name__ == "__main__":
    asyncio.run(main())
