"""Test script for RollBetter scraper."""
import asyncio
import sys
sys.path.insert(0, '.')

from m3tacron.backend.scrapers.rollbetter import (
    fetch_tournament,
    fetch_players,
    fetch_round_matches,
    extract_xws_from_player,
)


async def test_rollbetter():
    # Test with a known valid tournament ID
    tournament_id = 2474  # Known X-Wing tournament
    
    print(f"Testing RollBetter API with tournament ID: {tournament_id}")
    print("=" * 50)
    
    # Test 1: Fetch tournament metadata
    print("\n1. Fetching tournament metadata...")
    tournament = await fetch_tournament(tournament_id)
    if tournament:
        print(f"   ✓ Tournament: {tournament.get('name', 'Unknown')}")
        print(f"   ✓ Rounds: {len(tournament.get('rounds', []))}")
    else:
        print("   ✗ Failed to fetch tournament")
        return
    
    # Test 2: Fetch players
    print("\n2. Fetching players...")
    players = await fetch_players(tournament_id)
    print(f"   ✓ Found {len(players)} players")
    
    if players:
        # Show first player
        first = players[0] if isinstance(players, list) else list(players.values())[0]
        print(f"   ✓ First player: {first.get('name', first.get('displayName', 'Unknown'))}")
        
        # Test XWS extraction
        xws = extract_xws_from_player(first)
        if xws:
            print(f"   ✓ XWS found: faction={xws.get('faction', 'Unknown')}")
        else:
            print("   ⚠ No XWS data in player record")
    
    # Test 3: Fetch round matches
    print("\n3. Fetching Round 1 matches...")
    matches = await fetch_round_matches(tournament_id, 1)
    print(f"   ✓ Found {len(matches)} matches in Round 1")
    
    print("\n" + "=" * 50)
    print("RollBetter scraper test PASSED! ✓")


if __name__ == "__main__":
    asyncio.run(test_rollbetter())
