"""
ListFortress API Client.

Provides functions to fetch tournament data and extract XWS lists.
API Endpoints:
- GET /api/v1/tournaments/ - List all tournaments
- GET /api/v1/tournaments/{id} - Get tournament with participants
"""
import httpx
import json
from datetime import datetime

BASE_URL = "https://listfortress.com/api/v1"


async def fetch_tournaments(
    limit: int = 100,
    since_date: str | None = None,
) -> list[dict]:
    """
    Fetches tournament metadata from ListFortress.
    
    Optionally filters by date and limits results.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/tournaments/")
        response.raise_for_status()
        tournaments = response.json()
    
    if since_date:
        cutoff = datetime.fromisoformat(since_date)
        tournaments = [
            t for t in tournaments
            if datetime.fromisoformat(t.get("date", "1900-01-01")) >= cutoff
        ]
    
    tournaments.sort(key=lambda t: t.get("date", ""), reverse=True)
    return tournaments[:limit]


async def fetch_tournament_details(tournament_id: int) -> dict | None:
    """
    Fetches full tournament details including participant list.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/tournaments/{tournament_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()


def extract_xws_from_participant(participant: dict) -> dict | None:
    """
    Extracts and validates XWS data from a participant record.
    
    Handles both parsed dicts and serialized JSON strings.
    """
    squad_json = participant.get("list_json")
    if not squad_json:
        return None
    
    # Parse if stored as string
    if isinstance(squad_json, str):
        try:
            squad_json = json.loads(squad_json)
        except json.JSONDecodeError:
            return None

    if not isinstance(squad_json, dict):
        return None
    
    # Validate minimal XWS structure
    if "faction" not in squad_json and "pilots" not in squad_json:
        if "vendor" not in squad_json and "points" not in squad_json:
            return None
    
    return squad_json


def calculate_list_points(xws: dict) -> int:
    """Sums pilot points from an XWS list."""
    total = 0
    for pilot in xws.get("pilots", []):
        total += pilot.get("points", 0)
    return total
