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
// Pilot filter (lists page) + matching mode for multi-value filters
let selectedPilots = $state<string[]>([]);
let pilotFilterMode = $state<'any' | 'all'>('any');
let shipFilterMode = $state<'any' | 'all'>('any');
// Stat ranges — applied post-aggregation on the visible rows
// (AND between different stats, like other facets). Empty = no bound.
let listsMin = $state('');
let listsMax = $state('');
let entriesMin = $state('');
let entriesMax = $state('');
let gamesMin = $state('');
let gamesMax = $state('');
let winRateMin = $state('');
let winRateMax = $state('');

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
    for (const p of selectedPilots) chips.push({ key: `pilot:${p}`, label: `Pilot: ${p}` });
    if (pilotFilterMode === 'all' && selectedPilots.length > 1) chips.push({ key: 'pilotMode', label: 'Pilots: All' });
    if (shipFilterMode === 'all' && selectedShips.length > 1) chips.push({ key: 'shipMode', label: 'Ships: All' });
    if (listsMin || listsMax) chips.push({ key: 'listsRange', label: `Lists: ${listsMin || '0'}–${listsMax || '∞'}` });
    if (entriesMin || entriesMax) chips.push({ key: 'entriesRange', label: `Entries: ${entriesMin || '0'}–${entriesMax || '∞'}` });
    if (gamesMin || gamesMax) chips.push({ key: 'gamesRange', label: `Games: ${gamesMin || '0'}–${gamesMax || '∞'}` });
    if (winRateMin || winRateMax) chips.push({ key: 'winRateRange', label: `WR: ${winRateMin || '0'}–${winRateMax || '100'}%` });

    const effectiveFormats = selectedFormats.length > 0 ? selectedFormats : defaultFormatsForSource(dataSource);
    for (const f of effectiveFormats) {
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
    else if (key.startsWith('pilot:'))
        selectedPilots = selectedPilots.filter(p => p !== key.slice(6));
    else if (key === 'pilotMode') pilotFilterMode = 'any';
    else if (key === 'shipMode') shipFilterMode = 'any';
    else if (key === 'listsRange') { listsMin = ''; listsMax = ''; }
    else if (key === 'entriesRange') { entriesMin = ''; entriesMax = ''; }
    else if (key === 'gamesRange') { gamesMin = ''; gamesMax = ''; }
    else if (key === 'winRateRange') { winRateMin = ''; winRateMax = ''; }
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
    selectedPilots = [];
    pilotFilterMode = 'any';
    shipFilterMode = 'any';
    listsMin = ''; listsMax = '';
    entriesMin = ''; entriesMax = '';
    gamesMin = ''; gamesMax = '';
    winRateMin = ''; winRateMax = '';

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
    | 'selectedPilots'
    | 'pilotFilterMode'
    | 'shipFilterMode'
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
    | 'listsMin'
    | 'listsMax'
    | 'entriesMin'
    | 'entriesMax'
    | 'gamesMin'
    | 'gamesMax'
    | 'winRateMin'
    | 'winRateMax'
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
        'shipFilterMode',
        'selectedPilots',
        'pilotFilterMode',
        'selectedSources',
        'selectedContinents',
        'selectedCountries',
        'selectedCities',
        'dateStart',
        'dateEnd',
        'listsMin',
        'listsMax',
        'entriesMin',
        'entriesMax',
        'gamesMin',
        'gamesMax',
        'winRateMin',
        'winRateMax',
        'sortBy',
        'sortDirection',
    ],
    ships: [
        'dataSource',
        'includeEpic',
        'selectedFormats',
        'selectedFactions',
        'selectedShips',
        'shipFilterMode',
        'selectedSources',
        'selectedContinents',
        'selectedCountries',
        'selectedCities',
        'dateStart',
        'dateEnd',
        'listsMin',
        'listsMax',
        'entriesMin',
        'entriesMax',
        'gamesMin',
        'gamesMax',
        'winRateMin',
        'winRateMax',
        'sortBy',
        'sortDirection',
    ],
    squadrons: [
        'dataSource',
        'includeEpic',
        'selectedFormats',
        'selectedFactions',
        'selectedShips',
        'shipFilterMode',
        'selectedSources',
        'selectedContinents',
        'selectedCountries',
        'selectedCities',
        'dateStart',
        'dateEnd',
        'listsMin',
        'listsMax',
        'entriesMin',
        'entriesMax',
        'gamesMin',
        'gamesMax',
        'winRateMin',
        'winRateMax',
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
    pilotFilterMode: 'pilot_mode',
    shipFilterMode: 'ship_mode',
    listsMin: 'lists_min',
    listsMax: 'lists_max',
    entriesMin: 'entries_min',
    entriesMax: 'entries_max',
    gamesMin: 'games_min',
    gamesMax: 'games_max',
    winRateMin: 'win_rate_min',
    winRateMax: 'win_rate_max',
    // Multi-value fields — these use `params.append` and a fixed URL key:
    selectedFormats: 'formats',
    selectedFactions: 'factions',
    selectedShips: 'ships',
    selectedSources: 'sources',
    selectedContinents: 'continent',
    selectedCountries: 'country',
    selectedCities: 'city',
    selectedBaseSizes: 'base_sizes',
    selectedPilots: 'pilots',
};

