
"""
Database models and format utilities for the M3taCron platform.

Defines:
- Core entities: Tournament, PlayerStanding, TeamStanding, Match, TeamMatch
- Format enums and helper functions
- Duplicate detection and format inference utilities
"""
import logging
from sqlmodel import Field, Relationship, SQLModel
from datetime import date, datetime
from sqlalchemy import JSON, Column, Computed, String
from sqlalchemy.dialects.postgresql import JSONB

from .data_structures.formats import Format
from .data_structures.source import Source
from .data_structures.scenarios import Scenario
from .data_structures.round_types import RoundType
from .data_structures.location import Location, LocationType

logger = logging.getLogger(__name__)


class Tournament(SQLModel, table=True):
    """
    Represents a competitive X-Wing event.
    """
    id: int | None = Field(default=None, primary_key=True)
    name: str
    date: date
    location: Location | None = Field(default=Location(
        city="Unknown", country="Unknown", continent="Unknown"), sa_column=Column(LocationType))
    player_count: int = Field(default=0)
    team_count: int = Field(default=0)
    url: str

    source: Source = Field(sa_column=Column(String))
    format: Format | None = Field(default=None, sa_column=Column(String))

    standings: list["PlayerStanding"] = Relationship(
        back_populates="tournament")
    team_standings: list["TeamStanding"] = Relationship(
        back_populates="tournament")


class TeamStanding(SQLModel, table=True):
    """
    A team's performance in a tournament.
    """
    id: int | None = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id")
    team_name: str = Field()
    swiss_rank: int = Field(default=0)
    swiss_wins: int = Field(default=0)
    swiss_losses: int = Field(default=0)
    swiss_draws: int = Field(default=0)
    swiss_event_points: int | None = Field(default=None)
    swiss_tie_breaker_points: int | None = Field(default=None)
    cut_rank: int | None = Field(default=None)
    cut_wins: int | None = Field(default=None)
    cut_losses: int | None = Field(default=None)
    cut_draws: int | None = Field(default=None)
    cut_event_points: int | None = Field(default=None)
    cut_tie_breaker_points: int | None = Field(default=None)

    tournament: Tournament | None = Relationship(
        back_populates="team_standings")


class List(SQLModel, table=True):
    """
    Deduplicated squad list. One row per unique canonical signature.
    Referenced by PlayerStanding.list_id.
    """
    id: int | None = Field(default=None, primary_key=True)
    canonical_signature: str = Field(unique=True, index=False)  # UNIQUE creates implicit index
    faction: str
    faction_xws_normalized: str  # denormalized for fast WHERE filtering
    name: str | None = None
    points: int | None = None
    pilot_count: int | None = None
    ship_list: str  # sorted comma-joined: "btla4ywing,t65xwing,t65xwing"
    list_json: dict = Field(sa_column=Column(JSONB))
    created_at: datetime | None = Field(default=None)


class PlayerStanding(SQLModel, table=True):
    """
    A player's performance in a tournament.
    """
    id: int | None = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id")
    player_name: str = Field()
    team_id: int | None = Field(default=None, foreign_key="teamstanding.id")
    swiss_rank: int = Field(default=0)
    swiss_wins: int = Field(default=0)
    swiss_losses: int = Field(default=0)
    swiss_draws: int = Field(default=0)
    swiss_event_points: int | None = Field(default=None)
    swiss_tie_breaker_points: int | None = Field(default=None)
    cut_rank: int | None = Field(default=None)
    cut_wins: int | None = Field(default=None)
    cut_losses: int | None = Field(default=None)
    cut_draws: int | None = Field(default=None)
    cut_event_points: int | None = Field(default=None)
    cut_tie_breaker_points: int | None = Field(default=None)
    list_json: dict = Field(default={}, sa_column=Column(JSONB))
    list_id: int | None = Field(default=None, foreign_key="list.id", index=True)
    # Generated column: lower(replace(replace(list_json->>'faction', ' ', ''), '-', ''))
    # Mirrors the SQL GENERATED ALWAYS AS expression. Marked nullable since list_json
    # may lack a 'faction' key, in which case the column will be NULL.
    faction_xws_normalized: str | None = Field(
        default=None,
        sa_column=Column(
            String,
            Computed(
                "lower(replace(replace(list_json->>'faction', ' ', ''), '-', ''))",
                persisted=True,
            ),
        ),
    )

    tournament: Tournament | None = Relationship(back_populates="standings")
    team: TeamStanding | None = Relationship(
        sa_relationship_kwargs={"lazy": "select"})


class Match(SQLModel, table=True):
    """
    A single game between two players in a round.
    """
    id: int | None = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id")

    round_number: int
    round_type: RoundType = Field(
        default=RoundType.SWISS, sa_column=Column(String))
    scenario: Scenario | None = Field(default=None, sa_column=Column(String))

    player1_id: int | None = Field(
        default=None, foreign_key="playerstanding.id")
    player2_id: int | None = Field(
        default=None, foreign_key="playerstanding.id")

    player1_score: int = Field(default=-1)
    player2_score: int = Field(default=-1)

    winner_id: int | None = Field(default=None)  # -1 if draw
    is_bye: bool = Field(default=False)


class TeamMatch(SQLModel, table=True):
    """
    A single game between two teams in a round.
    """
    id: int | None = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id")

    round_number: int
    round_type: RoundType = Field(
        default=RoundType.SWISS, sa_column=Column(String))

    team1_id: int | None = Field(default=None, foreign_key="teamstanding.id")
    team2_id: int | None = Field(default=None, foreign_key="teamstanding.id")

    team1_score: int = Field(default=-1)
    team2_score: int = Field(default=-1)

    winner_id: int | None = Field(default=None)  # -1 if draw
    is_bye: bool = Field(default=False)


class ScrapeMeta(SQLModel, table=True):
    """
    Key/value store for incremental scrape state (e.g. data_version).

    Populated by `backend/scripts/migrate_performance.sql` for existing
    databases. `SQLModel.metadata.create_all` (in `database.create_db_and_tables`)
    will create it automatically for new installations.
    """
    key: str = Field(primary_key=True)
    value: str


class Supporter(SQLModel, table=True):
    """
    Represents a community supporter.
    """
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str | None = Field(default=None, index=True)
    total_contributed: float = Field(default=0.0)
    last_contribution: datetime = Field(default_factory=datetime.now)
    is_anonymous: bool = Field(default=False)

    contributions: list["Contribution"] = Relationship(
        back_populates="supporter")


class Contribution(SQLModel, table=True):
    """
    A single donation or contribution.
    """
    id: int | None = Field(default=None, primary_key=True)
    supporter_id: int | None = Field(default=None, foreign_key="supporter.id")
    amount: float
    currency: str = Field(default="USD")
    message: str | None = Field(default=None)
    date: datetime = Field(default_factory=datetime.now)
    ko_fi_transaction_id: str | None = Field(default=None, index=True)

    supporter: Supporter | None = Relationship(back_populates="contributions")
