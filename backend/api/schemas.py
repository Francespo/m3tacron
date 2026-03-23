from pydantic import BaseModel
from typing import Any
from backend.data_structures.factions import Faction
from backend.data_structures.formats import Format
from backend.data_structures.source import Source

# 1. Composition Data (Structural)

class UpgradeData(BaseModel):
    xws: str

class PilotData(BaseModel):
    xws: str
    upgrades: list[UpgradeData] = []

class ListData(BaseModel):
    name: str = ""
    signature: str
    points: int
    original_points: int
    faction_xws: Faction
    pilots: list[PilotData]
    wins: int
    games: int

# 2. Analytics Stats (Aggregated)

class FactionStats(BaseModel):
    xws: Faction
    games_count: int
    list_count: int
    different_lists_count: int
    wins: int

class PilotStats(BaseModel):
    xws: str
    games_count: int
    list_count: int
    different_lists_count: int
    wins: int

class UpgradeStats(BaseModel):
    xws: str
    games_count: int
    list_count: int
    different_lists_count: int
    wins: int

class ShipStats(BaseModel):
    xws: str
    faction_xws: Faction
    games_count: int
    list_count: int
    different_lists_count: int
    wins: int

# 3. Event Data (Tournaments and Results)

class TournamentData(BaseModel):
    id: int
    name: str
    date: str
    players: int
    format: Format | None
    source: Source
    location: str
    url: str

class PlayerResultData(BaseModel):
    id: int
    name: str
    rank: int
    swiss_rank: int
    cut_rank: int | None = None
    wins: int
    losses: int
    list_json: dict[str, Any] | None = None
    faction: Faction

class MatchData(BaseModel):
    round: int
    type: str
    player1: str
    player2: str
    score1: int
    score2: int
    winner_id: int | None = None
    scenario: str

# Response Models

class MetaSnapshotResponse(BaseModel):
    factions: list[FactionStats]
    ships: list[ShipStats]
    lists: list[ListData]
    pilots: list[PilotStats]
    upgrades: list[UpgradeStats]
    last_sync: str
    date_range: str
    total_tournaments: int
    total_players: int

class PaginatedTournamentsResponse(BaseModel):
    items: list[TournamentData]
    total: int
    page: int
    size: int

class PaginatedListsResponse(BaseModel):
    items: list[ListData]
    total: int
    page: int
    size: int

class PaginatedPilotsResponse(BaseModel):
    items: list[PilotStats]
    total: int
    page: int
    size: int

class PaginatedUpgradesResponse(BaseModel):
    items: list[UpgradeStats]
    total: int
    page: int
    size: int

class PaginatedShipsResponse(BaseModel):
    items: list[ShipStats]
    total: int
    page: int
    size: int

class TournamentDetailResponse(BaseModel):
    tournament: TournamentData
    players_swiss: list[PlayerResultData]
    players_cut: list[PlayerResultData]
    matches: list[MatchData]
