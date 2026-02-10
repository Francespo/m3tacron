
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
from datetime import date
from sqlalchemy import JSON, Column, String

from .data_structures.formats import Format
from .data_structures.platforms import Platform
from .data_structures.scenarios import Scenario
from .data_structures.round_types import RoundType
from .data_structures.location import Location, LocationType

logger = logging.getLogger(__name__)


class Tournament(rx.Model, table=True):
    """
    Represents a competitive X-Wing event.
    """
    name: str
    date: date
    location: Location | None = Field(default=Location(city="Unknown", country="Unknown", continent="Unknown"), sa_column=Column(LocationType))
    player_count: int = Field(default=0)
    team_count: int = Field(default=0)
    url: str
    
    platform: Platform = Field(sa_column=Column(String))
    format: Format | None = Field(default=None, sa_column=Column(String))
    
    results: list["PlayerResult"] = Relationship(back_populates="tournament")


class PlayerResult(rx.Model, table=True):
    """
    A player's performance in a tournament.
    """
    tournament_id: int = Field(foreign_key="tournament.id")
    player_name: str = Field()
    team_name: str | None = Field(default=None)
    swiss_rank: int = Field(default=-1)
    swiss_wins: int = Field(default=-1)
    swiss_losses: int = Field(default=-1)
    swiss_draws: int = Field(default=0)
    swiss_event_points: int | None = Field(default=None)
    swiss_tie_breaker_points: int = Field(default=None)
    cut_rank: int | None = Field(default=None)
    cut_wins: int | None = Field(default=None)
    cut_losses: int | None = Field(default=None)
    cut_draws: int | None = Field(default=None)
    cut_event_points: int | None = Field(default=None)
    cut_tie_breaker_points: int | None = Field(default=None)
    list_json: dict = Field(default={}, sa_column=Column(JSON))
    
    tournament: Tournament | None = Relationship(back_populates="results")


class Match(rx.Model, table=True):
    """
    A single game between two players in a round.
    """
    id: int | None = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id")
    
    round_number: int
    round_type: RoundType = Field(default=RoundType.SWISS, sa_column=Column(String))
    scenario: Scenario | None = Field(default=None, sa_column=Column(String))
    
    player1_id: int | None = Field(default=None, foreign_key="playerresult.id")
    player2_id: int | None = Field(default=None, foreign_key="playerresult.id")
    
    player1_score: int = Field(default=-1)
    player2_score: int = Field(default=-1)
    
    winner_id: int | None = Field(default=None) # -1 if draw
    is_bye: bool = Field(default=False)
