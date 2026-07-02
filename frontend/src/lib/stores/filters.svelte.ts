/**
 * Global Filter State.
 * Mirrors Reflex GlobalFilterState across all pages.
 *
 * The store is pure: it must NOT import $app/navigation, setTimeout, or
 * anything that triggers navigation / side effects. URL synchronization
 * is performed by callers (each route) which build URLSearchParams via
 * `toSearchParams` and then call `goto()` themselves.
 *
 * The one exception is the read-only `isPendingSync()` import from
 * `$lib/sync/urlSync.svelte`: it is a non-mutating flag that lets
 * `applyFromSearchParams` distinguish a stale-URL race condition
 * (the store just mutated, the URL hasn't caught up yet) from a real
 * navigation. The store itself never *causes* a navigation.
 */

import { getFormatFullLabel } from "$lib/data/formats";
import { isPendingSync, resolvePendingSync, markHydrated } from "$lib/sync/urlSync.svelte";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let dataSource = $state<'xwa' | 'legacy'>('xwa');
let includeEpic = $state(false);
let dateStart = $state('');
let dateEnd = $state('');
let selectedContinents = $state<string[]>([]);
let selectedCountries = $state<string[]>([]);
let selectedCities = $state<string[]>([]);
let selectedFormats = $state<string[]>([]);
let searchName = $state('');
let selectedSources = $state<string[]>([]);
let selectedShips = $state<string[]>([]);
let selectedFactions = $state<string[]>([]);

// Sort (was route-local; centralized here so the URL can round-trip it).
// Empty `sortBy` means "use the route's default"; routes should treat that
// as their own default sort metric when building the API call.
let sortBy = $state<string>('');
let sortDirection = $state<'asc' | 'desc'>('desc');

// Advanced Filters (Cards Page)
let pointsMin = $state('');
let pointsMax = $state('');
let loadoutMin = $state('');
let loadoutMax = $state('');
let isUnique = $state(false);
let isLimited = $state(false);
let isGeneric = $state(false);
let selectedBaseSizes = $state<string[]>([]);
let initMin = $state('');
let initMax = $state('');
let hullMin = $state('');
let hullMax = $state('');
let shieldsMin = $state('');
let shieldsMax = $state('');
let agilityMin = $state('');
let agilityMax = $state('');
let attackMin = $state('');
let attackMax = $state('');

// ---------------------------------------------------------------------------
// Derived: active filter chips
// ---------------------------------------------------------------------------

/** Shape consumed by `ActiveFilters.svelte` and `ActiveChips.svelte`. */
export interface FilterChip {
    key: string;
    label: string;
}

/** Memoized chip descriptors describing every non-default filter currently set. */
let activeChips = $derived<FilterChip[]>(buildActiveChips());

function buildActiveChips(): FilterChip[] {
    const chips: FilterChip[] = [];
    if (dateStart) chips.push({ key: 'dateStart', label: `From ${dateStart}` });
    if (dateEnd) chips.push({ key: 'dateEnd', label: `To ${dateEnd}` });
    for (const c of selectedContinents) chips.push({ key: `continent:${c}`, label: c });
    for (const c of selectedCountries) chips.push({ key: `country:${c}`, label: c });
    for (const c of selectedCities) chips.push({ key: `city:${c}`, label: c });
    for (const p of selectedSources) chips.push({ key: `source:${p}`, label: p });
    for (const s of selectedShips) chips.push({ key: `ship:${s}`, label: `Ship: ${s}` });
    for (const f of selectedFactions) chips.push({ key: `faction:${f}`, label: `Faction: ${f}` });

    for (const f of selectedFormats) {
        chips.push({ key: `format:${f}`, label: getFormatFullLabel(f) });
    }

    if (searchName) chips.push({ key: 'search', label: `"${searchName}"` });

    // Advanced Chips
    if (pointsMin || pointsMax) chips.push({ key: 'points', label: `Pts: ${pointsMin || 0}-${pointsMax || '∞'}` });
    if (loadoutMin || loadoutMax) chips.push({ key: 'loadout', label: `LV: ${loadoutMin || 0}-${loadoutMax || '∞'}` });
    if (isUnique) chips.push({ key: 'isUnique', label: 'Unique' });
    if (isLimited) chips.push({ key: 'isLimited', label: 'Limited' });
    if (isGeneric) chips.push({ key: 'isGeneric', label: 'Generic' });
    for (const b of selectedBaseSizes) chips.push({ key: `base:${b}`, label: `Base: ${b}` });

    if (initMin || initMax) chips.push({ key: 'init', label: `Init: ${initMin || 0}-${initMax || 6}` });
    if (hullMin || hullMax) chips.push({ key: 'hull', label: `Hull: ${hullMin || 0}-${hullMax || '∞'}` });
    if (shieldsMin || shieldsMax) chips.push({ key: 'shields', label: `Shields: ${shieldsMin || 0}-${shieldsMax || '∞'}` });
    if (agilityMin || agilityMax) chips.push({ key: 'agility', label: `Agility: ${agilityMin || 0}-${agilityMax || 3}` });
    if (attackMin || attackMax) chips.push({ key: 'attack', label: `Attack: ${attackMin || 0}-${attackMax || '∞'}` });

    return chips;
}

