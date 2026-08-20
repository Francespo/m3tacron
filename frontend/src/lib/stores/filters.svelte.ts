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
// NOTE FOR THE FILTERPANEL RESTRUCTURE LANE: these fields are owned by the
// cards-page workstream. They are named to be cards-scoped and distinct from
// the global/tournament fields above (`searchName` = tournament-name search,
// URL key `search`; `cardText` = card text search, URL key `text`). When you
// restructure the global FilterPanel, keep these names as-is.
let cardText = $state(''); // Card text search — decoupled from searchName.
let pointsMin = $state('');
let pointsMax = $state('');
let loadoutMin = $state('');
let loadoutMax = $state('');
let isUnique = $state(false);
let isLimited = $state(false);
let isStandardLegal = $state(false); // Replaces the old "Generic" (is_not_limited) toggle.
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

// Advanced — Ships & Pilots (pilots tab)
let selectedSlots = $state<string[]>([]); // upgrade slots on the pilot
let selectedKeywords = $state<string[]>([]);
let selectedActions = $state<string[]>([]);
let selectedLinkedActions = $state<string[]>([]);
let selectedArcs = $state<string[]>([]); // attack arc icons

// Advanced — Upgrades (upgrades tab)
let selectedUpgradeTypes = $state<string[]>([]); // "used slot" multi-select
let isDoubleSlot = $state(false);
let isRecurring = $state(false);
let chargesMin = $state('');
let chargesMax = $state('');
let forceMin = $state('');
let forceMax = $state('');

// Advanced — Data (stat ranges, both tabs; basic-mode "min games" / "min
// decks" share gamesMin / listsMin).
let gamesMin = $state('');
let gamesMax = $state('');
let listsMin = $state('');
let listsMax = $state('');
let uniqueListsMin = $state('');
let uniqueListsMax = $state('');
let winRateMin = $state('');
let winRateMax = $state('');

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
    if (cardText) chips.push({ key: 'text', label: `Text: "${cardText}"` });

    // Advanced Chips
    if (pointsMin || pointsMax) chips.push({ key: 'points', label: `Pts: ${pointsMin || 0}-${pointsMax || '∞'}` });
    if (loadoutMin || loadoutMax) chips.push({ key: 'loadout', label: `LV: ${loadoutMin || 0}-${loadoutMax || '∞'}` });
    if (isUnique) chips.push({ key: 'isUnique', label: 'Unique' });
    if (isLimited) chips.push({ key: 'isLimited', label: 'Limited' });
    if (isStandardLegal) chips.push({ key: 'isStandardLegal', label: 'Standard-legal' });
    for (const b of selectedBaseSizes) chips.push({ key: `base:${b}`, label: `Base: ${b}` });

    if (initMin || initMax) chips.push({ key: 'init', label: `Init: ${initMin || 0}-${initMax || 6}` });
    if (hullMin || hullMax) chips.push({ key: 'hull', label: `Hull: ${hullMin || 0}-${hullMax || '∞'}` });
    if (shieldsMin || shieldsMax) chips.push({ key: 'shields', label: `Shields: ${shieldsMin || 0}-${shieldsMax || '∞'}` });
    if (agilityMin || agilityMax) chips.push({ key: 'agility', label: `Agility: ${agilityMin || 0}-${agilityMax || 3}` });
    if (attackMin || attackMax) chips.push({ key: 'attack', label: `Attack: ${attackMin || 0}-${attackMax || '∞'}` });

    // Ships & Pilots / Upgrades
    for (const s of selectedSlots) chips.push({ key: `slot:${s}`, label: `Slot: ${s}` });
    for (const k of selectedKeywords) chips.push({ key: `keyword:${k}`, label: `Keyword: ${k}` });
    for (const a of selectedActions) chips.push({ key: `action:${a}`, label: `Action: ${a}` });
    for (const l of selectedLinkedActions) chips.push({ key: `linked:${l}`, label: `Linked: ${l}` });
    for (const a of selectedArcs) chips.push({ key: `arc:${a}`, label: `Arc: ${a}` });
    for (const t of selectedUpgradeTypes) chips.push({ key: `upgradeType:${t}`, label: `Slot: ${t}` });
    if (isDoubleSlot) chips.push({ key: 'isDoubleSlot', label: 'Double-slot' });
    if (isRecurring) chips.push({ key: 'isRecurring', label: 'Recurring charges' });
    if (chargesMin || chargesMax) chips.push({ key: 'charges', label: `Charges: ${chargesMin || 0}-${chargesMax || '∞'}` });
    if (forceMin || forceMax) chips.push({ key: 'force', label: `Force: ${forceMin || 0}-${forceMax || '∞'}` });

    // Data group
    if (gamesMin || gamesMax) chips.push({ key: 'games', label: `Games: ${gamesMin || 0}-${gamesMax || '∞'}` });
    if (listsMin || listsMax) chips.push({ key: 'lists', label: `Lists: ${listsMin || 0}-${listsMax || '∞'}` });
    if (uniqueListsMin || uniqueListsMax) chips.push({ key: 'uniqueLists', label: `Unique lists: ${uniqueListsMin || 0}-${uniqueListsMax || '∞'}` });
    if (winRateMin || winRateMax) chips.push({ key: 'winRate', label: `Win rate: ${winRateMin || 0}-${winRateMax || '∞'}%` });

    return chips;
}

