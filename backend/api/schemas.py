from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UpgradeData(BaseModel):
    name: str = ""
    xws: str = ""
    slot: str = ""
    slot_icon: str = ""
    image: str = ""
    points: int = 0

class PilotData(BaseModel):
    name: str = ""
    xws: str = ""
    ship_name: str = ""
    ship_icon: str = ""
    image: str = ""
    points: int = 0
    loadout: int = 0
    upgrades: List[UpgradeData] = []

class ListData(BaseModel):
    signature: str = ""
    name: str = ""
    faction: str = ""
    faction_key: str = ""
    faction_xws: str = ""
    icon_char: str = ""
    points: int = 0
    original_points: int = 0
    count: int = 0
    games: int = 0
    win_rate: float = 0.0
    total_loadout: int = 0
    pilots: List[PilotData] = []

class FactionStat(BaseModel):
    name: str
    xws: str
    icon_char: str
    win_rate: float
    popularity: int
    games: int
    wins: int
    percentage: Optional[float] = None
    real_name: Optional[str] = None

class MetaSnapshotResponse(BaseModel):
    factions: List[FactionStat]
    faction_distribution: List[FactionStat]
    ships: List[Dict[str, Any]]
    lists: List[ListData]
    pilots: List[Dict[str, Any]]
    upgrades: List[Dict[str, Any]]
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
    items: List[TournamentRow]
    total: int
    page: int
    size: int

class PaginatedListsResponse(BaseModel):
    items: List[ListData]
    total: int
    page: int
    size: int

class PaginatedPilotsResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    size: int

class PaginatedUpgradesResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    size: int

class PaginatedShipsResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    size: int

class PlayerStandingsRow(BaseModel):
    id: int
    name: str
    rank: int
    swiss_rank: int
    cut_rank: Optional[int] = None
    wins: int
    losses: int
    faction: str
    faction_xws: str
    has_list: bool
    list_json: Optional[Dict[str, Any]] = None

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
    players_swiss: List[PlayerStandingsRow]
    players_cut: List[PlayerStandingsRow]
    matches: List[MatchRow]

class FundTier(BaseModel):
    name: str
    target: Optional[float] = None
    current: float
    description: str

class FundStatusResponse(BaseModel):
    total_raised: float
    tiers: List[FundTier]

class SupporterResponse(BaseModel):
    name: str
    amount: float
    date: datetime
    message: Optional[str] = None