function removeChip(key: string) {
    if (key === 'dateStart') dateStart = '';
    else if (key === 'dateEnd') dateEnd = '';
    else if (key === 'search') searchName = '';
    else if (key === 'points') { pointsMin = ''; pointsMax = ''; }
    else if (key === 'loadout') { loadoutMin = ''; loadoutMax = ''; }
    else if (key === 'isUnique') isUnique = false;
    else if (key === 'isLimited') isLimited = false;
    else if (key === 'isGeneric') isGeneric = false;
    else if (key === 'init') { initMin = ''; initMax = ''; }
    else if (key === 'hull') { hullMin = ''; hullMax = ''; }
    else if (key === 'shields') { shieldsMin = ''; shieldsMax = ''; }
    else if (key === 'agility') { agilityMin = ''; agilityMax = ''; }
    else if (key === 'attack') { attackMin = ''; attackMax = ''; }
    else if (key.startsWith('base:'))
        selectedBaseSizes = selectedBaseSizes.filter(b => b !== key.slice(5));
    else if (key.startsWith('continent:'))
        selectedContinents = selectedContinents.filter(c => c !== key.slice(10));
    else if (key.startsWith('country:'))
        selectedCountries = selectedCountries.filter(c => c !== key.slice(8));
    else if (key.startsWith('city:'))
        selectedCities = selectedCities.filter(c => c !== key.slice(5));
    else if (key.startsWith('source:'))
        selectedSources = selectedSources.filter(p => p !== key.slice(7));
    else if (key.startsWith('format:'))
        selectedFormats = selectedFormats.filter(f => f !== key.slice(7));
    else if (key.startsWith('ship:'))
        selectedShips = selectedShips.filter(s => s !== key.slice(5));
    else if (key.startsWith('faction:'))
        selectedFactions = selectedFactions.filter(f => f !== key.slice(8));
}

function resetAll() {
    dateStart = '';
    dateEnd = '';
    selectedContinents = [];
    selectedCountries = [];
    selectedCities = [];
    selectedSources = [];
    selectedShips = [];
    selectedFactions = [];

    // CRITICAL: Reset All must respect the active Game Content Source
    if (dataSource === 'xwa') {
        selectedFormats = ['xwa'];
    } else if (dataSource === 'legacy') {
        selectedFormats = ['legacy_x2po'];
    } else {
        selectedFormats = [];
    }

    searchName = '';
    pointsMin = ''; pointsMax = '';
    loadoutMin = ''; loadoutMax = '';
    isUnique = false; isLimited = false; isGeneric = false;
    selectedBaseSizes = [];
    initMin = ''; initMax = '';
    hullMin = ''; hullMax = '';
    shieldsMin = ''; shieldsMax = '';
    agilityMin = ''; agilityMax = '';
    attackMin = ''; attackMax = '';
}

// ---------------------------------------------------------------------------
// URL serialization
// ---------------------------------------------------------------------------

