"""
RollBetter API Client for M3taCron.

RollBetter has an undocumented JSON API:
- GET /tournaments/{id} - Tournament metadata + rounds list
- GET /tournaments/{id}/players - Rankings with full squad lists
- GET /tournaments/{id}/rounds/{n} - Match pairings for round N
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

BASE_URL = "https://api.rollbetter.gg"


async def fetch_tournament(tournament_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch tournament metadata from RollBetter.
    
    Args:
        tournament_id: RollBetter tournament ID.
    
    Returns:
        Tournament dict with 'name', 'rounds', etc. or None if not found.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/tournaments/{tournament_id}")
        if response.status_code == 404 or response.status_code == 500:
            return None
        response.raise_for_status()
        return response.json()


async def fetch_players(tournament_id: int) -> List[Dict[str, Any]]:
    """
    Fetch player rankings and squad lists.
    
    Args:
        tournament_id: RollBetter tournament ID.
    
    Returns:
        List of player dicts with 'rank', 'name', 'squad', etc.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/tournaments/{tournament_id}/players")
        if response.status_code != 200:
            return []
        data = response.json()
        # The /players endpoint returns a 'ladder' or direct list
        if isinstance(data, list):
            return data
        return data.get("players", data.get("ladder", []))


async def fetch_round_matches(tournament_id: int, round_number: int) -> List[Dict[str, Any]]:
    """
    Fetch match pairings for a specific round.
    
    Args:
        tournament_id: RollBetter tournament ID.
        round_number: Round number (1, 2, 3, etc.)
    
    Returns:
        List of match dicts with player pairings and scores.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/tournaments/{tournament_id}/rounds/{round_number}"
        )
        if response.status_code != 200:
            return []
        data = response.json()
        # Extract matches from response
        if isinstance(data, list):
            return data
        return data.get("matches", data.get("pairings", data.get("games", [])))


def extract_xws_from_player(player: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract XWS data from a RollBetter player record.
    
    RollBetter stores squad data in various formats.
    Returns None if no valid XWS is present.
    """
    # Try different possible field names
    squad = player.get("squad") or player.get("list") or player.get("xws")
    if not squad:
        return None
    
    # If it's already a dict with XWS structure
    if isinstance(squad, dict):
        if "faction" in squad or "pilots" in squad:
            return squad
    
    # If it's a string (JSON), try to parse it
    if isinstance(squad, str):
        import json
        try:
            parsed = json.loads(squad)
            if isinstance(parsed, dict) and ("faction" in parsed or "pilots" in parsed):
                return parsed
        except json.JSONDecodeError:
            pass
    
    return None


async def fetch_full_tournament(tournament_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch complete tournament data including players and all rounds.
    
    Args:
        tournament_id: RollBetter tournament ID.
    
    Returns:
        Dict with 'tournament', 'players', and 'rounds' keys.
    """
    tournament = await fetch_tournament(tournament_id)
    if not tournament:
        return None
    
    players = await fetch_players(tournament_id)
    
    # Get all rounds based on tournament metadata
    rounds_info = tournament.get("rounds", [])
    matches_by_round = {}
    
    for i, round_info in enumerate(rounds_info, start=1):
        matches = await fetch_round_matches(tournament_id, i)
        if matches:
            matches_by_round[i] = matches
    
    return {
        "tournament": tournament,
        "players": players,
        "rounds": matches_by_round,
    }


async def list_recent_tournaments(game: str = "Star Wars: X-Wing", limit: int = 20) -> List[Dict[str, Any]]:
    """
    List recent tournaments for a specific game.
    
    Note: This endpoint may require different parameters.
    """
    # RollBetter's tournament listing is typically done via the web UI
    # The API might not have a direct listing endpoint
    # This is a placeholder for potential future implementation
    return []
