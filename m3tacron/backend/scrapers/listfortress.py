"""
ListFortress API Client for M3taCron.

ListFortress has a public JSON API:
- GET /api/v1/tournaments/ - List all tournaments
- GET /api/v1/tournaments/{id} - Get single tournament with participants
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

BASE_URL = "https://listfortress.com/api/v1"


async def fetch_tournaments(
    limit: int = 100,
    since_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch a list of tournaments from ListFortress.
    
    Args:
        limit: Maximum number of tournaments to return.
        since_date: Optional ISO date string (YYYY-MM-DD). Only returns
                    tournaments on or after this date.
    
    Returns:
        List of tournament dictionaries.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/tournaments/")
        response.raise_for_status()
        tournaments = response.json()
    
    # Filter by date if provided
    if since_date:
        cutoff = datetime.fromisoformat(since_date)
        tournaments = [
            t for t in tournaments
            if datetime.fromisoformat(t.get("date", "1900-01-01")) >= cutoff
        ]
    
    # Sort by date descending and limit
    tournaments.sort(key=lambda t: t.get("date", ""), reverse=True)
    return tournaments[:limit]


async def fetch_tournament_details(tournament_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch full details for a single tournament, including participants.
    
    Args:
        tournament_id: The ListFortress tournament ID.
    
    Returns:
        Tournament dictionary with 'participants' list, or None if not found.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/tournaments/{tournament_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()


def extract_xws_from_participant(participant: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extracts and standardizes the XWS squad data from a raw ListFortress record.
    
    It handles ListFortress's specific data storage quirks, such as JSON stored as
    serialized strings instead of native objects.
    """
    # ListFortress stores XWS in 'list_json', but the type varies by endpoint/age
    squad_json = participant.get("list_json")
    if not squad_json:
        return None
    
    # Handle serialized JSON strings
    # The API often returns the XWS blob as a string which needs manual parsing
    if isinstance(squad_json, str):
        import json
        try:
            squad_json = json.loads(squad_json)
        except json.JSONDecodeError:
            # If parsing fails, the data is corrupt or not XWS, so we discard it
            return None

    # Validate the structure is a dictionary before access
    if not isinstance(squad_json, dict):
        return None
        
    # Heuristic check for XWS validity
    # We require standard fields like 'faction' or 'pilots' to confirm it's a valid list
    # 'vendor' and 'points' are accepted as weak signals for older/partial data
    if "faction" not in squad_json and "pilots" not in squad_json:
         if "vendor" not in squad_json and "points" not in squad_json:
             return None
    
    return squad_json


def calculate_list_points(xws: Dict[str, Any]) -> int:
    """
    Calculate the total points of an XWS list.
    
    Note: This is a simplified calculation. In production, we'd need
    to look up points from a card database.
    """
    total = 0
    for pilot in xws.get("pilots", []):
        total += pilot.get("points", 0)
    return total
