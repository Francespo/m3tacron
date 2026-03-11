import { API_BASE } from '$lib/api';

export interface ShipChassis {
    xws: string;
    name: string;
    factions: string[];
}

export async function fetchAllShips(dataSource: string, includeEpic: boolean = false): Promise<ShipChassis[]> {
    try {
        const response = await fetch(`${API_BASE}/ships/all?data_source=${dataSource}&include_epic=${includeEpic}`);
        if (!response.ok) throw new Error('Failed to fetch ships');
        return await response.json();
    } catch (e) {
        console.error(e);
        return [];
    }
}
