"""
M3taCron Backend API Routes.

These are FastAPI-style routes that will be exposed via Reflex's backend API.
"""
import os
from datetime import datetime

import reflex as rx

from .scrapers.listfortress import fetch_tournaments, fetch_tournament_details, extract_xws_from_participant
from .models import Tournament, PlayerResult, ManualSubmission
from .database import get_session


# Simple API key auth
API_KEY = os.environ.get("API_KEY", "dev-key-change-me")


def verify_api_key(authorization: str) -> bool:
    """Check if the provided authorization header matches the API key."""
    if not authorization:
        return False
    if not authorization.startswith("Bearer "):
        return False
    token = authorization[7:]
    return token == API_KEY


class UpdateResponse(rx.Base):
    success: bool
    message: str
    tournaments_processed: int = 0
    players_imported: int = 0


async def trigger_update(days_back: int = 30) -> UpdateResponse:
    """
    Sync recent tournaments from ListFortress.
    
    Args:
        days_back: Number of days to look back for tournaments.
    
    Returns:
        UpdateResponse with sync results.
    """
    from datetime import timedelta
    
    cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    try:
        tournaments = await fetch_tournaments(limit=50, since_date=cutoff_date)
    except Exception as e:
        return UpdateResponse(success=False, message=f"Failed to fetch tournaments: {e}")
    
    tournaments_processed = 0
    players_imported = 0
    
    for t_data in tournaments:
        # Skip if already in database by URL
        # (In production, check with database query)
        
        # Fetch full details 
        t_id = t_data.get("id")
        if not t_id:
            continue
            
        try:
            details = await fetch_tournament_details(t_id)
        except Exception:
            continue
        
        if not details:
            continue
        
        # Create Tournament record
        tournament = Tournament(
            name=details.get("name", "Unknown"),
            date=datetime.fromisoformat(details.get("date", "2000-01-01")),
            platform="ListFortress",
            format=details.get("format", {}).get("name", "Unknown"),
            url=f"https://listfortress.com/tournaments/{t_id}",
        )
        
        # Process participants
        participants = details.get("participants", [])
        for p in participants:
            xws = extract_xws_from_participant(p)
            if not xws:
                # Skip players without valid XWS
                continue
            
            result = PlayerResult(
                tournament_id=0,  # Will be set after tournament insert
                player_name=p.get("name", "Unknown"),
                rank=p.get("rank", 0),
                swiss_rank=p.get("swiss_rank"),
                list_json=xws,
                points_at_event=p.get("points", 200),  # Default to 200 if not specified
            )
            players_imported += 1
        
        tournaments_processed += 1
    
    return UpdateResponse(
        success=True,
        message=f"Sync completed",
        tournaments_processed=tournaments_processed,
        players_imported=players_imported,
    )


class SubmissionRequest(rx.Base):
    player_name: str
    xws_data: dict
    tournament_name: str | None = None
    date: str | None = None


class SubmissionResponse(rx.Base):
    success: bool
    message: str
    submission_id: int | None = None


async def submit_list(data: SubmissionRequest, submitter_ip: str) -> SubmissionResponse:
    """
    Submit a list manually to the approval queue.
    
    Args:
        data: The submission payload.
        submitter_ip: IP address of submitter (for rate limiting).
    
    Returns:
        SubmissionResponse indicating success.
    """
    # Validate XWS
    xws = data.xws_data
    if not isinstance(xws, dict):
        return SubmissionResponse(success=False, message="Invalid XWS format")
    if "faction" not in xws or "pilots" not in xws:
        return SubmissionResponse(success=False, message="XWS must have 'faction' and 'pilots' fields")
    
    # Create submission
    submission = ManualSubmission(
        status="PENDING",
        xws_data=xws,
        submitter_ip=submitter_ip,
        player_name=data.player_name,
        tournament_name=data.tournament_name,
        date=datetime.fromisoformat(data.date) if data.date else None,
    )
    
    # In production: save to database
    # For now, just return success
    return SubmissionResponse(
        success=True,
        message="Submission received and pending approval",
        submission_id=1,  # Placeholder
    )
