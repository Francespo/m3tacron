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
        print(f"   [OK] Tournament: {tournament.get('name', 'Unknown')}")
        print(f"   [OK] Rounds: {len(tournament.get('rounds', []))}")
    else:
        print("   [FAIL] Failed to fetch tournament")
        return
    
    # Test 2: Fetch players
    print("\n2. Fetching players...")
    players = await fetch_players(tournament_id)
    print(f"   [OK] Found {len(players)} players")
    
    if players:
        # Show first player
        first = players[0] if isinstance(players, list) else list(players.values())[0]
        print(f"   [DEBUG] Player Keys: {list(first.keys())}")
        player_info = first.get("player", {})
        name = player_info.get("name") or player_info.get("username") or first.get("name") or "Unknown"
        print(f"   [OK] First player: {name}")
        
        # Test XWS extraction
        xws = extract_xws_from_player(first)
        if xws:
            print(f"   [OK] XWS found: faction={xws.get('faction', 'Unknown')}")
        else:
            print("   [WARN] No XWS data in player record")
    
    # Test 3: Fetch round matches
    print("\n3. Fetching Round 1 matches...")
    matches = await fetch_round_matches(tournament_id, 1)
    print(f"   [OK] Found {len(matches)} matches in Round 1")
    
    print("\n" + "=" * 50)
    print("RollBetter scraper test PASSED!")


if __name__ == "__main__":
    asyncio.run(test_rollbetter())
