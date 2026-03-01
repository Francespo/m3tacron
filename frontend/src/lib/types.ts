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
    popularity: number;
    win_rate: number;
    [key: string]: unknown;
}

export interface PilotStat {
    name: string;
    xws?: string;
    faction: string;
    ship_xws?: string;
    popularity: number;
    win_rate: number;
    [key: string]: unknown;
}

export interface UpgradeStat {
    name: string;
    xws?: string;
    popularity: number;
    win_rate: number;
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
