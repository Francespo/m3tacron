
"""
Database models and format utilities for the M3taCron platform.

Defines:
- Core entities: Tournament, PlayerResult, Match
- Format enums and helper functions
- Duplicate detection and format inference utilities
"""
import logging
import reflex as rx
from sqlmodel import Field, Relationship
from datetime import datetime, date
from sqlalchemy import JSON, Column, String

from .data_structures.formats import Format
from .data_structures.platforms import Platform
from .data_structures.scenarios import Scenario
from .data_structures.round_types import RoundType

logger = logging.getLogger(__name__)


class Tournament(rx.Model, table=True):
    """
    Represents a competitive X-Wing event.
    """
    name: str
    date: date
    city: str | None = Field(default=None)
    state: str | None = Field(default=None)
    player_count: int = Field(default=0)
    url: str
    
    platform: Platform = Field(sa_column=Column(String))
    format: Format | None = Field(default=None, sa_column=Column(String))
    
    results: list["PlayerResult"] = Relationship(back_populates="tournament")
    
    @property
    def macro_format(self) -> str:
        """Infer macro format from the specific format."""
        return (self.format or Format.OTHER).macro.value


class PlayerResult(rx.Model, table=True):
    """
    A player's performance in a tournament.
    """
    tournament_id: int = Field(foreign_key="tournament.id")
    player_name: str
    rank: int
    swiss_rank: int | None = None
    
    # Detailed Results
    swiss_wins: int = Field(default=0)
    swiss_losses: int = Field(default=0)
    swiss_draws: int = Field(default=0)
    cut_wins: int = Field(default=0)
    cut_losses: int = Field(default=0)
    
    list_json: dict = Field(default={}, sa_column=Column(JSON))
    points_at_event: int = 0
    
    tournament: Tournament | None = Relationship(back_populates="results")

    class Config:
        arbitrary_types_allowed = True


class Match(rx.Model, table=True):
    """
    A single game between two players in a round.
    """
    id: int | None = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id")
    
    round_number: int
    round_type: RoundType = Field(default=RoundType.SWISS, sa_column=Column(String))
    scenario: Scenario | None = Field(default=None, sa_column=Column(String))
    
    player1_id: int = Field(foreign_key="playerresult.id")
    player2_id: int | None = Field(default=None, foreign_key="playerresult.id")
    
    player1_score: int = Field(default=0)
    player2_score: int = Field(default=0)
    
    winner_id: int | None = Field(default=None)
    first_player_id: int | None = Field(default=None)
    is_bye: bool = Field(default=False)

