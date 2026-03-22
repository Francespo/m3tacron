
/**
 * Reactive store for X-Wing game data from xwing-data2 and xwing-data2-legacy.
 * Loads the pre-generated monolithic manifest (xwing-data.json).
 */

export type XWingSource = 'xwa' | 'legacy';

export interface XWingStat {
    type: string;
    value: number;
    arc?: string;
}

export interface XWingAction {
    type: string;
    difficulty: string;
    linked?: XWingAction;
}

export interface XWingPilot {
    name: string;
    xws: string;
    initiative: number;
    ability?: string;
    shipAbility?: {
        name: string;
        text: string;
    };
    image?: string;
    artwork?: string;
    caption?: string;
    limited: number;
    cost?: number; 
    loadout?: number; 
    ship: string; // XWS of ship
    faction: string; // XWS of faction
    force?: {
        value: number;
        recovers: number;
        side: string[];
    };
    charges?: {
        value: number;
        recovers: number;
    };
    slots?: string[];
}

export interface XWingShip {
    name: string;
    xws: string;
    size: string;
    stats: XWingStat[];
    actions: XWingAction[];
    /** Some manifests keep pilots inside ship, but our unified manifest separates them. Optional here. */
    pilots?: any[]; 
    icon?: string;
    factions: string[];
}

export interface XWingUpgrade {
    name: string;
    xws: string;
    limited: number;
    sides: {
        title: string;
        type: string;
        ability?: string;
        image?: string;
        artwork?: string;
        attack?: {
            arc: string;
            value: number;
            minrange: number;
            maxrange: number;
        };
        actions?: XWingAction[];
        grants?: { type: string; value: any }[];
        slots?: string[];
    }[];
    cost?: { value: number };
}

export interface XWingDataManifest {
    ships: Record<string, XWingShip>;
    pilots: Record<string, XWingPilot>;
    upgrades: Record<string, XWingUpgrade>;
}

class XwingDataStore {
    currentSource = $state<XWingSource>('xwa');

    // Data containers
    // Note: Svelte 5 reactivity with Map/Set requires reassignment or using specific reactive structure.
    // For simplicity, we just store the raw object which is deeply reactive if declared with $state?
    // Actually, $state(new Map()) works but mutations need to be tracked. 
    // Let's store the whole manifest object as state.
    data = $state<Record<XWingSource, XWingDataManifest | null>>({
        xwa: null,
        legacy: null
    });

    pilotCountByShip = $state<Record<XWingSource, Record<string, number> | null>>({
        xwa: null,
        legacy: null,
    });

    loading = $state(false);
    error = $state<string | null>(null);

    constructor() {
    }

    /**
     * Set the active data source.
     */
    async setSource(source: XWingSource) {
        const sameSource = this.currentSource === source;
        this.currentSource = source;

        // Even if the source did not change, ensure data exists.
        // This covers first render where default source is already "xwa".
        if (!this.data[source]) {
            await this.init(source);
        }

        if (sameSource) return;
    }

    /**
     * Initialize the store for a specific source by loading its manifest.
     */
    async init(source: XWingSource = this.currentSource) {
        if (this.data[source]) return;

        this.loading = true;
        try {
            const basePath = source === 'xwa' ? '/data-xwa' : '/data-legacy';
            const response = await fetch(`${basePath}/xwing-data.json`);
            if (!response.ok) throw new Error(`Failed to load ${source} data`);
            const json = await response.json();

            this.data[source] = json;
            this.pilotCountByShip[source] = null;
        } catch (e) {
            this.error = e.message;
            console.error(`XwingDataStore init error (${source}):`, e);
        } finally {
            this.loading = false;
        }
    }

    private getData(source: XWingSource = this.currentSource) {
        return this.data[source];
    }

    /**
     * Get ship details by XWS.
     */
    getShip(xws: string): XWingShip | null {
        const d = this.getData();
        if (!d || !d.ships) return null;
        return d.ships[xws] ?? null;
    }

    /**
     * Get pilot details by XWS.
     */
    getPilot(xws: string): XWingPilot | null {
        const d = this.getData();
        if (!d || !d.pilots) return null;
        return d.pilots[xws] ?? null;
    }

    /**
     * Get upgrade details by XWS.
     */
    getUpgrade(xws: string): XWingUpgrade | null {
        const d = this.getData();
        if (!d || !d.upgrades) return null;
        return d.upgrades[xws] ?? null;
    }

    /**
     * Get number of pilots for a ship/chassis XWS.
     * Built once per source and then served from cache.
     */
    getPilotCountByShip(shipXws: string, source: XWingSource = this.currentSource): number {
        const d = this.getData(source);
        if (!d || !d.pilots) return 0;

        if (!this.pilotCountByShip[source]) {
            const counts: Record<string, number> = {};
            for (const pilot of Object.values(d.pilots)) {
                const ship = pilot?.ship;
                if (!ship) continue;
                counts[ship] = (counts[ship] ?? 0) + 1;
            }
            this.pilotCountByShip[source] = counts;
        }

        return this.pilotCountByShip[source]?.[shipXws] ?? 0;
    }
}

export const xwingData = new XwingDataStore();
