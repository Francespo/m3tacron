from pydantic import BaseModel, Field
from typing import Any

class UpgradeData(BaseModel):
    xws: str
    slot_xws: str  # slot type xws

class PilotData(BaseModel):
    xws: str
    ship_xws: str
    faction_xws: str
    upgrades: list[UpgradeData] = []

class ListData(BaseModel):
    signature: str = ""
    name: str = ""
    faction_xws: str = ""
    points: int = 0
    original_points: int = 0
    wins: int = 0
    games: int = 0
    total_loadout: int = 0
    pilots: list[PilotData] = []

class FactionStat(BaseModel):
    name: str
    xws: str
    icon_char: str
    win_rate: float
    popularity: int
    games: int
    wins: int
    percentage: float | None = None
    real_name: str | None = None

class MetaSnapshotResponse(BaseModel):
    factions: list[FactionStat]
    faction_distribution: list[FactionStat]
    ships: list[dict[str, Any]]
    lists: list[ListData]
    pilots: list[dict[str, Any]]
    upgrades: list[dict[str, Any]]
    last_sync: str
    date_range: str
    total_tournaments: int
    total_players: int

class TournamentRow(BaseModel):
    id: int
    name: str
    date: str
    players: int
    format_label: str
    badge_l1: str
    badge_l2: str
    platform_label: str
    location: str
    url: str

class PaginatedTournamentsResponse(BaseModel):
    items: list[TournamentRow]
    total: int
    page: int
    size: int

class PaginatedListsResponse(BaseModel):
    items: list[ListData]
    total: int
    page: int
    size: int

class PaginatedPilotsResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    size: int

class PaginatedUpgradesResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    size: int

class PaginatedShipsResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    size: int

class PlayerStandingsRow(BaseModel):
    id: int
    name: str
    rank: int
    swiss_rank: int
    cut_rank: int | None = None
    wins: int
    losses: int
    faction: str
    faction_xws: str
    has_list: bool
    list_json: dict[str, Any] | None = None

class MatchRow(BaseModel):
    round: int
    type: str
    player1: str
    player2: str
    player1_id: int
    player2_id: int
    score1: int
    score2: int
    winner_id: int
    scenario: str

class TournamentDetailResponse(BaseModel):
    tournament: TournamentRow
    players_swiss: list[PlayerStandingsRow]
    players_cut: list[PlayerStandingsRow]
    matches: list[MatchRow]
