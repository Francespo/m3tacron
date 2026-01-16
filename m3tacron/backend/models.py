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


class GameFormat(str, Enum):
    """X-Wing game format/ruleset identifiers."""
    # 2.5
    XWA = "XWA"
    AMG = "AMG"
    # 2.0
    FFG = "FFG"
    LEGACY_X2PO = "Legacy (X2PO)"
    LEGACY_XLC = "Legacy (XLC)"
    WILDSPACE = "Wildspace"
    # Other
    OTHER = "Other"


class MacroFormat(str, Enum):
    """High-level format categories."""
    V2_5 = "2.5"
    V2_0 = "2.0"
    OTHER = "Other"


class SubFormat(str, Enum):
    """Sub-format categories for detailed filtering."""
    # 2.5 sub-formats
    AMG = "AMG"
    XWA = "XWA"
    # 2.0 sub-formats
    X2PO = "Legacy (X2PO)"
    XLC = "Legacy (XLC)"
    WILDSPACE = "Wildspace"
    # Other
    UNKNOWN = "Unknown"


def get_macro_format(fmt: str) -> str:
    """Infer macro format category from a specific format."""
    fmt_lower = fmt.lower()
    if any(x in fmt_lower for x in ["xwa", "amg", "2.5"]):
        return MacroFormat.V2_5.value
    elif any(x in fmt_lower for x in ["legacy (x2po)", "legacy (xlc)", "wildspace", "2.0", "ffg"]):
        return MacroFormat.V2_0.value
    return MacroFormat.OTHER.value


def get_sub_format(fmt: str) -> str:
    """Extract sub-format from format string."""
    fmt_lower = fmt.lower()
    if "x2po" in fmt_lower:
        return SubFormat.X2PO.value
    elif "xlc" in fmt_lower:
        return SubFormat.XLC.value
    elif "wildspace" in fmt_lower:
        return SubFormat.WILDSPACE.value
    elif "xwa" in fmt_lower:
        return SubFormat.XWA.value
    elif "amg" in fmt_lower:
        return SubFormat.AMG.value
    return SubFormat.UNKNOWN.value


class Tournament(rx.Model, table=True):
    """Represents a competitive X-Wing event."""
    name: str
    date: datetime
    platform: str
    format: str = GameFormat.OTHER.value
    player_count: int = Field(default=0)
    url: str
    
    results: list["PlayerResult"] = Relationship(back_populates="tournament")
    
    @property
    def macro_format(self) -> str:
        """Infer macro format from the specific format."""
        return get_macro_format(self.format)
    
    @property
    def sub_format(self) -> str:
        """Return the specific format as sub-format."""
        return self.format


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