/**

 * URL key used for `selectedSources` per route. The lists/ships/cards/
 * squadrons backends accept the `platforms` parameter; the tournaments
 * backend accepts `sources`. Emitting the wrong key means the backend
 * silently ignores the filter.
 */
const SOURCE_KEY_BY_ROUTE: Record<RouteId, string> = {
    cards: 'platforms',
    lists: 'platforms',
    ships: 'platforms',
    squadrons: 'platforms',
    tournaments: 'sources',
};

/** Base formats for a data source (matching the `dataSource` setter). */
function defaultFormatsForSource(source: 'xwa' | 'legacy'): string[] {
    return source === 'xwa' ? ['xwa'] : ['legacy_x2po'];
}


/**
 * Serialize the current filter state to a `URLSearchParams` containing ONLY
 * the fields the given route supports. Default values are omitted, multi-
 * value fields use repeated keys, and the key order is deterministic.
 *
 * `selectedFormats` is always written in full (even when it matches the
 * current `dataSource` default) so the URL round-trips cleanly with
 * `applyFromSearchParams` and multi-select stays stable across re-renders.
 * When the "Include Epic" toggle is on, the route's epic format variant(s)
 * are added to the emitted formats (see `resolveFormats`).
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
            case 'pilotFilterMode':
                if (pilotFilterMode === 'all') params.set(SINGLE_KEY.pilotFilterMode, 'all');
                break;
            case 'shipFilterMode':
                if (shipFilterMode === 'all') params.set(SINGLE_KEY.shipFilterMode, 'all');
                break;
            case 'listsMin':
                if (listsMin) params.set(SINGLE_KEY.listsMin, listsMin);
                break;
            case 'listsMax':
                if (listsMax) params.set(SINGLE_KEY.listsMax, listsMax);
                break;
            case 'entriesMin':
                if (entriesMin) params.set(SINGLE_KEY.entriesMin, entriesMin);
                break;
            case 'entriesMax':
                if (entriesMax) params.set(SINGLE_KEY.entriesMax, entriesMax);
                break;
            case 'gamesMin':
                if (gamesMin) params.set(SINGLE_KEY.gamesMin, gamesMin);
                break;
            case 'gamesMax':
                if (gamesMax) params.set(SINGLE_KEY.gamesMax, gamesMax);
                break;
            case 'winRateMin':
                if (winRateMin) params.set(SINGLE_KEY.winRateMin, winRateMin);
                break;
            case 'winRateMax':
                if (winRateMax) params.set(SINGLE_KEY.winRateMax, winRateMax);
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
            case 'selectedFormats': {
                const formats = selectedFormats.length > 0 ? selectedFormats : defaultFormatsForSource(dataSource);
                for (const f of formats) {
                    params.append(SINGLE_KEY.selectedFormats, f);
                }
                break;
            }
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
            case 'selectedPilots':
                for (const p of selectedPilots) {
                    params.append('pilots', p);
                }
                break;
            case 'selectedSources':
                for (const p of selectedSources) {
                    params.append(SOURCE_KEY_BY_ROUTE[routeId], p);
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
    const dataSourceVal = params.get('data_source');
    dataSource = dataSourceVal === 'legacy' ? 'legacy' : 'xwa';

    includeEpic = params.get('epic') === 'true';
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
    if (params.has('pilot_mode')) {
        const v = params.get('pilot_mode');
        if (v === 'all' || v === 'any') pilotFilterMode = v;
    }
    if (params.has('ship_mode')) {
        const v = params.get('ship_mode');
        if (v === 'all' || v === 'any') shipFilterMode = v;
    }
    if (params.has('lists_min')) {
        const v = params.get('lists_min') ?? '';
        if (v) listsMin = v;
    }
    if (params.has('lists_max')) {
        const v = params.get('lists_max') ?? '';
        if (v) listsMax = v;
    }
    if (params.has('entries_min')) {
        const v = params.get('entries_min') ?? '';
        if (v) entriesMin = v;
    }
    if (params.has('entries_max')) {
        const v = params.get('entries_max') ?? '';
        if (v) entriesMax = v;
    }
    if (params.has('games_min')) {
        const v = params.get('games_min') ?? '';
        if (v) gamesMin = v;
    }
    if (params.has('games_max')) {
        const v = params.get('games_max') ?? '';
        if (v) gamesMax = v;
    }
    if (params.has('win_rate_min')) {
        const v = params.get('win_rate_min') ?? '';
        if (v) winRateMin = v;
    }
    if (params.has('win_rate_max')) {
        const v = params.get('win_rate_max') ?? '';
        if (v) winRateMax = v;
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
    const platforms = params.getAll('platforms');
    if (sources.length > 0) selectedSources = sources;
    else if (platforms.length > 0) selectedSources = platforms;
    const continents = params.getAll('continent');
    if (continents.length > 0) selectedContinents = continents;
    const countries = params.getAll('country');
    if (countries.length > 0) selectedCountries = countries;
    const cities = params.getAll('city');
    if (cities.length > 0) selectedCities = cities;
    const baseSizes = params.getAll('base_sizes');
    if (baseSizes.length > 0) selectedBaseSizes = baseSizes;
    const pilots = params.getAll('pilots');
    if (pilots.length > 0) selectedPilots = pilots;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------


// ---------------------------------------------------------------------------
// Per-route local filter persistence (dataset stays global, local is per page)
// ---------------------------------------------------------------------------

const LOCAL_KEYS_BY_ROUTE: Record<RouteId, string[]> = {
    cards: ['selectedFactions','selectedShips','searchName','pointsMin','pointsMax','loadoutMin','loadoutMax','isUnique','isLimited','isGeneric','selectedBaseSizes','initMin','initMax','hullMin','hullMax','shieldsMin','shieldsMax','agilityMin','agilityMax','attackMin','attackMax','listsMin','listsMax','entriesMin','entriesMax','gamesMin','gamesMax','winRateMin','winRateMax'],
    lists: ['selectedFactions','selectedShips','selectedPilots','pilotFilterMode','shipFilterMode','listsMin','listsMax','entriesMin','entriesMax','gamesMin','gamesMax','winRateMin','winRateMax'],
    ships: ['selectedFactions','selectedShips','shipFilterMode','listsMin','listsMax','entriesMin','entriesMax','gamesMin','gamesMax','winRateMin','winRateMax'],
    squadrons: ['selectedFactions','selectedShips','shipFilterMode','listsMin','listsMax','entriesMin','entriesMax','gamesMin','gamesMax','winRateMin','winRateMax'],
    tournaments: ['searchName'],
};

function localStorageKey(route: RouteId): string { return `m3tacron:localFilters:${route}`; }

function snapshotLocal(route: RouteId): Record<string, unknown> {
    const keys = LOCAL_KEYS_BY_ROUTE[route] ?? [];
    const out: Record<string, unknown> = {};
    for (const k of keys) {
        switch (k) {
            case 'selectedFactions': out[k] = [...selectedFactions]; break;
            case 'selectedShips': out[k] = [...selectedShips]; break;
            case 'selectedPilots': out[k] = [...selectedPilots]; break;
            case 'pilotFilterMode': out[k] = pilotFilterMode; break;
            case 'shipFilterMode': out[k] = shipFilterMode; break;
            case 'searchName': out[k] = searchName; break;
            case 'pointsMin': out[k] = pointsMin; break;
            case 'pointsMax': out[k] = pointsMax; break;
            case 'loadoutMin': out[k] = loadoutMin; break;
            case 'loadoutMax': out[k] = loadoutMax; break;
            case 'isUnique': out[k] = isUnique; break;
            case 'isLimited': out[k] = isLimited; break;
            case 'isGeneric': out[k] = isGeneric; break;
            case 'selectedBaseSizes': out[k] = [...selectedBaseSizes]; break;
            case 'initMin': out[k] = initMin; break;
            case 'initMax': out[k] = initMax; break;
            case 'hullMin': out[k] = hullMin; break;
            case 'hullMax': out[k] = hullMax; break;
            case 'shieldsMin': out[k] = shieldsMin; break;
            case 'shieldsMax': out[k] = shieldsMax; break;
            case 'agilityMin': out[k] = agilityMin; break;
            case 'agilityMax': out[k] = agilityMax; break;
            case 'attackMin': out[k] = attackMin; break;
            case 'attackMax': out[k] = attackMax; break;
            case 'listsMin': out[k] = listsMin; break;
            case 'listsMax': out[k] = listsMax; break;
            case 'entriesMin': out[k] = entriesMin; break;
            case 'entriesMax': out[k] = entriesMax; break;
            case 'gamesMin': out[k] = gamesMin; break;
            case 'gamesMax': out[k] = gamesMax; break;
            case 'winRateMin': out[k] = winRateMin; break;
            case 'winRateMax': out[k] = winRateMax; break;
        }
    }
    return out;
}

function applyLocalSnapshot(route: RouteId, snap: Record<string, unknown>): void {
    const has = (k: string) => snap[k] !== undefined;
    if (has('selectedFactions') && Array.isArray(snap['selectedFactions'])) selectedFactions = snap['selectedFactions'] as string[];
    if (has('selectedShips') && Array.isArray(snap['selectedShips'])) selectedShips = snap['selectedShips'] as string[];
    if (has('selectedPilots') && Array.isArray(snap['selectedPilots'])) selectedPilots = snap['selectedPilots'] as string[];
    if (has('pilotFilterMode') && (snap['pilotFilterMode']==='any'||snap['pilotFilterMode']==='all')) pilotFilterMode = snap['pilotFilterMode'] as 'any'|'all';
    if (has('shipFilterMode') && (snap['shipFilterMode']==='any'||snap['shipFilterMode']==='all')) shipFilterMode = snap['shipFilterMode'] as 'any'|'all';
    if (has('searchName') && typeof snap['searchName']==='string') searchName = snap['searchName'] as string;
    if (has('pointsMin') && typeof snap['pointsMin']==='string') pointsMin = snap['pointsMin'] as string;
    if (has('pointsMax') && typeof snap['pointsMax']==='string') pointsMax = snap['pointsMax'] as string;
    if (has('loadoutMin') && typeof snap['loadoutMin']==='string') loadoutMin = snap['loadoutMin'] as string;
    if (has('loadoutMax') && typeof snap['loadoutMax']==='string') loadoutMax = snap['loadoutMax'] as string;
    if (has('isUnique') && typeof snap['isUnique']==='boolean') isUnique = snap['isUnique'] as boolean;
    if (has('isLimited') && typeof snap['isLimited']==='boolean') isLimited = snap['isLimited'] as boolean;
    if (has('isGeneric') && typeof snap['isGeneric']==='boolean') isGeneric = snap['isGeneric'] as boolean;
    if (has('selectedBaseSizes') && Array.isArray(snap['selectedBaseSizes'])) selectedBaseSizes = snap['selectedBaseSizes'] as string[];
    if (has('initMin') && typeof snap['initMin']==='string') initMin = snap['initMin'] as string;
    if (has('initMax') && typeof snap['initMax']==='string') initMax = snap['initMax'] as string;
    if (has('hullMin') && typeof snap['hullMin']==='string') hullMin = snap['hullMin'] as string;
    if (has('hullMax') && typeof snap['hullMax']==='string') hullMax = snap['hullMax'] as string;
    if (has('shieldsMin') && typeof snap['shieldsMin']==='string') shieldsMin = snap['shieldsMin'] as string;
    if (has('shieldsMax') && typeof snap['shieldsMax']==='string') shieldsMax = snap['shieldsMax'] as string;
    if (has('agilityMin') && typeof snap['agilityMin']==='string') agilityMin = snap['agilityMin'] as string;
    if (has('agilityMax') && typeof snap['agilityMax']==='string') agilityMax = snap['agilityMax'] as string;
    if (has('attackMin') && typeof snap['attackMin']==='string') attackMin = snap['attackMin'] as string;
    if (has('attackMax') && typeof snap['attackMax']==='string') attackMax = snap['attackMax'] as string;
    if (has('listsMin') && typeof snap['listsMin']==='string') listsMin = snap['listsMin'] as string;
    if (has('listsMax') && typeof snap['listsMax']==='string') listsMax = snap['listsMax'] as string;
    if (has('entriesMin') && typeof snap['entriesMin']==='string') entriesMin = snap['entriesMin'] as string;
    if (has('entriesMax') && typeof snap['entriesMax']==='string') entriesMax = snap['entriesMax'] as string;
    if (has('gamesMin') && typeof snap['gamesMin']==='string') gamesMin = snap['gamesMin'] as string;
    if (has('gamesMax') && typeof snap['gamesMax']==='string') gamesMax = snap['gamesMax'] as string;
    if (has('winRateMin') && typeof snap['winRateMin']==='string') winRateMin = snap['winRateMin'] as string;
    if (has('winRateMax') && typeof snap['winRateMax']==='string') winRateMax = snap['winRateMax'] as string;
}

function saveLocalFilters(route: RouteId): void {
    if (typeof localStorage === 'undefined') return;
    try { localStorage.setItem(localStorageKey(route), JSON.stringify(snapshotLocal(route))); } catch(e){ console.warn('saveLocalFilters failed', e); }
}

function restoreLocalFilters(route: RouteId, urlParams: URLSearchParams): void {
    if (typeof localStorage === 'undefined') return;
    const hasLocalInUrl = LOCAL_KEYS_BY_ROUTE[route]?.some(k => {
        const urlKey = (SINGLE_KEY as unknown as Record<string,string>)[k];
        if (!urlKey) return urlParams.has(k) || urlParams.has('pilots') || urlParams.has('factions') || urlParams.has('ships');
        return urlParams.has(urlKey) || (k==='selectedFactions' && urlParams.has('factions')) || (k==='selectedShips' && urlParams.has('ships')) || (k==='selectedPilots' && urlParams.has('pilots'));
    });
    if (hasLocalInUrl) return;
    try {
        const raw = localStorage.getItem(localStorageKey(route));
        if (!raw) {
            // No saved state for this route and no URL params -> clear this route's local keys so previous page's values don't bleed
            const empty: Record<string, unknown> = {};
            for (const k of (LOCAL_KEYS_BY_ROUTE[route] ?? [])) {
                if (k==='selectedFactions' || k==='selectedShips' || k==='selectedPilots' || k==='selectedBaseSizes') empty[k] = [];
                else if (k==='pilotFilterMode' || k==='shipFilterMode') empty[k] = 'any';
                else if (k==='isUnique' || k==='isLimited' || k==='isGeneric') empty[k] = false;
                else empty[k] = '';
            }
            applyLocalSnapshot(route, empty);
            return;
        }
        const snap = JSON.parse(raw) as Record<string, unknown>;
        applyLocalSnapshot(route, snap);
    } catch(e){ console.warn('restoreLocalFilters failed', e); }
}


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
    set includeEpic(v: boolean) {
        includeEpic = v;
    },
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
    get selectedPilots() { return selectedPilots; },
    set selectedPilots(v: string[]) { selectedPilots = v; },
    get pilotFilterMode() { return pilotFilterMode; },
    set pilotFilterMode(v: 'any' | 'all') { pilotFilterMode = v; },
    get shipFilterMode() { return shipFilterMode; },
    set shipFilterMode(v: 'any' | 'all') { shipFilterMode = v; },
    get listsMin() { return listsMin; },
    set listsMin(v: string) { listsMin = v; },
    get listsMax() { return listsMax; },
    set listsMax(v: string) { listsMax = v; },
    get entriesMin() { return entriesMin; },
    set entriesMin(v: string) { entriesMin = v; },
    get entriesMax() { return entriesMax; },
    set entriesMax(v: string) { entriesMax = v; },
    get gamesMin() { return gamesMin; },
    set gamesMin(v: string) { gamesMin = v; },
    get gamesMax() { return gamesMax; },
    set gamesMax(v: string) { gamesMax = v; },
    get winRateMin() { return winRateMin; },
    set winRateMin(v: string) { winRateMin = v; },
    get winRateMax() { return winRateMax; },
    set winRateMax(v: string) { winRateMax = v; },
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
    saveLocalFilters,
    restoreLocalFilters,
    /** Memoized chip descriptors for every non-default filter. */
    get activeChips() { return activeChips; },
    removeChip,
    resetAll,
    /** Serialize the current store to a per-route URLSearchParams. */
    toSearchParams,
    /** Apply URL params to the store. Only present keys are updated. */
    applyFromSearchParams,
};
