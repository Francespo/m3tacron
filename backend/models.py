
"""
Database models and format utilities for the M3taCron platform.

Defines:
- Core entities: Tournament, PlayerStanding, TeamStanding, Match, TeamMatch
- Format enums and helper functions
- Duplicate detection and format inference utilities
"""
import logging
from sqlmodel import Field, Relationship, SQLModel
from datetime import date as date_type, datetime
from sqlalchemy import JSON, Boolean, Column, Computed, String
from sqlalchemy.dialects.postgresql import JSONB

# JSONB is Postgres-only; fall back to generic JSON on other backends
# (SQLite) so the schema can be created for local/artifact databases.
JSONB_VARIANT = JSONB().with_variant(JSON(), "sqlite")

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
    date: date_type = Field(index=True)
    location: Location | None = Field(default=Location(
        city="Unknown", country="Unknown", continent="Unknown"), sa_column=Column(LocationType))
    player_count: int = Field(default=0)
    team_count: int = Field(default=0)
    url: str

    source: Source = Field(sa_column=Column(String, index=True))
    format: Format | None = Field(default=None, sa_column=Column(String, index=True))

    # True when the event is a team tournament (has TeamStanding/TeamMatch rows).
    # Used by analytics to include only real member rows (is_team_member) and
    # exclude legacy team-placeholder rows.
    is_team_event: bool = Field(default=False, sa_column=Column("is_team_event", Boolean, index=True))

    standings: list["PlayerStanding"] = Relationship(
        back_populates="tournament")
    team_standings: list["TeamStanding"] = Relationship(
        back_populates="tournament")


class TeamStanding(SQLModel, table=True):
    """
    A team's identity in a tournament.
    """
    id: int | None = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id")
    team_name: str = Field()

    tournament: Tournament | None = Relationship(
        back_populates="team_standings")
    members: list["TeamMember"] = Relationship(back_populates="team")


class TeamMember(SQLModel, table=True):
    """
    Membership edge between a team and an individual player standing.

    One row per (team, member) pair; a player standing belongs to at most one
    team (enforced by the playerstanding_id unique constraint). The member's
    own list is on their PlayerStanding row; list_id/list_json here mirror it
    for convenience.

    NOTE: explicit __tablename__ = "team_member" — SQLModel would otherwise
    derive "teammember", which does not match the migration-created table
    ("team_member") and would make create_all try to recreate it, colliding
    with the existing unique constraint name.
    """
    __tablename__ = "team_member"

    id: int | None = Field(default=None, primary_key=True)
    teamstanding_id: int = Field(
        foreign_key="teamstanding.id", index=True)
    playerstanding_id: int = Field(
        foreign_key="playerstanding.id", unique=True, index=True)
    list_id: int | None = Field(default=None, foreign_key="list.id")
    list_json: dict | None = Field(default=None, sa_column=Column(JSONB_VARIANT))

    team: TeamStanding | None = Relationship(back_populates="members")
    player: "PlayerStanding" = Relationship(back_populates="team_membership")

    __table_args__ = (
        # One membership edge per (team, member) pair.
        __import__("sqlalchemy").UniqueConstraint(
            "teamstanding_id", "playerstanding_id",
            name="uq_team_member_team_player",
        ),
    )


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
    list_json: dict = Field(sa_column=Column(JSONB_VARIANT))
    created_at: datetime | None = Field(default=None)


class PlayerStanding(SQLModel, table=True):
    """
    A player's performance in a tournament.
    """
    # Allow transient (non-column) attributes like `team_name` to be attached
    # by scrapers without SQLModel trying to map them to columns.
    model_config = {"extra": "allow"}

    id: int | None = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id", index=True)
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
    list_json: dict = Field(default={}, sa_column=Column(JSONB_VARIANT))
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
    # True when this standing row is a real individual member of a team event.
    # False for solo-event players and for legacy team-placeholder rows (rows
    # whose player_name is a team name — created by the pre-team_member scraper).
    is_team_member: bool = Field(default=False, sa_column=Column("is_team_member", Boolean, index=True))
    team_membership: "TeamMember" = Relationship(back_populates="player")

    # NOTE: do NOT declare `team_name` here — SQLModel maps every annotated
    # class attribute to a table column, and `team_name` is not a real column
    # on playerstanding. Scrapers attach it dynamically as a transient
    # instance attribute (setattr) so save_tournament_data / migrations can
    # read it without SQLAlchemy trying to persist it.


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


class PilotShipMapping(SQLModel, table=True):
    """
    Lookup mapping pilot XWS -> ship XWS + canonical faction.

    Populated from the vendored xwing-data manifests (one row per
    (pilot_xws, source) pair). Used by the ships analytics aggregation to
    map every pilot occurrence in a list_json to the ship it flies and the
    faction that ship belongs to. Without this table the ships page returns
    zero stats; the faction column is what lets per-ship stats be broken
    down by pilot faction for the multi-faction pill toggle.
    """

    __tablename__ = "pilot_ship_mapping"  # type: ignore[assignment]

    pilot_xws: str = Field(primary_key=True)
    source: str = Field(primary_key=True)
    ship_xws: str = Field()
    faction: str | None = Field(default=None)


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
