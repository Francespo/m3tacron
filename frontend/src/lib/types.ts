/**
 * TypeScript interfaces mirroring the FastAPI pydantic schemas
 * from backend/api/schemas.py.
 */

export interface UpgradeData {
    name: string;
    xws: string;
    slot: string;
    slot_icon: string;
    image: string;
    points: number;
}

export interface PilotData {
    name: string;
    xws: string;
    ship_name: string;
    ship_icon: string;
    image: string;
    points: number;
    loadout: number;
    upgrades: UpgradeData[];
}

export interface ListData {
    signature: string;
    faction: string;
    faction_key: string;
    points: number;
    count: number;
    games: number;
    win_rate: number;
    total_loadout: number;
    pilots: PilotData[];
}

export interface FactionStat {
    name: string;
    xws: string;
    icon_char: string;
    win_rate: number;
    popularity: number;
    games: number;
    wins: number;
    percentage?: number;
    real_name?: string;
}

export interface ShipStat {
    ship_name: string;
    ship_xws: string;
    faction: string;
    faction_xws: string;
    win_rate: number | string;
    popularity: number;
    games: number;
    [key: string]: unknown;
}

export interface PilotStat {
    name: string;
    xws: string;
    count: number;
    popularity: number;
    wins: number;
    games: number;
    faction: string;
    ship: string;
    ship_xws: string;
    ship_icon: string;
    image: string;
    cost: number;
    loadout: number;
    win_rate: number | string;
    [key: string]: unknown;
}

export interface UpgradeStat {
    name: string;
    xws: string;
    type: string;
    count: number;
    popularity: number;
    wins: number;
    games: number;
    image: string;
    cost: number;
    win_rate: number | string;
    [key: string]: unknown;
}

export interface MetaSnapshotResponse {
    factions: FactionStat[];
    faction_distribution: FactionStat[];
    ships: ShipStat[];
    lists: ListData[];
    pilots: PilotStat[];
    upgrades: UpgradeStat[];
    last_sync: string;
    date_range: string;
    total_tournaments: number;
    total_players: number;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    size: number;
}

export interface TournamentRow {
    id: number;
    name: string;
    date: string;
    players: number;
    format_label: string;
    badge_l1: string;
    badge_l2: string;
    platform_label: string;
    location: string;
    url: string;
}