function removeChip(key: string) {
    if (key === 'dateStart') dateStart = '';
    else if (key === 'dateEnd') dateEnd = '';
    else if (key === 'search') searchName = '';
    else if (key === 'text') cardText = '';
    else if (key === 'points') { pointsMin = ''; pointsMax = ''; }
    else if (key === 'loadout') { loadoutMin = ''; loadoutMax = ''; }
    else if (key === 'isUnique') isUnique = false;
    else if (key === 'isLimited') isLimited = false;
    else if (key === 'isStandardLegal') isStandardLegal = false;
    else if (key === 'init') { initMin = ''; initMax = ''; }
    else if (key === 'hull') { hullMin = ''; hullMax = ''; }
    else if (key === 'shields') { shieldsMin = ''; shieldsMax = ''; }
    else if (key === 'agility') { agilityMin = ''; agilityMax = ''; }
    else if (key === 'attack') { attackMin = ''; attackMax = ''; }
    else if (key === 'isDoubleSlot') isDoubleSlot = false;
    else if (key === 'isRecurring') isRecurring = false;
    else if (key === 'charges') { chargesMin = ''; chargesMax = ''; }
    else if (key === 'force') { forceMin = ''; forceMax = ''; }
    else if (key === 'games') { gamesMin = ''; gamesMax = ''; }
    else if (key === 'lists') { listsMin = ''; listsMax = ''; }
    else if (key === 'uniqueLists') { uniqueListsMin = ''; uniqueListsMax = ''; }
    else if (key === 'winRate') { winRateMin = ''; winRateMax = ''; }
    else if (key.startsWith('slot:'))
        selectedSlots = selectedSlots.filter(s => s !== key.slice(5));
    else if (key.startsWith('keyword:'))
        selectedKeywords = selectedKeywords.filter(k => k !== key.slice(8));
    else if (key.startsWith('action:'))
        selectedActions = selectedActions.filter(a => a !== key.slice(7));
    else if (key.startsWith('linked:'))
        selectedLinkedActions = selectedLinkedActions.filter(l => l !== key.slice(7));
    else if (key.startsWith('arc:'))
        selectedArcs = selectedArcs.filter(a => a !== key.slice(4));
    else if (key.startsWith('upgradeType:'))
        selectedUpgradeTypes = selectedUpgradeTypes.filter(t => t !== key.slice(12));
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
    cardText = '';
    pointsMin = ''; pointsMax = '';
    loadoutMin = ''; loadoutMax = '';
    isUnique = false; isLimited = false; isStandardLegal = false;
    selectedBaseSizes = [];
    initMin = ''; initMax = '';
    hullMin = ''; hullMax = '';
    shieldsMin = ''; shieldsMax = '';
    agilityMin = ''; agilityMax = '';
    attackMin = ''; attackMax = '';
    selectedSlots = [];
    selectedKeywords = [];
    selectedActions = [];
    selectedLinkedActions = [];
    selectedArcs = [];
    selectedUpgradeTypes = [];
    isDoubleSlot = false;
    isRecurring = false;
    chargesMin = ''; chargesMax = '';
    forceMin = ''; forceMax = '';
    gamesMin = ''; gamesMax = '';
    listsMin = ''; listsMax = '';
    uniqueListsMin = ''; uniqueListsMax = '';
    winRateMin = ''; winRateMax = '';
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
    | 'cardText'
    | 'pointsMin'
    | 'pointsMax'
    | 'loadoutMin'
    | 'loadoutMax'
    | 'isUnique'
    | 'isLimited'
    | 'isStandardLegal'
    | 'selectedBaseSizes'
    | 'selectedSlots'
    | 'selectedKeywords'
    | 'selectedActions'
    | 'selectedLinkedActions'
    | 'selectedArcs'
    | 'selectedUpgradeTypes'
    | 'isDoubleSlot'
    | 'isRecurring'
    | 'chargesMin'
    | 'chargesMax'
    | 'forceMin'
    | 'forceMax'
    | 'gamesMin'
    | 'gamesMax'
    | 'listsMin'
    | 'listsMax'
    | 'uniqueListsMin'
    | 'uniqueListsMax'
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
        'cardText',
        'pointsMin',
        'pointsMax',
        'loadoutMin',
        'loadoutMax',
        'isUnique',
        'isLimited',
        'isStandardLegal',
        'selectedBaseSizes',
        'selectedSlots',
        'selectedKeywords',
        'selectedActions',
        'selectedLinkedActions',
        'selectedArcs',
        'selectedUpgradeTypes',
        'isDoubleSlot',
        'isRecurring',
        'chargesMin',
        'chargesMax',
        'forceMin',
        'forceMax',
        'gamesMin',
        'gamesMax',
        'listsMin',
        'listsMax',
        'uniqueListsMin',
        'uniqueListsMax',
        'winRateMin',
        'winRateMax',
        'sortBy',
        'sortDirection',
    ],
    lists: [
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
        'sortBy',
        'sortDirection',
    ],
    ships: [
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
        'sortBy',
        'sortDirection',
    ],
    squadrons: [
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
    cardText: 'text',
    dateStart: 'date_start',
    dateEnd: 'date_end',
    pointsMin: 'points_min',
    pointsMax: 'points_max',
    loadoutMin: 'loadout_min',
    loadoutMax: 'loadout_max',
    isUnique: 'is_unique',
    isLimited: 'is_limited',
    isStandardLegal: 'is_standard_legal',
    isDoubleSlot: 'double_slot',
    isRecurring: 'is_recurring',
    chargesMin: 'charges_min',
    chargesMax: 'charges_max',
    forceMin: 'force_min',
    forceMax: 'force_max',
    gamesMin: 'games_min',
    gamesMax: 'games_max',
    listsMin: 'lists_min',
    listsMax: 'lists_max',
    uniqueListsMin: 'unique_lists_min',
    uniqueListsMax: 'unique_lists_max',
    winRateMin: 'win_rate_min',
    winRateMax: 'win_rate_max',
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
    selectedSlots: 'slots',
    selectedKeywords: 'keywords',
    selectedActions: 'actions',
    selectedLinkedActions: 'linked_actions',
    selectedArcs: 'arcs',
    selectedUpgradeTypes: 'upgrade_types',
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
            case 'cardText':
                if (cardText) {
                    params.set(SINGLE_KEY.cardText, cardText);
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
            case 'isStandardLegal':
                if (isStandardLegal) {
                    params.set(SINGLE_KEY.isStandardLegal, 'true');
                }
                break;
            case 'isDoubleSlot':
                if (isDoubleSlot) {
                    params.set(SINGLE_KEY.isDoubleSlot, 'true');
                }
                break;
            case 'isRecurring':
                if (isRecurring) {
                    params.set(SINGLE_KEY.isRecurring, 'true');
                }
                break;
            case 'chargesMin':
                if (chargesMin) {
                    params.set(SINGLE_KEY.chargesMin, chargesMin);
                }
                break;
            case 'chargesMax':
                if (chargesMax) {
                    params.set(SINGLE_KEY.chargesMax, chargesMax);
                }
                break;
            case 'forceMin':
                if (forceMin) {
                    params.set(SINGLE_KEY.forceMin, forceMin);
                }
                break;
            case 'forceMax':
                if (forceMax) {
                    params.set(SINGLE_KEY.forceMax, forceMax);
                }
                break;
            case 'gamesMin':
                if (gamesMin) {
                    params.set(SINGLE_KEY.gamesMin, gamesMin);
                }
                break;
            case 'gamesMax':
                if (gamesMax) {
                    params.set(SINGLE_KEY.gamesMax, gamesMax);
                }
                break;
            case 'listsMin':
                if (listsMin) {
                    params.set(SINGLE_KEY.listsMin, listsMin);
                }
                break;
            case 'listsMax':
                if (listsMax) {
                    params.set(SINGLE_KEY.listsMax, listsMax);
                }
                break;
            case 'uniqueListsMin':
                if (uniqueListsMin) {
                    params.set(SINGLE_KEY.uniqueListsMin, uniqueListsMin);
                }
                break;
            case 'uniqueListsMax':
                if (uniqueListsMax) {
                    params.set(SINGLE_KEY.uniqueListsMax, uniqueListsMax);
                }
                break;
            case 'winRateMin':
                if (winRateMin) {
                    params.set(SINGLE_KEY.winRateMin, winRateMin);
                }
                break;
            case 'winRateMax':
                if (winRateMax) {
                    params.set(SINGLE_KEY.winRateMax, winRateMax);
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
            case 'selectedSlots':
                for (const s of selectedSlots) {
                    params.append(SINGLE_KEY.selectedSlots, s);
                }
                break;
            case 'selectedKeywords':
                for (const k of selectedKeywords) {
                    params.append(SINGLE_KEY.selectedKeywords, k);
                }
                break;
            case 'selectedActions':
                for (const a of selectedActions) {
                    params.append(SINGLE_KEY.selectedActions, a);
                }
                break;
            case 'selectedLinkedActions':
                for (const l of selectedLinkedActions) {
                    params.append(SINGLE_KEY.selectedLinkedActions, l);
                }
                break;
            case 'selectedArcs':
                for (const a of selectedArcs) {
                    params.append(SINGLE_KEY.selectedArcs, a);
                }
                break;
            case 'selectedUpgradeTypes':
                for (const t of selectedUpgradeTypes) {
                    params.append(SINGLE_KEY.selectedUpgradeTypes, t);
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
    if (params.has('text')) {
        const v = params.get('text') ?? '';
        if (v) cardText = v;
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
    if (params.has('is_standard_legal')) {
        isStandardLegal = params.get('is_standard_legal') === 'true';
    }
    if (params.has('double_slot')) {
        isDoubleSlot = params.get('double_slot') === 'true';
    }
    if (params.has('is_recurring')) {
        isRecurring = params.get('is_recurring') === 'true';
    }
    if (params.has('charges_min')) {
        const v = params.get('charges_min') ?? '';
        if (v) chargesMin = v;
    }
    if (params.has('charges_max')) {
        const v = params.get('charges_max') ?? '';
        if (v) chargesMax = v;
    }
    if (params.has('force_min')) {
        const v = params.get('force_min') ?? '';
        if (v) forceMin = v;
    }
    if (params.has('force_max')) {
        const v = params.get('force_max') ?? '';
        if (v) forceMax = v;
    }
    if (params.has('games_min')) {
        const v = params.get('games_min') ?? '';
        if (v) gamesMin = v;
    }
    if (params.has('games_max')) {
        const v = params.get('games_max') ?? '';
        if (v) gamesMax = v;
    }
    if (params.has('lists_min')) {
        const v = params.get('lists_min') ?? '';
        if (v) listsMin = v;
    }
    if (params.has('lists_max')) {
        const v = params.get('lists_max') ?? '';
        if (v) listsMax = v;
    }
    if (params.has('unique_lists_min')) {
        const v = params.get('unique_lists_min') ?? '';
        if (v) uniqueListsMin = v;
    }
    if (params.has('unique_lists_max')) {
        const v = params.get('unique_lists_max') ?? '';
        if (v) uniqueListsMax = v;
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
    const slots = params.getAll('slots');
    if (slots.length > 0) selectedSlots = slots;
    const keywords = params.getAll('keywords');
    if (keywords.length > 0) selectedKeywords = keywords;
    const actions = params.getAll('actions');
    if (actions.length > 0) selectedActions = actions;
    const linkedActions = params.getAll('linked_actions');
    if (linkedActions.length > 0) selectedLinkedActions = linkedActions;
    const arcs = params.getAll('arcs');
    if (arcs.length > 0) selectedArcs = arcs;
    const upgradeTypes = params.getAll('upgrade_types');
    if (upgradeTypes.length > 0) selectedUpgradeTypes = upgradeTypes;
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
    // Card text search (cards page) — decoupled from searchName on purpose.
    get cardText() { return cardText; },
    set cardText(v: string) { cardText = v; },
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
    get isStandardLegal() { return isStandardLegal; }, set isStandardLegal(v: boolean) { isStandardLegal = v; },
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
    // Ships & Pilots (pilots tab)
    get selectedSlots() { return selectedSlots; }, set selectedSlots(v: string[]) { selectedSlots = v; },
    get selectedKeywords() { return selectedKeywords; }, set selectedKeywords(v: string[]) { selectedKeywords = v; },
    get selectedActions() { return selectedActions; }, set selectedActions(v: string[]) { selectedActions = v; },
    get selectedLinkedActions() { return selectedLinkedActions; }, set selectedLinkedActions(v: string[]) { selectedLinkedActions = v; },
    get selectedArcs() { return selectedArcs; }, set selectedArcs(v: string[]) { selectedArcs = v; },
    // Upgrades (upgrades tab)
    get selectedUpgradeTypes() { return selectedUpgradeTypes; }, set selectedUpgradeTypes(v: string[]) { selectedUpgradeTypes = v; },
    get isDoubleSlot() { return isDoubleSlot; }, set isDoubleSlot(v: boolean) { isDoubleSlot = v; },
    get isRecurring() { return isRecurring; }, set isRecurring(v: boolean) { isRecurring = v; },
    get chargesMin() { return chargesMin; }, set chargesMin(v: string) { chargesMin = v; },
    get chargesMax() { return chargesMax; }, set chargesMax(v: string) { chargesMax = v; },
    get forceMin() { return forceMin; }, set forceMin(v: string) { forceMin = v; },
    get forceMax() { return forceMax; }, set forceMax(v: string) { forceMax = v; },
    // Data (stat ranges)
    get gamesMin() { return gamesMin; }, set gamesMin(v: string) { gamesMin = v; },
    get gamesMax() { return gamesMax; }, set gamesMax(v: string) { gamesMax = v; },
    get listsMin() { return listsMin; }, set listsMin(v: string) { listsMin = v; },
    get listsMax() { return listsMax; }, set listsMax(v: string) { listsMax = v; },
    get uniqueListsMin() { return uniqueListsMin; }, set uniqueListsMin(v: string) { uniqueListsMin = v; },
    get uniqueListsMax() { return uniqueListsMax; }, set uniqueListsMax(v: string) { uniqueListsMax = v; },
    get winRateMin() { return winRateMin; }, set winRateMin(v: string) { winRateMin = v; },
    get winRateMax() { return winRateMax; }, set winRateMax(v: string) { winRateMax = v; },
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
