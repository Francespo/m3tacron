import { API_BASE } from '$lib/api';

export interface ShipChassis {
    xws: string;
    name: string;
    factions: string[];
}

export interface ShipOptionsResponse {
    items: ShipChassis[];
    total: number;
    page: number;
    size: number;
    has_more: boolean;
}

export async function fetchAllShips(dataSource: string): Promise<ShipChassis[]> {
    try {
        const response = await fetch(`${API_BASE}/ships/all?data_source=${dataSource}`);
        if (!response.ok) throw new Error('Failed to fetch ships');
        return await response.json();
    } catch (e) {
        console.error(e);
        return [];
    }
}

export async function fetchShipOptionsPage(
    dataSource: string,
    page: number,
    size = 80,
    search = "",
    factions: string[] = [],
): Promise<ShipOptionsResponse> {
    try {
        const params = new URLSearchParams();
        params.set("data_source", dataSource);
        params.set("page", String(page));
        params.set("size", String(size));
        if (search.trim()) params.set("search", search.trim());
        for (const faction of factions) {
            params.append("factions", faction);
        }

        const response = await fetch(`${API_BASE}/ships/options?${params.toString()}`);
        if (!response.ok) throw new Error("Failed to fetch ship options");
        return await response.json();
    } catch (e) {
        console.error(e);
        return {
            items: [],
            total: 0,
            page,
            size,
            has_more: false,
        };
    }
}
