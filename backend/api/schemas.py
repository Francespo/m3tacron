from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class UpgradeData(BaseModel):
    name: str = ""
    xws: str = ""
    slot: str = ""
    points: int = 0

class PilotData(BaseModel):
    name: str = ""
    xws: str = ""
    ship_name: str = ""
    ship_icon: str = ""
    points: int = 0
    loadout: int = 0
    upgrades: List[UpgradeData] = []

class ListData(BaseModel):
    signature: str = ""
    name: str = ""
    faction: str = ""
    faction_xws: str = ""
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

class PilotRow(BaseModel):
    name: str
    xws: str
    count: int
    popularity: int
    wins: int
    games: int
    lists: int
    faction: str
    faction_xws: str
    ship: str
    ship_xws: str
    ship_icon: str
    image: str
    cost: int
    loadout: int
    win_rate: str | float
    icon_char: str

class UpgradeRow(BaseModel):
    name: str
    xws: str
    type: str
    count: int
    popularity: int
    wins: int
    games: int
    lists: int
    image: str
    cost: int
    win_rate: str | float

class ShipRow(BaseModel):
    ship_name: str
    ship_xws: str
    faction: str
    faction_xws: str
    icon_char: str
    win_rate: str | float
    popularity: int
    games: int
    pilots_count: int

class SquadronRow(BaseModel):
    signature: str
    faction: str
    faction_xws: str
    games: int
    win_rate: float
    count: int
    pilots: List[Dict[str, str]]

class PaginatedPilotsResponse(BaseModel):
    items: List[PilotRow]
    total: int
    page: int
    size: int

class PaginatedUpgradesResponse(BaseModel):
    items: List[UpgradeRow]
    total: int
    page: int
    size: int

class PaginatedShipsResponse(BaseModel):
    items: List[ShipRow]
    total: int
    page: int
    size: int

class PaginatedSquadronsResponse(BaseModel):
    items: List[SquadronRow]
    total: int
    page: int
    size: int

class PilotInfo(BaseModel):
    name: str
    xws: str
    image: str
    ship: Optional[str] = None
    ship_xws: Optional[str] = None
    faction: Optional[str] = None
    faction_xws: Optional[str] = None
    cost: Optional[int] = None
    loadout: Optional[int] = None

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

class ChartDataPoint(BaseModel):
    date: str
    usage: float

class CardChartResponse(BaseModel):
    data: Dict[str, List[ChartDataPoint]]
    series: List[str]

class PilotConfiguration(BaseModel):
    upgrades: List[UpgradeRow]
    count: int
    wins: int
    win_rate: float

class PilotConfigurationsResponse(BaseModel):
    configurations: List[PilotConfiguration]
    total: int

class ShipDetailResponse(BaseModel):
    info: Dict[str, Any]
    stats: Dict[str, Any]

class ShipPilotsResponse(BaseModel):
    pilots: List[PilotRow]

class ShipListsResponse(BaseModel):
    lists: List[ListData]

class ShipSquadronsResponse(BaseModel):
    squadrons: List[SquadronRow]

class SquadronPilotRow(BaseModel):
    pilot_xws: str
    ship_xws: str
    name: str
    cost: int
    games: int
    win_rate: float
    percent_of_squadron: float

class PilotDetailResponse(BaseModel):
    info: PilotInfo
    upgrades: PaginatedUpgradesResponse
    chart: CardChartResponse
    configurations: PilotConfigurationsResponse
