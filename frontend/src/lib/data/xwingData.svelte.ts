
/**
 * Reactive store for X-Wing game data from xwing-data2 and xwing-data2-legacy.
 * Handles lazy loading and caching of high-fidelity ship and upgrade info
 * based on the active data source (XWA vs Legacy).
 */

export type XWingSource = 'xwa' | 'legacy';

export interface XWingManifest {
    pilots: {
        faction: string;
        ships: string[];
    }[];
    upgrades: string[];
}

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
    image?: string;
    artwork?: string;
    caption?: string;
    limited: number;
    cost?: number; // Might be overridden by backend
    loadout?: number; // Might be overridden by backend
    force?: {
        value: number;
        recovers: number;
        side: string[];
    };
    charges?: {
        value: number;
        recovers: number;
    };
}

export interface XWingShip {
    name: string;
    xws: string;
    size: string;
    stats: XWingStat[];
    actions: XWingAction[];
    pilots: XWingPilot[];
    icon?: string;
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
    }[];
    cost?: { value: number }; // Might be overridden by backend
}

class XwingDataStore {
    currentSource = $state<XWingSource>('xwa');

    // Manifests and mappings per source
    manifests = new Map<XWingSource, XWingManifest | null>();
    shipPaths = new Map<XWingSource, Map<string, Map<string, string>>>();
    upgradePaths = new Map<XWingSource, Map<string, string>>();

    // Caches per source (Key is the file path)
    shipCache = new Map<XWingSource, Map<string, XWingShip>>();
    upgradeCache = new Map<XWingSource, Map<string, XWingUpgrade[]>>();

    loading = $state(false);
    error = $state<string | null>(null);

    constructor() {
        this.manifests.set('xwa', null);
        this.manifests.set('legacy', null);
        this.shipPaths.set('xwa', new Map());
        this.shipPaths.set('legacy', new Map());
        this.upgradePaths.set('xwa', new Map());
        this.upgradePaths.set('legacy', new Map());
        this.shipCache.set('xwa', new Map());
        this.shipCache.set('legacy', new Map());
        this.upgradeCache.set('xwa', new Map());
        this.upgradeCache.set('legacy', new Map());
    }

    /**
     * Set the active data source.
     */
    async setSource(source: XWingSource) {
        if (this.currentSource === source) return;
        this.currentSource = source;
        await this.init(source);
    }

    /**
     * Initialize the store for a specific source by loading its manifest.
     */
    async init(source: XWingSource = this.currentSource) {
        if (this.manifests.get(source)) return;

        this.loading = true;
        try {
            const basePath = source === 'xwa' ? '/data-xwa' : '/data-legacy';
            const response = await fetch(`${basePath}/manifest.json`);
            if (!response.ok) throw new Error(`Failed to load ${source} manifest`);
            const data: XWingManifest = await response.json();

            // Build pilots/ships mapping
            const factionMap = this.shipPaths.get(source)!;
            for (const factionEntry of data.pilots) {
                const shipsMap = new Map<string, string>();
                for (const shipRelativePath of factionEntry.ships) {
                    const filename = shipRelativePath.split('/').pop()!;
                    const shipXws = filename.replace('.json', '');
                    shipsMap.set(shipXws, `${basePath}/${shipRelativePath}`);
                }
                factionMap.set(factionEntry.faction, shipsMap);
            }

            // Build upgrades mapping
            const upgMap = this.upgradePaths.get(source)!;
            for (const upgradeRelativePath of data.upgrades) {
                const filename = upgradeRelativePath.split('/').pop()!;
                const slotXws = filename.replace('.json', '');
                upgMap.set(slotXws, `${basePath}/${upgradeRelativePath}`);
            }

            this.manifests.set(source, data);
        } catch (e: any) {
            this.error = e.message;
            console.error(`XwingDataStore init error (${source}):`, e);
        } finally {
            this.loading = false;
        }
    }

    /**
     * Get ship and all its pilots from the current source.
     */
    async getShip(factionXws: string, shipXws: string): Promise<XWingShip | null> {
        const source = this.currentSource;
        await this.init(source);

        const path = this.shipPaths.get(source)?.get(factionXws)?.get(shipXws);
        if (!path) return null;

        const cache = this.shipCache.get(source)!;
        if (cache.has(path)) {
            return cache.get(path)!;
        }

        try {
            const response = await fetch(path);
            if (!response.ok) throw new Error(`Failed to load ship: ${path}`);
            const data: XWingShip = await response.json();
            cache.set(path, data);
            return data;
        } catch (e) {
            console.error(e);
            return null;
        }
    }

    /**
     * Get specific pilot details by drilling down into ship data.
     */
    async getPilot(factionXws: string, shipXws: string, pilotXws: string): Promise<XWingPilot | null> {
        const ship = await this.getShip(factionXws, shipXws);
        if (!ship) return null;
        return ship.pilots.find(p => p.xws === pilotXws) ?? null;
    }

    /**
     * Get upgrade data by xws from the current source.
     * Drills down into the slot-specific JSON file.
     */
    async getUpgrade(slotXws: string, upgradeXws: string): Promise<XWingUpgrade | null> {
        const source = this.currentSource;
        await this.init(source);

        const path = this.upgradePaths.get(source)?.get(slotXws);
        if (!path) return null;

        const cache = this.upgradeCache.get(source)!;
        let upgrades = cache.get(path);

        if (!upgrades) {
            try {
                const response = await fetch(path);
                if (!response.ok) throw new Error(`Failed to load upgrades: ${path}`);
                upgrades = await response.json();
                cache.set(path, upgrades!);
            } catch (e) {
                console.error(e);
                return null;
            }
        }

        return upgrades?.find(u => u.xws === upgradeXws) ?? null;
    }
}

export const xwingData = new XwingDataStore();
