import reflex as rx
from sqlmodel import Field, Relationship
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import JSON, Column

class Tournament(rx.Model, table=True):
    """Model for X-Wing Tournaments."""
    name: str
    date: datetime
    platform: str  # 'RollBetter', 'Longshanks', 'ListFortress', 'Manual'
    format: str    # Display format (e.g. "2.5 XWA", "2.0 X2PO")
    url: str       # Source URL
    
    # Hierarchical format categorization
    macro_format: str = "Other"  # "2.0", "2.5", "Other"
    sub_format: str = "Unknown"  # "FFG", "X2PO", "XLC", "AMG", "XWA", "Epic", etc.
    
    # Relationships
    results: List["PlayerResult"] = Relationship(back_populates="tournament")

class PlayerResult(rx.Model, table=True):
    """Model for a player's result in a tournament."""
    tournament_id: int = Field(foreign_key="tournament.id")
    player_name: str
    rank: int
    swiss_rank: Optional[int] = None
    
    # Storing the full XWS list as JSON
    list_json: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Historic points at the time of the event
    points_at_event: int = 0
    
    tournament: Optional[Tournament] = Relationship(back_populates="results")

    class Config:
        # Allow arbitrary types for JSON field handling
        arbitrary_types_allowed = True

class ManualSubmission(rx.Model, table=True):
    """Model for manually submitted lists pending approval."""
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED
    xws_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    submitter_ip: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional metadata
    player_name: str
    tournament_name: Optional[str] = None
    date: Optional[datetime] = None


class Match(rx.Model, table=True):
    """
    Represents a single game round between two players.
    
    Tracks scores and the winner. Handles BYEs by checking is_bye flag.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id")
    
    # Round context
    # Used to group matches in the UI
    round_number: int
    round_type: str = Field(default="swiss") # 'swiss' or 'elimination'
    
    # Player references
    # We map back to PlayerResult IDs to link to player details
    player1_id: int = Field(foreign_key="playerresult.id")
    player2_id: Optional[int] = Field(default=None, foreign_key="playerresult.id")
    
    player1_score: int = Field(default=0)
    player2_score: int = Field(default=0)
    
    # Winner ID
    # Explicitly stored to avoid re-calculating from scores (draws, concessions)
    winner_id: Optional[int] = Field(default=None)
    
    # BYE flag
    # Functionally, a BYE is a match against no one with a fixed win score
    is_bye: bool = Field(default=False)
```
