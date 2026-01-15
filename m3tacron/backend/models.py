"""
Database models for the M3taCron platform.

Defines the core entities: Tournament, PlayerResult, Match, and ManualSubmission.
Uses Enums for standardized values like Factions and Formats.
"""
import reflex as rx
from sqlmodel import Field, Relationship
from datetime import datetime
from sqlalchemy import JSON, Column
from enum import Enum


class Faction(str, Enum):
    """X-Wing faction identifiers matching XWS standard."""
    REBEL = "rebelalliance"
    EMPIRE = "galacticempire"
    SCUM = "scumandvillainy"
    RESISTANCE = "resistance"
    FIRST_ORDER = "firstorder"
    REPUBLIC = "galacticrepublic"
    SEPARATIST = "separatistalliance"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_xws(cls, value: str) -> "Faction":
        """Converts raw XWS faction string to Enum."""
        normalized = value.lower().replace(" ", "").replace("-", "")
        for faction in cls:
            if faction.value == normalized:
                return faction
        return cls.UNKNOWN


class MacroFormat(str, Enum):
    """Top-level game version categories."""
    V2_0 = "2.0"
    V2_5 = "2.5"
    OTHER = "Other"


class SubFormat(str, Enum):
    """Specific rulesets within each macro format."""
    FFG = "FFG"
    X2PO = "X2PO"
    XLC = "XLC"
    AMG = "AMG"
    XWA = "XWA"
    EPIC = "Epic"
    CUSTOM = "Custom"
    UNKNOWN = "Unknown"


class Tournament(rx.Model, table=True):
    """Represents a competitive X-Wing event."""
    name: str
    date: datetime
    platform: str
    format: str
    url: str
    
    macro_format: str = MacroFormat.OTHER.value
    sub_format: str = SubFormat.UNKNOWN.value
    
    results: list["PlayerResult"] = Relationship(back_populates="tournament")


class PlayerResult(rx.Model, table=True):
    """A player's performance in a tournament."""
    tournament_id: int = Field(foreign_key="tournament.id")
    player_name: str
    rank: int
    swiss_rank: int | None = None
    
    list_json: dict = Field(default={}, sa_column=Column(JSON))
    points_at_event: int = 0
    
    tournament: Tournament | None = Relationship(back_populates="results")

    class Config:
        arbitrary_types_allowed = True


class ManualSubmission(rx.Model, table=True):
    """User-submitted lists pending admin review."""
    status: str = "PENDING"
    xws_data: dict = Field(default={}, sa_column=Column(JSON))
    submitter_ip: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    player_name: str
    tournament_name: str | None = None
    date: datetime | None = None


class Match(rx.Model, table=True):
    """A single game between two players in a round."""
    id: int | None = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id")
    
    round_number: int
    round_type: str = Field(default="swiss")
    
    player1_id: int = Field(foreign_key="playerresult.id")
    player2_id: int | None = Field(default=None, foreign_key="playerresult.id")
    
    player1_score: int = Field(default=0)
    player2_score: int = Field(default=0)
    
    winner_id: int | None = Field(default=None)
    is_bye: bool = Field(default=False)
