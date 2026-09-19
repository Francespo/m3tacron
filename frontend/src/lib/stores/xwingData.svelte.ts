
/**
 * Reactive store for X-Wing game data from xwing-data2 and xwing-data2-legacy.
 * Loads the pre-generated monolithic manifest (xwing-data.json).
 */

import { SHIP_DISPLAY_LABELS } from '$lib/data/shipLabels';
import { cardArtFallback, cardArtDonorIds } from '$lib/data/shipArt';

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
    /** Epic-only ships (no standard-legal pilots). Used by the ships page
     *  epic toggle: only shown when "Include Epic" is on. */
    epic?: boolean;
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

export const PACK_INFO_MAP: Record<string, { pack: string }> = {
    'armedanddangerous': { pack: 'Armed and Dangerous' },
    'evacuationofdqar': { pack: 'Evacuation of D\'QAR' },
    'battleoverendor': { pack: 'Battle Over Endor' },
    'battleofyavin': { pack: 'Battle of Yavin' },
    'siegeofcoruscant': { pack: 'Siege of Coruscant' },
    'alphastrike': { pack: 'Alpha Strike' },
};

export function getPackNameFromXws(xws: string): string | null {
    if (!xws) return null;
    const lower = xws.toLowerCase();
    for (const [key, info] of Object.entries(PACK_INFO_MAP)) {
        if (lower.includes(key)) {
            return info.pack;
        }
    }
    return null;
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

    /**
     * Pilot display name -> card image for the chassis that donate art to a
     * split variant (see `$lib/data/shipArt`). Built once per source during
     * init so `getPilot()` stays a pure lookup.
     */
    cardArtDonorImages = $state<Record<XWingSource, Record<string, string> | null>>({
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

            // Build pilot count map eagerly so getPilotCountByShip()
            // never mutates $state inside a template expression.
            const counts: Record<string, number> = {};
            const pilots = (json as any).pilots ?? {};
            for (const pilot of Object.values(pilots) as XWingPilot[]) {
                const ship = pilot?.ship;
                if (!ship) continue;
                counts[ship] = (counts[ship] ?? 0) + 1;
            }
            this.pilotCountByShip[source] = counts;

            // Card-art donors for split variants (e.g. the integrated-loadout
            // Y-Wing, whose own card PNGs 404 upstream).
            const donorIds = cardArtDonorIds();
            const donors: Record<string, string> = {};
            for (const pilot of Object.values(pilots) as XWingPilot[]) {
                if (!pilot?.ship || !pilot.name) continue;
                if (!donorIds.has(pilot.ship)) continue;
                donors[pilot.name] = pilot.image ?? '';
            }
            this.cardArtDonorImages[source] = donors;
        } catch (e: unknown) {
            const message = e instanceof Error ? e.message : String(e);
            this.error = message;
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
     *
     * The generated manifest carries the vendored upstream `name`, which is
     * identical for split chassis (both BTA-NR2 Y-Wing entries). The split
     * label is applied here, at the display lookup, so the manifest stays
     * reproducible from the vendored data.
     */
    getShip(xws: string): XWingShip | null {
        const d = this.getData();
        if (!d || !d.ships) return null;
        const ship = d.ships[xws] ?? null;
        if (!ship) return null;
        const label = SHIP_DISPLAY_LABELS[xws];
        return label ? { ...ship, name: label } : ship;
    }

    /**
     * Get pilot details by XWS.
     */
    getPilot(xws: string): (XWingPilot & { pack?: string }) | null {
        const d = this.getData();
        if (!d || !d.pilots) return null;
        if (!xws) return null;

        const pack = getPackNameFromXws(xws);

        if (d.pilots[xws]) {
            const p = d.pilots[xws];
            const resolved = pack && !(p as any).pack ? { ...p, pack } : p;
            return this.withCardArt(resolved);
        }

        const suffixes = [
            '-armedanddangerous',
            '-evacuationofdqar',
            '-battleoverendor',
            '-battleofyavin',
            '-siegeofcoruscant',
            '-alphastrike',
            '-lsl'
        ];

        let cleanId = xws;
        for (const suf of suffixes) {
            if (cleanId.endsWith(suf)) {
                cleanId = cleanId.slice(0, -suf.length);
            }
        }

        if (d.pilots[cleanId]) {
            const basePilot = d.pilots[cleanId];
            return this.withCardArt({
                ...basePilot,
                xws,
                pack: pack ?? undefined
            });
        }

        return null;
    }

    /**
     * Apply the declared card-art fallback for a split variant, at lookup
     * time. The manifest itself keeps the upstream (404) URLs.
     */
    private withCardArt<T extends { ship?: string; name?: string; image?: string }>(
        pilot: T,
    ): T {
        const fallback = pilot?.ship ? cardArtFallback(pilot.ship) : null;
        if (!fallback || !pilot.name) return pilot;
        const donorImage = this.cardArtDonorImages[this.currentSource]?.[pilot.name];
        if (!donorImage) return pilot;
        return { ...pilot, image: donorImage };
    }

    /**
     * Get upgrade details by XWS.
     */
    getUpgrade(xws: string): XWingUpgrade | null {
        const d = this.getData();
        if (!d || !d.upgrades) return null;
        if (!xws) return null;

        if (d.upgrades[xws]) {
            return d.upgrades[xws];
        }

        const suffixes = [
            '-armedanddangerous',
            '-evacuationofdqar',
            '-battleoverendor',
            '-battleofyavin',
            '-siegeofcoruscant',
            '-alphastrike',
            '-lsl'
        ];

        let cleanId = xws;
        for (const suf of suffixes) {
            if (cleanId.endsWith(suf)) {
                cleanId = cleanId.slice(0, -suf.length);
            }
        }

        if (d.upgrades[cleanId]) {
            return {
                ...d.upgrades[cleanId],
                xws
            };
        }

        return null;
    }

    /**
     * Get number of pilots for a ship/chassis XWS.
     * The map is built eagerly during init(), so this is a pure read.
     */
    getPilotCountByShip(shipXws: string, source: XWingSource = this.currentSource): number {
        return this.pilotCountByShip[source]?.[shipXws] ?? 0;
    }

    /**
     * Get number of pilots for a ship filtered by faction.
     * When faction is null/"all"/"unknown" the total is returned.
     */
    getPilotCountByShipForFaction(
        shipXws: string,
        faction: string | null,
        source: XWingSource = this.currentSource,
    ): number {
        if (!faction || faction === "all" || faction.toLowerCase() === "unknown") {
            return this.getPilotCountByShip(shipXws, source);
        }
        const data = this.data[source];
        if (!data?.pilots) return 0;
        const normWanted = faction.toLowerCase().replace(/[\s-]/g, "");
        let count = 0;
        for (const pilot of Object.values(data.pilots) as XWingPilot[]) {
            if (pilot.ship !== shipXws) continue;
            const pf = (pilot.faction ?? "").toLowerCase().replace(/[\s-]/g, "");
            if (pf === normWanted) count++;
        }
        return count;
    }
}

export const xwingData = new XwingDataStore();