/** The set of routes that consume this store. */
export type RouteId = 'cards' | 'lists' | 'ships' | 'squadrons' | 'tournaments';

/**
 * Per-route whitelist of store fields, in the **order** they should be emitted
 * in the URL query string. The order is significant: `URLSearchParams`
 * preserves insertion order, and `applyFromSearchParams` → `toSearchParams`
 * must round-trip to an identical string so callers can break the URL-echo
 * loop with a string-equality guard.
 */
type FieldKey =
    | 'dataSource'
    | 'includeEpic'
    | 'selectedFormats'
    | 'selectedFactions'
    | 'selectedShips'
    | 'selectedSources'
    | 'selectedContinents'
    | 'selectedCountries'
    | 'selectedCities'
    | 'dateStart'
    | 'dateEnd'
    | 'searchName'
    | 'pointsMin'
    | 'pointsMax'
    | 'loadoutMin'
    | 'loadoutMax'
    | 'isUnique'
    | 'isLimited'
    | 'isGeneric'
    | 'selectedBaseSizes'
    | 'sortBy'
    | 'sortDirection';

const ROUTE_FIELDS: Record<RouteId, readonly FieldKey[]> = {
    cards: [
        'dataSource',
        'includeEpic',
        'selectedFormats',
        'selectedFactions',
        'selectedShips',
        'selectedSources',
        'selectedContinents',
        'selectedCountries',
        'selectedCities',
        'dateStart',
        'dateEnd',
        'searchName',
        'pointsMin',
        'pointsMax',
        'loadoutMin',
        'loadoutMax',
        'isUnique',
        'isLimited',
        'isGeneric',
        'selectedBaseSizes',
        'sortBy',
        'sortDirection',
    ],
    lists: [
        'dataSource',
        'includeEpic',
        'selectedFormats',
        'selectedFactions',
        'selectedShips',
        'sortBy',
        'sortDirection',
    ],
    ships: [
        'dataSource',
        'includeEpic',
        'selectedFormats',
        'selectedFactions',
        'selectedShips',
        'sortBy',
        'sortDirection',
    ],
    squadrons: [
        'dataSource',
        'includeEpic',
        'selectedFormats',
        'selectedFactions',
        'selectedShips',
        'sortBy',
        'sortDirection',
    ],
    tournaments: [
        'dataSource',
        'includeEpic',
        'selectedFormats',
        'selectedSources',
        'selectedContinents',
        'selectedCountries',
        'selectedCities',
        'dateStart',
        'dateEnd',
        'searchName',
        'sortBy',
        'sortDirection',
    ],
};

/** Maps a single-value field to its URL key. */
const SINGLE_KEY: Record<FieldKey, string> = {
    dataSource: 'data_source',
    includeEpic: 'epic',
    searchName: 'search',
    dateStart: 'date_start',
    dateEnd: 'date_end',
    pointsMin: 'points_min',
    pointsMax: 'points_max',
    loadoutMin: 'loadout_min',
    loadoutMax: 'loadout_max',
    isUnique: 'is_unique',
    isLimited: 'is_limited',
    isGeneric: 'is_not_limited',
    sortBy: 'sort_metric',
    sortDirection: 'sort_direction',
    // Multi-value fields — these use `params.append` and a fixed URL key:
    selectedFormats: 'formats',
    selectedFactions: 'factions',
    selectedShips: 'ships',
    selectedSources: 'sources',
    selectedContinents: 'continent',
    selectedCountries: 'country',
    selectedCities: 'city',
    selectedBaseSizes: 'base_sizes',
};

/**
 * Serialize the current filter state to a `URLSearchParams` containing ONLY
 * the fields the given route supports. Default values are omitted, multi-
 * value fields use repeated keys, and the key order is deterministic.
 *
 * `selectedFormats` is always written in full (even when it matches the
 * current `dataSource` default) so the URL round-trips cleanly with
 * `applyFromSearchParams` and multi-select stays stable across re-renders.
 */
function toSearchParams(routeId: RouteId): URLSearchParams {
    const params = new URLSearchParams();
    const fields = ROUTE_FIELDS[routeId];

    for (const field of fields) {
        switch (field) {
            case 'dataSource':
                if (dataSource !== 'xwa') {
                    params.set(SINGLE_KEY.dataSource, dataSource);
                }
                break;
            case 'includeEpic':
                if (includeEpic) {
                    params.set(SINGLE_KEY.includeEpic, 'true');
                }
                break;
            case 'searchName':
                if (searchName) {
                    params.set(SINGLE_KEY.searchName, searchName);
                }
                break;
            case 'dateStart':
                if (dateStart) {
                    params.set(SINGLE_KEY.dateStart, dateStart);
                }
                break;
            case 'dateEnd':
                if (dateEnd) {
                    params.set(SINGLE_KEY.dateEnd, dateEnd);
                }
                break;
            case 'pointsMin':
                if (pointsMin) {
                    params.set(SINGLE_KEY.pointsMin, pointsMin);
                }
                break;
            case 'pointsMax':
                if (pointsMax) {
                    params.set(SINGLE_KEY.pointsMax, pointsMax);
                }
                break;
            case 'loadoutMin':
                if (loadoutMin) {
                    params.set(SINGLE_KEY.loadoutMin, loadoutMin);
                }
                break;
            case 'loadoutMax':
                if (loadoutMax) {
                    params.set(SINGLE_KEY.loadoutMax, loadoutMax);
                }
                break;
            case 'isUnique':
                if (isUnique) {
                    params.set(SINGLE_KEY.isUnique, 'true');
                }
                break;
            case 'isLimited':
                if (isLimited) {
                    params.set(SINGLE_KEY.isLimited, 'true');
                }
                break;
            case 'isGeneric':
                if (isGeneric) {
                    params.set(SINGLE_KEY.isGeneric, 'true');
                }
                break;
            case 'sortBy':
                if (sortBy) {
                    params.set(SINGLE_KEY.sortBy, sortBy);
                }
                break;
            case 'sortDirection':
                if (sortDirection !== 'desc') {
                    params.set(SINGLE_KEY.sortDirection, sortDirection);
                }
                break;
            // Multi-value fields
            case 'selectedFormats':
                for (const f of selectedFormats) {
                    params.append(SINGLE_KEY.selectedFormats, f);
                }
                break;
            case 'selectedFactions':
                for (const f of selectedFactions) {
                    params.append(SINGLE_KEY.selectedFactions, f);
                }
                break;
            case 'selectedShips':
                for (const s of selectedShips) {
                    params.append(SINGLE_KEY.selectedShips, s);
                }
                break;
            case 'selectedSources':
                for (const p of selectedSources) {
                    params.append(SINGLE_KEY.selectedSources, p);
                }
                break;
            case 'selectedContinents':
                for (const c of selectedContinents) {
                    params.append(SINGLE_KEY.selectedContinents, c);
                }
                break;
            case 'selectedCountries':
                for (const c of selectedCountries) {
                    params.append(SINGLE_KEY.selectedCountries, c);
                }
                break;
            case 'selectedCities':
                for (const c of selectedCities) {
                    params.append(SINGLE_KEY.selectedCities, c);
                }
                break;
            case 'selectedBaseSizes':
                for (const b of selectedBaseSizes) {
                    params.append(SINGLE_KEY.selectedBaseSizes, b);
                }
                break;
        }
    }

    return params;
}

/**
 * Apply URL parameters to the store. Only fields present in `params` are
 * updated; absent fields are left untouched, which preserves the "filters
 * carry across routes" behavior. Boolean values are parsed from the string
 * `'true'`.
 */
function applyFromSearchParams(params: URLSearchParams): void {
    // Single-value fields
    const dataSourceVal = params.get('data_source');
    if (dataSourceVal === 'xwa' || dataSourceVal === 'legacy') {
        dataSource = dataSourceVal;
    }

    if (params.has('epic')) {
        includeEpic = params.get('epic') === 'true';
    }
    if (params.has('search')) {
        const v = params.get('search') ?? '';
        if (v) searchName = v;
    }
    if (params.has('date_start')) {
        const v = params.get('date_start') ?? '';
        if (v) dateStart = v;
    }
    if (params.has('date_end')) {
        const v = params.get('date_end') ?? '';
        if (v) dateEnd = v;
    }
    if (params.has('points_min')) {
        const v = params.get('points_min') ?? '';
        if (v) pointsMin = v;
    }
    if (params.has('points_max')) {
        const v = params.get('points_max') ?? '';
        if (v) pointsMax = v;
    }
    if (params.has('loadout_min')) {
        const v = params.get('loadout_min') ?? '';
        if (v) loadoutMin = v;
    }
    if (params.has('loadout_max')) {
        const v = params.get('loadout_max') ?? '';
        if (v) loadoutMax = v;
    }
    if (params.has('is_unique')) {
        isUnique = params.get('is_unique') === 'true';
    }
    if (params.has('is_limited')) {
        isLimited = params.get('is_limited') === 'true';
    }
    if (params.has('is_not_limited')) {
        isGeneric = params.get('is_not_limited') === 'true';
    }
    if (params.has('sort_metric')) {
        const v = params.get('sort_metric') ?? '';
        if (v) sortBy = v;
    }
    if (params.has('sort_direction')) {
        const v = params.get('sort_direction');
        if (v === 'asc' || v === 'desc') {
            sortDirection = v;
        }
    }

    // Multi-value fields
    const formats = params.getAll('formats');
    if (formats.length > 0) {
        // Defensive guard against a stale-URL race condition.
        //
        // The layout's `$effect` calls `applyFromSearchParams` on
        // every URL change. But the `+page.svelte` `$effect` writes
        // the URL via a debounced `scheduleSync`, so there is a
        // window in which the user has just mutated the store but the
        // URL has not been updated yet. If the layout's effect re-runs
        // during that window, it reads the STALE URL and would
        // clobber the user's mutation.
        //
        // `isPendingSync()` returns `true` while such a sync is in
        // flight. When it is, we skip the write — the store is the
        // source of truth and the URL will catch up. Once the URL
        // actually changes to match the store, we call
        // `resolvePendingSync()` to clear the flag so the NEXT URL
        // change (a real navigation) hydrates the store normally.
        if (isPendingSync()) {
            // Stale URL: trust the store, do not overwrite.
        } else {
            // No sync in flight — either initial hydration or a real
            // navigation. Hydrate the store from the URL.
            selectedFormats = formats;
        }
    } else {
        // URL has no `formats` — could be a navigation to a page
        // without filters, or the post-`resolvePendingSync` case
        // where the URL now matches the store. Either way, only
        // clear the store if there isn't a sync in flight.
        if (!isPendingSync() && selectedFormats.length > 0) {
            selectedFormats = [];
        }
    }

    // If a sync was pending, check whether the URL we just observed
    // matches the store's current state. If so, the sync has landed
    // and we can clear the pending flag. If not, keep the flag so the
    // next layout re-run (with the freshly-updated URL) will still
    // skip overwriting.
    if (isPendingSync()) {
        const currentUrlFormats = formats;
        let matches = currentUrlFormats.length === selectedFormats.length;
        if (matches) {
            for (let i = 0; i < currentUrlFormats.length; i++) {
                if (currentUrlFormats[i] !== selectedFormats[i]) {
                    matches = false;
                    break;
                }
            }
        }
        if (matches) {
            resolvePendingSync();
        }
    } else {
        // No pending sync — this is the very first hydration after
        // page load, or a real navigation. Either way, the store has
        // now been synchronised with the URL at this point in time,
        // so future syncs can safely be guarded.
        markHydrated();
    }
    const factions = params.getAll('factions');
    if (factions.length > 0) selectedFactions = factions;
    const ships = params.getAll('ships');
    if (ships.length > 0) selectedShips = ships;
    const sources = params.getAll('sources');
    if (sources.length > 0) selectedSources = sources;
    const continents = params.getAll('continent');
    if (continents.length > 0) selectedContinents = continents;
    const countries = params.getAll('country');
    if (countries.length > 0) selectedCountries = countries;
    const cities = params.getAll('city');
    if (cities.length > 0) selectedCities = cities;
    const baseSizes = params.getAll('base_sizes');
    if (baseSizes.length > 0) selectedBaseSizes = baseSizes;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export const filters = {
    get dataSource() { return dataSource; },
    set dataSource(v: 'xwa' | 'legacy') {
        dataSource = v;
        if (v === 'xwa') {
            selectedFormats = ['xwa'];
        } else if (v === 'legacy') {
            selectedFormats = ['legacy_x2po'];
        }
    },
    get includeEpic() { return includeEpic; },
    set includeEpic(v: boolean) { includeEpic = v; },
    get dateStart() { return dateStart; },
    set dateStart(v: string) { dateStart = v; },
    get dateEnd() { return dateEnd; },
    set dateEnd(v: string) { dateEnd = v; },
    get selectedContinents() { return selectedContinents; },
    set selectedContinents(v: string[]) { selectedContinents = v; },
    get selectedCountries() { return selectedCountries; },
    set selectedCountries(v: string[]) { selectedCountries = v; },
    get selectedCities() { return selectedCities; },
    set selectedCities(v: string[]) { selectedCities = v; },
    get selectedFormats() { return selectedFormats; },
    set selectedFormats(v: string[]) { selectedFormats = v; },
    get searchName() { return searchName; },
    set searchName(v: string) { searchName = v; },
    get selectedSources() { return selectedSources; },
    set selectedSources(v: string[]) { selectedSources = v; },
    get selectedShips() { return selectedShips; },
    set selectedShips(v: string[]) { selectedShips = v; },
    get selectedFactions() { return selectedFactions; },
    set selectedFactions(v: string[]) { selectedFactions = v; },
    get sortBy() { return sortBy; },
    set sortBy(v: string) { sortBy = v; },
    get sortDirection() { return sortDirection; },
    set sortDirection(v: 'asc' | 'desc') { sortDirection = v; },
    // Adv
    get pointsMin() { return pointsMin; }, set pointsMin(v: string) { pointsMin = v; },
    get pointsMax() { return pointsMax; }, set pointsMax(v: string) { pointsMax = v; },
    get loadoutMin() { return loadoutMin; }, set loadoutMin(v: string) { loadoutMin = v; },
    get loadoutMax() { return loadoutMax; }, set loadoutMax(v: string) { loadoutMax = v; },
    get isUnique() { return isUnique; }, set isUnique(v: boolean) { isUnique = v; },
    get isLimited() { return isLimited; }, set isLimited(v: boolean) { isLimited = v; },
    get isGeneric() { return isGeneric; }, set isGeneric(v: boolean) { isGeneric = v; },
    get selectedBaseSizes() { return selectedBaseSizes; }, set selectedBaseSizes(v: string[]) { selectedBaseSizes = v; },
    get initMin() { return initMin; }, set initMin(v: string) { initMin = v; },
    get initMax() { return initMax; }, set initMax(v: string) { initMax = v; },
    get hullMin() { return hullMin; }, set hullMin(v: string) { hullMin = v; },
    get hullMax() { return hullMax; }, set hullMax(v: string) { hullMax = v; },
    get shieldsMin() { return shieldsMin; }, set shieldsMin(v: string) { shieldsMin = v; },
    get shieldsMax() { return shieldsMax; }, set shieldsMax(v: string) { shieldsMax = v; },
    get agilityMin() { return agilityMin; }, set agilityMin(v: string) { agilityMin = v; },
    get agilityMax() { return agilityMax; }, set agilityMax(v: string) { agilityMax = v; },
    get attackMin() { return attackMin; }, set attackMin(v: string) { attackMin = v; },
    get attackMax() { return attackMax; }, set attackMax(v: string) { attackMax = v; },
    // End Adv
    /** Memoized chip descriptors for every non-default filter. */
    get activeChips() { return activeChips; },
    removeChip,
    resetAll,
    /** Serialize the current store to a per-route URLSearchParams. */
    toSearchParams,
    /** Apply URL params to the store. Only present keys are updated. */
    applyFromSearchParams,
};
