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

function getInitialDataSource(): 'xwa' | 'legacy' {
    if (typeof localStorage !== 'undefined') {
        try {
            const saved = localStorage.getItem('m3tacron:dataSource');
            if (saved === 'legacy' || saved === 'xwa') return saved;
        } catch (e) {}
    }
    return 'xwa';
}

let dataSource = $state<'xwa' | 'legacy'>(getInitialDataSource());
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
// YASB-inspired multi-value filters (pilots)
// Composite slot filter: { slot, count } entries (replaces simple selectedSlots + hasMultipleSlots)
let slotCounts = $state<string>(""); // JSON string: [{slot,count}] for stable URL sync
let slotCountMode = $state<'any' | 'all'>('any');
// Legacy flat slots still kept for backwards compat / migration
let selectedSlots = $state<string[]>([]);
let slotFilterMode = $state<'any' | 'all'>('any');
let hasMultipleSlots = $state(false);
let selectedKeywords = $state<string[]>([]);
let keywordFilterMode = $state<'any' | 'all'>('any');
// Composite action pairs: { action: string|null, linked: string|null }[] as JSON string
let actionPairs = $state<string>("");
let actionPairMode = $state<'any' | 'all'>('any');
// Legacy flat actions
let selectedActions = $state<string[]>([]);
let actionFilterMode = $state<'any' | 'all'>('any');
let selectedLinkedActions = $state<string[]>([]);
let linkedActionFilterMode = $state<'any' | 'all'>('any');
// Arc ranges — OR between arcs (grid layout)
let frontArcMin = $state('');
let frontArcMax = $state('');
let singleTurretMin = $state('');
let singleTurretMax = $state('');
let doubleTurretMin = $state('');
let doubleTurretMax = $state('');
let fullFrontMin = $state('');
let fullFrontMax = $state('');
let rearArcMin = $state('');
let rearArcMax = $state('');
let bullseyeMin = $state('');
let bullseyeMax = $state('');
// Resources
let chargesMin = $state('');
let chargesMax = $state('');
let isRecurring = $state(false);
let isNotRecurring = $state(false);
let forceMin = $state('');
let forceMax = $state('');
// Upgrade-specific
let selectedUsedSlots = $state<string[]>([]);
let usedSlotFilterMode = $state<'any' | 'all'>('any');
let selectedUsedDoubleSlots = $state<string[]>([]);
let usedDoubleSlotFilterMode = $state<'any' | 'all'>('any');
let onlyMultiSlot = $state(false);

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
    if (isUnique) chips.push({ key: 'isUnique', label: 'Unique (•)' });
    if (isLimited) chips.push({ key: 'isLimited', label: 'Limited (2+)' });
    if (isGeneric) chips.push({ key: 'isGeneric', label: 'Generic' });
    for (const b of selectedBaseSizes) chips.push({ key: `base:${b}`, label: `Base: ${b}` });

    if (initMin || initMax) chips.push({ key: 'init', label: `Init: ${initMin || 0}-${initMax || 6}` });
    if (hullMin || hullMax) chips.push({ key: 'hull', label: `Hull: ${hullMin || 0}-${hullMax || '∞'}` });
    if (shieldsMin || shieldsMax) chips.push({ key: 'shields', label: `Shields: ${shieldsMin || 0}-${shieldsMax || '∞'}` });
    if (agilityMin || agilityMax) chips.push({ key: 'agility', label: `Agility: ${agilityMin || 0}-${agilityMax || 3}` });
    if (attackMin || attackMax) chips.push({ key: 'attack', label: `Attack: ${attackMin || 0}-${attackMax || '∞'}` });
    // Slot composite: show slot × count chips, plus mode
    try {
        const _sc: Array<{slot:string;count:number}> = slotCounts ? JSON.parse(slotCounts) : [];
        for (const e of _sc) chips.push({ key: `slotCount:${e.slot}:${e.count}`, label: `${e.slot} ×${e.count}` });
        if (_sc.length > 1 && slotCountMode === 'all') chips.push({ key: 'slotCountMode', label: 'Slots: All' });
    } catch {}
    for (const s of selectedSlots) chips.push({ key: `slot:${s}`, label: `Slot: ${s}` });
    if (hasMultipleSlots) chips.push({ key: 'hasMultipleSlots', label: 'Multiple slots' });
    if (slotFilterMode === 'all' && selectedSlots.length > 1) chips.push({ key: 'slotMode', label: 'Slots: All' });
    for (const k of selectedKeywords) chips.push({ key: `keyword:${k}`, label: `Keyword: ${k}` });
    if (keywordFilterMode === 'all' && selectedKeywords.length > 1) chips.push({ key: 'keywordMode', label: 'Keywords: All' });
    // Action pairs: { action, linked } composite (new), plus legacy flat for compat
    try {
        const _ap: Array<{action:string|null;linked:string|null}> = actionPairs ? JSON.parse(actionPairs) : [];
        for (let i=0;i<_ap.length;i++) {
            const p=_ap[i];
            const lab = `${p.action ?? 'Any'}${p.linked ? ' → ' + p.linked : ''}`;
            chips.push({ key: `actionPair:${i}`, label: lab });
        }
        if (_ap.length > 1 && actionPairMode === 'all') chips.push({ key: 'actionPairMode', label: 'Actions: All' });
    } catch {}
    for (const a of selectedActions) chips.push({ key: `action:${a}`, label: `Action: ${a}` });
    if (actionFilterMode === 'all' && selectedActions.length > 1) chips.push({ key: 'actionMode', label: 'Actions: All' });
    for (const a of selectedLinkedActions) chips.push({ key: `linkedAction:${a}`, label: `Linked: ${a}` });
    if (linkedActionFilterMode === 'all' && selectedLinkedActions.length > 1) chips.push({ key: 'linkedActionMode', label: 'Linked: All' });
    if (frontArcMin || frontArcMax) chips.push({ key: 'frontArc', label: `Front Arc: ${frontArcMin || 0}-${frontArcMax || '∞'}` });
    if (singleTurretMin || singleTurretMax) chips.push({ key: 'singleTurret', label: `Single Turret: ${singleTurretMin || 0}-${singleTurretMax || '∞'}` });
    if (doubleTurretMin || doubleTurretMax) chips.push({ key: 'doubleTurret', label: `Double Turret: ${doubleTurretMin || 0}-${doubleTurretMax || '∞'}` });
    if (fullFrontMin || fullFrontMax) chips.push({ key: 'fullFront', label: `Full Front: ${fullFrontMin || 0}-${fullFrontMax || '∞'}` });
    if (rearArcMin || rearArcMax) chips.push({ key: 'rearArc', label: `Rear Arc: ${rearArcMin || 0}-${rearArcMax || '∞'}` });
    if (bullseyeMin || bullseyeMax) chips.push({ key: 'bullseye', label: `Bullseye: ${bullseyeMin || 0}-${bullseyeMax || '∞'}` });
    if (chargesMin || chargesMax) chips.push({ key: 'charges', label: `Charges: ${chargesMin || 0}-${chargesMax || '∞'}` });
    if (isRecurring) chips.push({ key: 'isRecurring', label: 'Recurring' });
    if (isNotRecurring) chips.push({ key: 'isNotRecurring', label: 'Not recurring' });
    if (forceMin || forceMax) chips.push({ key: 'force', label: `Force: ${forceMin || 0}-${forceMax || '∞'}` });
    for (const s of selectedUsedSlots) chips.push({ key: `usedSlot:${s}`, label: `Used slot: ${s}` });
    if (usedSlotFilterMode === 'all' && selectedUsedSlots.length > 1) chips.push({ key: 'usedSlotMode', label: 'Used slots: All' });
    for (const s of selectedUsedDoubleSlots) chips.push({ key: `usedDoubleSlot:${s}`, label: `Double-slot: ${s}` });
    if (usedDoubleSlotFilterMode === 'all' && selectedUsedDoubleSlots.length > 1) chips.push({ key: 'usedDoubleSlotMode', label: 'Double-slots: All' });
    if (onlyMultiSlot) chips.push({ key: 'onlyMultiSlot', label: 'Only multi-slot' });

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
    else if (key === 'slotMode') slotFilterMode = 'any';
    else if (key === 'slotCountMode') slotCountMode = 'any';
    else if (key === 'keywordMode') keywordFilterMode = 'any';
    else if (key === 'actionMode') actionFilterMode = 'any';
    else if (key === 'linkedActionMode') linkedActionFilterMode = 'any';
    else if (key === 'actionPairMode') actionPairMode = 'any';
    else if (key.startsWith('slotCount:')) {
        try { const parts = key.slice(10).split(':'); const cnt = parseInt(parts.pop()!); const slot = parts.join(':'); const arr: Array<{slot:string;count:number}> = slotCounts ? JSON.parse(slotCounts) : []; const filtered = arr.filter(e => !(e.slot===slot && e.count===cnt)); slotCounts = filtered.length ? JSON.stringify(filtered) : ""; } catch {}
    } else if (key.startsWith('actionPair:')) {
        try { const idx = parseInt(key.slice(11)); const arr: Array<{action:string|null;linked:string|null}> = actionPairs ? JSON.parse(actionPairs) : []; const filtered = arr.filter((_,i)=>i!==idx); actionPairs = filtered.length ? JSON.stringify(filtered) : ""; } catch {}
    }
    else if (key === 'usedSlotMode') usedSlotFilterMode = 'any';
    else if (key === 'usedDoubleSlotMode') usedDoubleSlotFilterMode = 'any';
    else if (key === 'frontArc') { frontArcMin = ''; frontArcMax = ''; }
    else if (key === 'singleTurret') { singleTurretMin = ''; singleTurretMax = ''; }
    else if (key === 'doubleTurret') { doubleTurretMin = ''; doubleTurretMax = ''; }
    else if (key === 'fullFront') { fullFrontMin = ''; fullFrontMax = ''; }
    else if (key === 'rearArc') { rearArcMin = ''; rearArcMax = ''; }
    else if (key === 'bullseye') { bullseyeMin = ''; bullseyeMax = ''; }
    else if (key === 'charges') { chargesMin = ''; chargesMax = ''; }
    else if (key === 'isRecurring') isRecurring = false;
    else if (key === 'isNotRecurring') isNotRecurring = false;
    else if (key === 'force') { forceMin = ''; forceMax = ''; }
    else if (key === 'onlyMultiSlot') onlyMultiSlot = false;
    else if (key === 'hasMultipleSlots') hasMultipleSlots = false;
    else if (key.startsWith('slot:')) selectedSlots = selectedSlots.filter(s => s !== key.slice(5));
    else if (key.startsWith('slotCount:')) { try { const parts = key.slice(10).split(':'); const cnt = parseInt(parts.pop()!); const slot = parts.join(':'); const arr: Array<{slot:string;count:number}> = slotCounts ? JSON.parse(slotCounts) : []; const filtered = arr.filter(e => !(e.slot===slot && e.count===cnt)); slotCounts = filtered.length ? JSON.stringify(filtered) : ""; } catch {} }
    else if (key.startsWith('keyword:')) selectedKeywords = selectedKeywords.filter(s => s !== key.slice(8));
    else if (key.startsWith('action:')) selectedActions = selectedActions.filter(s => s !== key.slice(7));
    else if (key.startsWith('linkedAction:')) selectedLinkedActions = selectedLinkedActions.filter(s => s !== key.slice(13));
    else if (key.startsWith('usedSlot:')) selectedUsedSlots = selectedUsedSlots.filter(s => s !== key.slice(9));
    else if (key.startsWith('usedDoubleSlot:')) selectedUsedDoubleSlots = selectedUsedDoubleSlots.filter(s => s !== key.slice(15));
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
    // YASB-inspired
    slotCounts = ""; slotCountMode = 'any'; selectedSlots = []; slotFilterMode = 'any'; hasMultipleSlots = false;
    selectedKeywords = []; keywordFilterMode = 'any';
    actionPairs = ""; actionPairMode = 'any'; selectedActions = []; actionFilterMode = 'any';
    selectedLinkedActions = []; linkedActionFilterMode = 'any';
    frontArcMin = ''; frontArcMax = '';
    singleTurretMin = ''; singleTurretMax = '';
    doubleTurretMin = ''; doubleTurretMax = '';
    fullFrontMin = ''; fullFrontMax = '';
    rearArcMin = ''; rearArcMax = '';
    bullseyeMin = ''; bullseyeMax = '';
    chargesMin = ''; chargesMax = ''; isRecurring = false; isNotRecurring = false;
    forceMin = ''; forceMax = '';
    selectedUsedSlots = []; usedSlotFilterMode = 'any';
    selectedUsedDoubleSlots = []; usedDoubleSlotFilterMode = 'any';
    onlyMultiSlot = false;
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
    | 'sortDirection'
    | 'selectedSlots'
    | 'slotFilterMode'
    | 'hasMultipleSlots'
    | 'slotCounts'
    | 'slotCountMode'
    | 'selectedKeywords'
    | 'keywordFilterMode'
    | 'selectedActions'
    | 'actionFilterMode'
    | 'selectedLinkedActions'
    | 'linkedActionFilterMode'
    | 'actionPairs'
    | 'actionPairMode'
    | 'frontArcMin'
    | 'frontArcMax'
    | 'singleTurretMin'
    | 'singleTurretMax'
    | 'doubleTurretMin'
    | 'doubleTurretMax'
    | 'fullFrontMin'
    | 'fullFrontMax'
    | 'rearArcMin'
    | 'rearArcMax'
    | 'bullseyeMin'
    | 'bullseyeMax'
    | 'chargesMin'
    | 'chargesMax'
    | 'isRecurring'
    | 'isNotRecurring'
    | 'forceMin'
    | 'forceMax'
    | 'selectedUsedSlots'
    | 'usedSlotFilterMode'
    | 'selectedUsedDoubleSlots'
    | 'usedDoubleSlotFilterMode'
    | 'onlyMultiSlot';

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
        'slotCounts',
        'slotCountMode',
        'selectedSlots',
        'slotFilterMode',
        'hasMultipleSlots',
        'selectedKeywords',
        'keywordFilterMode',
        'actionPairs',
        'actionPairMode',
        'selectedActions',
        'actionFilterMode',
        'selectedLinkedActions',
        'linkedActionFilterMode',
        'frontArcMin',
        'frontArcMax',
        'singleTurretMin',
        'singleTurretMax',
        'doubleTurretMin',
        'doubleTurretMax',
        'fullFrontMin',
        'fullFrontMax',
        'rearArcMin',
        'rearArcMax',
        'bullseyeMin',
        'bullseyeMax',
        'chargesMin',
        'chargesMax',
        'isRecurring',
        'isNotRecurring',
        'forceMin',
        'forceMax',
        'selectedUsedSlots',
        'usedSlotFilterMode',
        'selectedUsedDoubleSlots',
        'usedDoubleSlotFilterMode',
        'onlyMultiSlot',
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
    slotFilterMode: 'slot_mode',
    slotCounts: 'slot_counts',
    slotCountMode: 'slot_count_mode',
    actionPairs: 'action_pairs',
    actionPairMode: 'action_pair_mode',
    keywordFilterMode: 'keyword_mode',
    actionFilterMode: 'action_mode',
    linkedActionFilterMode: 'linked_action_mode',
    frontArcMin: 'front_arc_min',
    frontArcMax: 'front_arc_max',
    singleTurretMin: 'single_turret_min',
    singleTurretMax: 'single_turret_max',
    doubleTurretMin: 'double_turret_min',
    doubleTurretMax: 'double_turret_max',
    fullFrontMin: 'full_front_min',
    fullFrontMax: 'full_front_max',
    rearArcMin: 'rear_arc_min',
    rearArcMax: 'rear_arc_max',
    bullseyeMin: 'bullseye_min',
    bullseyeMax: 'bullseye_max',
    chargesMin: 'charges_min',
    chargesMax: 'charges_max',
    isRecurring: 'is_recurring',
    isNotRecurring: 'is_not_recurring',
    forceMin: 'force_min',
    forceMax: 'force_max',
    hasMultipleSlots: 'has_multiple_slots',
    usedSlotFilterMode: 'used_slot_mode',
    usedDoubleSlotFilterMode: 'used_double_slot_mode',
    onlyMultiSlot: 'only_multi_slot',
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
    selectedSlots: 'slots',
    selectedKeywords: 'keywords',
    selectedActions: 'actions',
    selectedLinkedActions: 'linked_actions',
    selectedUsedSlots: 'used_slots',
    selectedUsedDoubleSlots: 'used_double_slots',
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
            case 'slotCounts':
                if (slotCounts) params.set(SINGLE_KEY.slotCounts, slotCounts);
                break;
            case 'slotCountMode':
                if (slotCountMode === 'all') params.set(SINGLE_KEY.slotCountMode, 'all');
                break;
            case 'slotFilterMode':
                if (slotFilterMode === 'all') params.set(SINGLE_KEY.slotFilterMode, 'all');
                break;
            case 'hasMultipleSlots':
                if (hasMultipleSlots) params.set(SINGLE_KEY.hasMultipleSlots, 'true');
                break;
            case 'actionPairs':
                if (actionPairs) params.set(SINGLE_KEY.actionPairs, actionPairs);
                break;
            case 'actionPairMode':
                if (actionPairMode === 'all') params.set(SINGLE_KEY.actionPairMode, 'all');
                break;
            case 'keywordFilterMode':
                if (keywordFilterMode === 'all') params.set(SINGLE_KEY.keywordFilterMode, 'all');
                break;
            case 'actionFilterMode':
                if (actionFilterMode === 'all') params.set(SINGLE_KEY.actionFilterMode, 'all');
                break;
            case 'linkedActionFilterMode':
                if (linkedActionFilterMode === 'all') params.set(SINGLE_KEY.linkedActionFilterMode, 'all');
                break;
            case 'frontArcMin':
                if (frontArcMin) params.set(SINGLE_KEY.frontArcMin, frontArcMin);
                break;
            case 'frontArcMax':
                if (frontArcMax) params.set(SINGLE_KEY.frontArcMax, frontArcMax);
                break;
            case 'singleTurretMin':
                if (singleTurretMin) params.set(SINGLE_KEY.singleTurretMin, singleTurretMin);
                break;
            case 'singleTurretMax':
                if (singleTurretMax) params.set(SINGLE_KEY.singleTurretMax, singleTurretMax);
                break;
            case 'doubleTurretMin':
                if (doubleTurretMin) params.set(SINGLE_KEY.doubleTurretMin, doubleTurretMin);
                break;
            case 'doubleTurretMax':
                if (doubleTurretMax) params.set(SINGLE_KEY.doubleTurretMax, doubleTurretMax);
                break;
            case 'fullFrontMin':
                if (fullFrontMin) params.set(SINGLE_KEY.fullFrontMin, fullFrontMin);
                break;
            case 'fullFrontMax':
                if (fullFrontMax) params.set(SINGLE_KEY.fullFrontMax, fullFrontMax);
                break;
            case 'rearArcMin':
                if (rearArcMin) params.set(SINGLE_KEY.rearArcMin, rearArcMin);
                break;
            case 'rearArcMax':
                if (rearArcMax) params.set(SINGLE_KEY.rearArcMax, rearArcMax);
                break;
            case 'bullseyeMin':
                if (bullseyeMin) params.set(SINGLE_KEY.bullseyeMin, bullseyeMin);
                break;
            case 'bullseyeMax':
                if (bullseyeMax) params.set(SINGLE_KEY.bullseyeMax, bullseyeMax);
                break;
            case 'chargesMin':
                if (chargesMin) params.set(SINGLE_KEY.chargesMin, chargesMin);
                break;
            case 'chargesMax':
                if (chargesMax) params.set(SINGLE_KEY.chargesMax, chargesMax);
                break;
            case 'isRecurring':
                if (isRecurring) params.set(SINGLE_KEY.isRecurring, 'true');
                break;
            case 'isNotRecurring':
                if (isNotRecurring) params.set(SINGLE_KEY.isNotRecurring, 'true');
                break;
            case 'forceMin':
                if (forceMin) params.set(SINGLE_KEY.forceMin, forceMin);
                break;
            case 'forceMax':
                if (forceMax) params.set(SINGLE_KEY.forceMax, forceMax);
                break;
            case 'usedSlotFilterMode':
                if (usedSlotFilterMode === 'all') params.set(SINGLE_KEY.usedSlotFilterMode, 'all');
                break;
            case 'usedDoubleSlotFilterMode':
                if (usedDoubleSlotFilterMode === 'all') params.set(SINGLE_KEY.usedDoubleSlotFilterMode, 'all');
                break;
            case 'onlyMultiSlot':
                if (onlyMultiSlot) params.set(SINGLE_KEY.onlyMultiSlot, 'true');
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
            case 'selectedSlots':
                for (const s of selectedSlots) params.append(SINGLE_KEY.selectedSlots, s);
                break;
            case 'selectedKeywords':
                for (const k of selectedKeywords) params.append(SINGLE_KEY.selectedKeywords, k);
                break;
            case 'selectedActions':
                for (const a of selectedActions) params.append(SINGLE_KEY.selectedActions, a);
                break;
            case 'selectedLinkedActions':
                for (const a of selectedLinkedActions) params.append(SINGLE_KEY.selectedLinkedActions, a);
                break;
            case 'selectedUsedSlots':
                for (const s of selectedUsedSlots) params.append(SINGLE_KEY.selectedUsedSlots, s);
                break;
            case 'selectedUsedDoubleSlots':
                for (const s of selectedUsedDoubleSlots) params.append(SINGLE_KEY.selectedUsedDoubleSlots, s);
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
    if (params.has('data_source')) {
        const dataSourceVal = params.get('data_source');
        const nextDs = dataSourceVal === 'legacy' ? 'legacy' : 'xwa';
        if (dataSource !== nextDs) {
            dataSource = nextDs;
            if (typeof localStorage !== 'undefined') {
                try { localStorage.setItem('m3tacron:dataSource', nextDs); } catch (e) {}
            }
            if (nextDs === 'xwa') {
                selectedFormats = ['xwa'];
            } else {
                selectedFormats = ['legacy_x2po'];
            }
        }
    } else if (typeof localStorage !== 'undefined') {
        try {
            const saved = localStorage.getItem('m3tacron:dataSource');
            if ((saved === 'legacy' || saved === 'xwa') && dataSource !== saved) {
                dataSource = saved;
                if (saved === 'xwa') {
                    selectedFormats = ['xwa'];
                } else {
                    selectedFormats = ['legacy_x2po'];
                }
            }
        } catch (e) {}
    }

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
    if (params.has('slot_counts')) { const v = params.get('slot_counts') ?? ''; if (v) slotCounts = v; }
    if (params.has('slot_count_mode')) { const v = params.get('slot_count_mode'); if (v === 'all' || v === 'any') slotCountMode = v; }
    if (params.has('action_pairs')) { const v = params.get('action_pairs') ?? ''; if (v) actionPairs = v; }
    if (params.has('action_pair_mode')) { const v = params.get('action_pair_mode'); if (v === 'all' || v === 'any') actionPairMode = v; }
    if (params.has('slot_mode')) { const v = params.get('slot_mode'); if (v === 'all' || v === 'any') slotFilterMode = v; }
    if (params.has('has_multiple_slots')) hasMultipleSlots = params.get('has_multiple_slots') === 'true';
    if (params.has('keyword_mode')) { const v = params.get('keyword_mode'); if (v === 'all' || v === 'any') keywordFilterMode = v; }
    if (params.has('action_mode')) { const v = params.get('action_mode'); if (v === 'all' || v === 'any') actionFilterMode = v; }
    if (params.has('linked_action_mode')) { const v = params.get('linked_action_mode'); if (v === 'all' || v === 'any') linkedActionFilterMode = v; }
    if (params.has('front_arc_min')) { const v = params.get('front_arc_min') ?? ''; if (v) frontArcMin = v; }
    if (params.has('front_arc_max')) { const v = params.get('front_arc_max') ?? ''; if (v) frontArcMax = v; }
    if (params.has('single_turret_min')) { const v = params.get('single_turret_min') ?? ''; if (v) singleTurretMin = v; }
    if (params.has('single_turret_max')) { const v = params.get('single_turret_max') ?? ''; if (v) singleTurretMax = v; }
    if (params.has('double_turret_min')) { const v = params.get('double_turret_min') ?? ''; if (v) doubleTurretMin = v; }
    if (params.has('double_turret_max')) { const v = params.get('double_turret_max') ?? ''; if (v) doubleTurretMax = v; }
    if (params.has('full_front_min')) { const v = params.get('full_front_min') ?? ''; if (v) fullFrontMin = v; }
    if (params.has('full_front_max')) { const v = params.get('full_front_max') ?? ''; if (v) fullFrontMax = v; }
    if (params.has('rear_arc_min')) { const v = params.get('rear_arc_min') ?? ''; if (v) rearArcMin = v; }
    if (params.has('rear_arc_max')) { const v = params.get('rear_arc_max') ?? ''; if (v) rearArcMax = v; }
    if (params.has('bullseye_min')) { const v = params.get('bullseye_min') ?? ''; if (v) bullseyeMin = v; }
    if (params.has('bullseye_max')) { const v = params.get('bullseye_max') ?? ''; if (v) bullseyeMax = v; }
    if (params.has('charges_min')) { const v = params.get('charges_min') ?? ''; if (v) chargesMin = v; }
    if (params.has('charges_max')) { const v = params.get('charges_max') ?? ''; if (v) chargesMax = v; }
    if (params.has('is_recurring')) isRecurring = params.get('is_recurring') === 'true';
    if (params.has('is_not_recurring')) isNotRecurring = params.get('is_not_recurring') === 'true';
    if (params.has('force_min')) { const v = params.get('force_min') ?? ''; if (v) forceMin = v; }
    if (params.has('force_max')) { const v = params.get('force_max') ?? ''; if (v) forceMax = v; }
    if (params.has('used_slot_mode')) { const v = params.get('used_slot_mode'); if (v === 'all' || v === 'any') usedSlotFilterMode = v; }
    if (params.has('used_double_slot_mode')) { const v = params.get('used_double_slot_mode'); if (v === 'all' || v === 'any') usedDoubleSlotFilterMode = v; }
    if (params.has('only_multi_slot')) onlyMultiSlot = params.get('only_multi_slot') === 'true';

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
    const slots = params.getAll('slots');
    if (slots.length > 0) selectedSlots = slots;
    const keywords = params.getAll('keywords');
    if (keywords.length > 0) selectedKeywords = keywords;
    const actions = params.getAll('actions');
    if (actions.length > 0) selectedActions = actions;
    const linkedActions = params.getAll('linked_actions');
    if (linkedActions.length > 0) selectedLinkedActions = linkedActions;
    const usedSlots = params.getAll('used_slots');
    if (usedSlots.length > 0) selectedUsedSlots = usedSlots;
    const usedDoubleSlots = params.getAll('used_double_slots');
    if (usedDoubleSlots.length > 0) selectedUsedDoubleSlots = usedDoubleSlots;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------


// ---------------------------------------------------------------------------
// Per-route local filter persistence (dataset stays global, local is per page)
// ---------------------------------------------------------------------------

// Dataset keys: global across routes, never per-route. Local = everything else.
const DATASET_KEYS: Record<string, boolean> = {
    dataSource: true, includeEpic: true, selectedFormats: true,
    selectedSources: true, selectedContinents: true, selectedCountries: true,
    selectedCities: true, dateStart: true, dateEnd: true,
};
const LOCAL_KEYS_BY_ROUTE: Record<RouteId, string[]> = {
    cards: ['selectedFactions','selectedShips','searchName','pointsMin','pointsMax','loadoutMin','loadoutMax','isUnique','isLimited','isGeneric','selectedBaseSizes','initMin','initMax','hullMin','hullMax','shieldsMin','shieldsMax','agilityMin','agilityMax','attackMin','attackMax','slotCounts','slotCountMode','selectedSlots','slotFilterMode','hasMultipleSlots','selectedKeywords','keywordFilterMode','actionPairs','actionPairMode','selectedActions','actionFilterMode','selectedLinkedActions','linkedActionFilterMode','frontArcMin','frontArcMax','singleTurretMin','singleTurretMax','doubleTurretMin','doubleTurretMax','fullFrontMin','fullFrontMax','rearArcMin','rearArcMax','bullseyeMin','bullseyeMax','chargesMin','chargesMax','isRecurring','isNotRecurring','forceMin','forceMax','selectedUsedSlots','usedSlotFilterMode','selectedUsedDoubleSlots','usedDoubleSlotFilterMode','onlyMultiSlot','listsMin','listsMax','entriesMin','entriesMax','gamesMin','gamesMax','winRateMin','winRateMax','sortBy','sortDirection'],
    lists: ['selectedFactions','selectedShips','selectedPilots','pilotFilterMode','shipFilterMode','listsMin','listsMax','entriesMin','entriesMax','gamesMin','gamesMax','winRateMin','winRateMax','sortBy','sortDirection'],
    ships: ['selectedFactions','selectedShips','shipFilterMode','listsMin','listsMax','entriesMin','entriesMax','gamesMin','gamesMax','winRateMin','winRateMax','sortBy','sortDirection'],
    squadrons: ['selectedFactions','selectedShips','shipFilterMode','listsMin','listsMax','entriesMin','entriesMax','gamesMin','gamesMax','winRateMin','winRateMax','sortBy','sortDirection'],
    tournaments: ['searchName','sortBy','sortDirection'],
};

function localStorageKey(route: RouteId): string { return `m3tacron:localFilters:${route}`; }

function snapshotLocal(route: RouteId): Record<string, unknown> {
    const keys = LOCAL_KEYS_BY_ROUTE[route] ?? [];
    const out: Record<string, unknown> = {};
    for (const k of keys) {
        switch (k) {
            // YASB-inspired pilot/upgrade filters
            case 'slotCounts': out[k] = slotCounts; break;
            case 'slotCountMode': out[k] = slotCountMode; break;
            case 'actionPairs': out[k] = actionPairs; break;
            case 'actionPairMode': out[k] = actionPairMode; break;
            case 'selectedSlots': out[k] = [...selectedSlots]; break;
            case 'slotFilterMode': out[k] = slotFilterMode; break;
            case 'hasMultipleSlots': out[k] = hasMultipleSlots; break;
            case 'selectedKeywords': out[k] = [...selectedKeywords]; break;
            case 'keywordFilterMode': out[k] = keywordFilterMode; break;
            case 'selectedActions': out[k] = [...selectedActions]; break;
            case 'actionFilterMode': out[k] = actionFilterMode; break;
            case 'selectedLinkedActions': out[k] = [...selectedLinkedActions]; break;
            case 'linkedActionFilterMode': out[k] = linkedActionFilterMode; break;
            case 'frontArcMin': out[k] = frontArcMin; break;
            case 'frontArcMax': out[k] = frontArcMax; break;
            case 'singleTurretMin': out[k] = singleTurretMin; break;
            case 'singleTurretMax': out[k] = singleTurretMax; break;
            case 'doubleTurretMin': out[k] = doubleTurretMin; break;
            case 'doubleTurretMax': out[k] = doubleTurretMax; break;
            case 'fullFrontMin': out[k] = fullFrontMin; break;
            case 'fullFrontMax': out[k] = fullFrontMax; break;
            case 'rearArcMin': out[k] = rearArcMin; break;
            case 'rearArcMax': out[k] = rearArcMax; break;
            case 'bullseyeMin': out[k] = bullseyeMin; break;
            case 'bullseyeMax': out[k] = bullseyeMax; break;
            case 'chargesMin': out[k] = chargesMin; break;
            case 'chargesMax': out[k] = chargesMax; break;
            case 'isRecurring': out[k] = isRecurring; break;
            case 'isNotRecurring': out[k] = isNotRecurring; break;
            case 'forceMin': out[k] = forceMin; break;
            case 'forceMax': out[k] = forceMax; break;
            case 'selectedUsedSlots': out[k] = [...selectedUsedSlots]; break;
            case 'usedSlotFilterMode': out[k] = usedSlotFilterMode; break;
            case 'selectedUsedDoubleSlots': out[k] = [...selectedUsedDoubleSlots]; break;
            case 'usedDoubleSlotFilterMode': out[k] = usedDoubleSlotFilterMode; break;
            case 'onlyMultiSlot': out[k] = onlyMultiSlot; break;
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

function clearLocalKeysForRoutesExcept(activeRoute: RouteId): void {
    const keep = new Set(LOCAL_KEYS_BY_ROUTE[activeRoute] ?? []);
    const allLocal = new Set<string>();
    for (const ks of Object.values(LOCAL_KEYS_BY_ROUTE)) for (const k of ks as string[]) if (!DATASET_KEYS[k]) allLocal.add(k);
    for (const k of allLocal) {
        if (keep.has(k)) continue;
        switch (k) {
            case 'selectedFactions': selectedFactions = []; break;
            case 'selectedShips': selectedShips = []; break;
            case 'selectedPilots': selectedPilots = []; break;
            case 'pilotFilterMode': pilotFilterMode = 'any'; break;
            case 'shipFilterMode': shipFilterMode = 'any'; break;
            case 'searchName': searchName = ''; break;
            case 'pointsMin': pointsMin = ''; break;
            case 'pointsMax': pointsMax = ''; break;
            case 'loadoutMin': loadoutMin = ''; break;
            case 'loadoutMax': loadoutMax = ''; break;
            case 'isUnique': isUnique = false; break;
            case 'isLimited': isLimited = false; break;
            case 'isGeneric': isGeneric = false; break;
            case 'selectedBaseSizes': selectedBaseSizes = []; break;
            case 'initMin': initMin = ''; break;
            case 'initMax': initMax = ''; break;
            case 'hullMin': hullMin = ''; break;
            case 'hullMax': hullMax = ''; break;
            case 'shieldsMin': shieldsMin = ''; break;
            case 'shieldsMax': shieldsMax = ''; break;
            case 'agilityMin': agilityMin = ''; break;
            case 'agilityMax': agilityMax = ''; break;
            case 'attackMin': attackMin = ''; break;
            case 'attackMax': attackMax = ''; break;
            case 'slotCounts': slotCounts = ''; break;
            case 'slotCountMode': slotCountMode = 'any'; break;
            case 'selectedSlots': selectedSlots = []; break;
            case 'slotFilterMode': slotFilterMode = 'any'; break;
            case 'hasMultipleSlots': hasMultipleSlots = false; break;
            case 'selectedKeywords': selectedKeywords = []; break;
            case 'keywordFilterMode': keywordFilterMode = 'any'; break;
            case 'actionPairs': actionPairs = ''; break;
            case 'actionPairMode': actionPairMode = 'any'; break;
            case 'selectedActions': selectedActions = []; break;
            case 'actionFilterMode': actionFilterMode = 'any'; break;
            case 'selectedLinkedActions': selectedLinkedActions = []; break;
            case 'linkedActionFilterMode': linkedActionFilterMode = 'any'; break;
            case 'frontArcMin': frontArcMin = ''; break;
            case 'frontArcMax': frontArcMax = ''; break;
            case 'singleTurretMin': singleTurretMin = ''; break;
            case 'singleTurretMax': singleTurretMax = ''; break;
            case 'doubleTurretMin': doubleTurretMin = ''; break;
            case 'doubleTurretMax': doubleTurretMax = ''; break;
            case 'fullFrontMin': fullFrontMin = ''; break;
            case 'fullFrontMax': fullFrontMax = ''; break;
            case 'rearArcMin': rearArcMin = ''; break;
            case 'rearArcMax': rearArcMax = ''; break;
            case 'bullseyeMin': bullseyeMin = ''; break;
            case 'bullseyeMax': bullseyeMax = ''; break;
            case 'chargesMin': chargesMin = ''; break;
            case 'chargesMax': chargesMax = ''; break;
            case 'isRecurring': isRecurring = false; break;
            case 'isNotRecurring': isNotRecurring = false; break;
            case 'forceMin': forceMin = ''; break;
            case 'forceMax': forceMax = ''; break;
            case 'selectedUsedSlots': selectedUsedSlots = []; break;
            case 'usedSlotFilterMode': usedSlotFilterMode = 'any'; break;
            case 'selectedUsedDoubleSlots': selectedUsedDoubleSlots = []; break;
            case 'usedDoubleSlotFilterMode': usedDoubleSlotFilterMode = 'any'; break;
            case 'onlyMultiSlot': onlyMultiSlot = false; break;
            case 'listsMin': listsMin = ''; break;
            case 'listsMax': listsMax = ''; break;
            case 'entriesMin': entriesMin = ''; break;
            case 'entriesMax': entriesMax = ''; break;
            case 'gamesMin': gamesMin = ''; break;
            case 'gamesMax': gamesMax = ''; break;
            case 'winRateMin': winRateMin = ''; break;
            case 'winRateMax': winRateMax = ''; break;
            case 'sortBy': sortBy = ''; break;
            case 'sortDirection': sortDirection = 'desc'; break;
        }
    }
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
    if (has('slotCounts') && typeof snap['slotCounts']==='string') slotCounts = snap['slotCounts'] as string;
    if (has('slotCountMode') && (snap['slotCountMode']==='any'||snap['slotCountMode']==='all')) slotCountMode = snap['slotCountMode'] as 'any'|'all';
    if (has('actionPairs') && typeof snap['actionPairs']==='string') actionPairs = snap['actionPairs'] as string;
    if (has('actionPairMode') && (snap['actionPairMode']==='any'||snap['actionPairMode']==='all')) actionPairMode = snap['actionPairMode'] as 'any'|'all';
    if (has('selectedSlots') && Array.isArray(snap['selectedSlots'])) selectedSlots = snap['selectedSlots'] as string[];
    if (has('slotFilterMode') && (snap['slotFilterMode']==='any'||snap['slotFilterMode']==='all')) slotFilterMode = snap['slotFilterMode'] as 'any'|'all';
    if (has('hasMultipleSlots') && typeof snap['hasMultipleSlots']==='boolean') hasMultipleSlots = snap['hasMultipleSlots'] as boolean;
    if (has('selectedKeywords') && Array.isArray(snap['selectedKeywords'])) selectedKeywords = snap['selectedKeywords'] as string[];
    if (has('keywordFilterMode') && (snap['keywordFilterMode']==='any'||snap['keywordFilterMode']==='all')) keywordFilterMode = snap['keywordFilterMode'] as 'any'|'all';
    if (has('selectedActions') && Array.isArray(snap['selectedActions'])) selectedActions = snap['selectedActions'] as string[];
    if (has('actionFilterMode') && (snap['actionFilterMode']==='any'||snap['actionFilterMode']==='all')) actionFilterMode = snap['actionFilterMode'] as 'any'|'all';
    if (has('selectedLinkedActions') && Array.isArray(snap['selectedLinkedActions'])) selectedLinkedActions = snap['selectedLinkedActions'] as string[];
    if (has('linkedActionFilterMode') && (snap['linkedActionFilterMode']==='any'||snap['linkedActionFilterMode']==='all')) linkedActionFilterMode = snap['linkedActionFilterMode'] as 'any'|'all';
    if (has('frontArcMin') && typeof snap['frontArcMin']==='string') frontArcMin = snap['frontArcMin'] as string;
    if (has('frontArcMax') && typeof snap['frontArcMax']==='string') frontArcMax = snap['frontArcMax'] as string;
    if (has('singleTurretMin') && typeof snap['singleTurretMin']==='string') singleTurretMin = snap['singleTurretMin'] as string;
    if (has('singleTurretMax') && typeof snap['singleTurretMax']==='string') singleTurretMax = snap['singleTurretMax'] as string;
    if (has('doubleTurretMin') && typeof snap['doubleTurretMin']==='string') doubleTurretMin = snap['doubleTurretMin'] as string;
    if (has('doubleTurretMax') && typeof snap['doubleTurretMax']==='string') doubleTurretMax = snap['doubleTurretMax'] as string;
    if (has('fullFrontMin') && typeof snap['fullFrontMin']==='string') fullFrontMin = snap['fullFrontMin'] as string;
    if (has('fullFrontMax') && typeof snap['fullFrontMax']==='string') fullFrontMax = snap['fullFrontMax'] as string;
    if (has('rearArcMin') && typeof snap['rearArcMin']==='string') rearArcMin = snap['rearArcMin'] as string;
    if (has('rearArcMax') && typeof snap['rearArcMax']==='string') rearArcMax = snap['rearArcMax'] as string;
    if (has('bullseyeMin') && typeof snap['bullseyeMin']==='string') bullseyeMin = snap['bullseyeMin'] as string;
    if (has('bullseyeMax') && typeof snap['bullseyeMax']==='string') bullseyeMax = snap['bullseyeMax'] as string;
    if (has('chargesMin') && typeof snap['chargesMin']==='string') chargesMin = snap['chargesMin'] as string;
    if (has('chargesMax') && typeof snap['chargesMax']==='string') chargesMax = snap['chargesMax'] as string;
    if (has('isRecurring') && typeof snap['isRecurring']==='boolean') isRecurring = snap['isRecurring'] as boolean;
    if (has('isNotRecurring') && typeof snap['isNotRecurring']==='boolean') isNotRecurring = snap['isNotRecurring'] as boolean;
    if (has('forceMin') && typeof snap['forceMin']==='string') forceMin = snap['forceMin'] as string;
    if (has('forceMax') && typeof snap['forceMax']==='string') forceMax = snap['forceMax'] as string;
    if (has('selectedUsedSlots') && Array.isArray(snap['selectedUsedSlots'])) selectedUsedSlots = snap['selectedUsedSlots'] as string[];
    if (has('usedSlotFilterMode') && (snap['usedSlotFilterMode']==='any'||snap['usedSlotFilterMode']==='all')) usedSlotFilterMode = snap['usedSlotFilterMode'] as 'any'|'all';
    if (has('selectedUsedDoubleSlots') && Array.isArray(snap['selectedUsedDoubleSlots'])) selectedUsedDoubleSlots = snap['selectedUsedDoubleSlots'] as string[];
    if (has('usedDoubleSlotFilterMode') && (snap['usedDoubleSlotFilterMode']==='any'||snap['usedDoubleSlotFilterMode']==='all')) usedDoubleSlotFilterMode = snap['usedDoubleSlotFilterMode'] as 'any'|'all';
    if (has('onlyMultiSlot') && typeof snap['onlyMultiSlot']==='boolean') onlyMultiSlot = snap['onlyMultiSlot'] as boolean;
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
    // If URL already carries any local key for this route, it is the source of truth (shareable URL).
    const hasLocalInUrl = LOCAL_KEYS_BY_ROUTE[route]?.some(k => {
        const urlKey = (SINGLE_KEY as unknown as Record<string,string>)[k];
        if (!urlKey) return urlParams.has(k) || urlParams.has('pilots') || urlParams.has('factions') || urlParams.has('ships');
        return urlParams.has(urlKey) || (k==='selectedFactions' && urlParams.has('factions')) || (k==='selectedShips' && urlParams.has('ships')) || (k==='selectedPilots' && urlParams.has('pilots'));
    });
    if (hasLocalInUrl) { clearLocalKeysForRoutesExcept(route); return; }
    try {
        const raw = localStorage.getItem(localStorageKey(route));
        if (!raw) {
            // First visit to this route and no URL locals -> ensure other routes' locals don't bleed into this page.
            clearLocalKeysForRoutesExcept(route);
            return;
        }
        // Isolate: clear other routes' locals, then hydrate this route's saved snapshot.
        clearLocalKeysForRoutesExcept(route);
        const snap = JSON.parse(raw) as Record<string, unknown>;
        applyLocalSnapshot(route, snap);
    } catch(e){ console.warn('restoreLocalFilters failed', e); }
}


export const filters = {
    get dataSource() { return dataSource; },
    set dataSource(v: 'xwa' | 'legacy') {
        dataSource = v;
        if (typeof localStorage !== 'undefined') {
            try { localStorage.setItem('m3tacron:dataSource', v); } catch (e) {}
        }
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
    // YASB-inspired pilot/upgrade filters
    get slotCounts() { return slotCounts; }, set slotCounts(v: string) { slotCounts = v; },
    get slotCountMode() { return slotCountMode; }, set slotCountMode(v: 'any' | 'all') { slotCountMode = v; },
    get selectedSlots() { return selectedSlots; }, set selectedSlots(v: string[]) { selectedSlots = v; },
    get slotFilterMode() { return slotFilterMode; }, set slotFilterMode(v: 'any' | 'all') { slotFilterMode = v; },
    get hasMultipleSlots() { return hasMultipleSlots; }, set hasMultipleSlots(v: boolean) { hasMultipleSlots = v; },
    get selectedKeywords() { return selectedKeywords; }, set selectedKeywords(v: string[]) { selectedKeywords = v; },
    get keywordFilterMode() { return keywordFilterMode; }, set keywordFilterMode(v: 'any' | 'all') { keywordFilterMode = v; },
    get actionPairs() { return actionPairs; }, set actionPairs(v: string) { actionPairs = v; },
    get actionPairMode() { return actionPairMode; }, set actionPairMode(v: 'any' | 'all') { actionPairMode = v; },
    get selectedActions() { return selectedActions; }, set selectedActions(v: string[]) { selectedActions = v; },
    get actionFilterMode() { return actionFilterMode; }, set actionFilterMode(v: 'any' | 'all') { actionFilterMode = v; },
    get selectedLinkedActions() { return selectedLinkedActions; }, set selectedLinkedActions(v: string[]) { selectedLinkedActions = v; },
    get linkedActionFilterMode() { return linkedActionFilterMode; }, set linkedActionFilterMode(v: 'any' | 'all') { linkedActionFilterMode = v; },
    get frontArcMin() { return frontArcMin; }, set frontArcMin(v: string) { frontArcMin = v; },
    get frontArcMax() { return frontArcMax; }, set frontArcMax(v: string) { frontArcMax = v; },
    get singleTurretMin() { return singleTurretMin; }, set singleTurretMin(v: string) { singleTurretMin = v; },
    get singleTurretMax() { return singleTurretMax; }, set singleTurretMax(v: string) { singleTurretMax = v; },
    get doubleTurretMin() { return doubleTurretMin; }, set doubleTurretMin(v: string) { doubleTurretMin = v; },
    get doubleTurretMax() { return doubleTurretMax; }, set doubleTurretMax(v: string) { doubleTurretMax = v; },
    get fullFrontMin() { return fullFrontMin; }, set fullFrontMin(v: string) { fullFrontMin = v; },
    get fullFrontMax() { return fullFrontMax; }, set fullFrontMax(v: string) { fullFrontMax = v; },
    get rearArcMin() { return rearArcMin; }, set rearArcMin(v: string) { rearArcMin = v; },
    get rearArcMax() { return rearArcMax; }, set rearArcMax(v: string) { rearArcMax = v; },
    get bullseyeMin() { return bullseyeMin; }, set bullseyeMin(v: string) { bullseyeMin = v; },
    get bullseyeMax() { return bullseyeMax; }, set bullseyeMax(v: string) { bullseyeMax = v; },
    get chargesMin() { return chargesMin; }, set chargesMin(v: string) { chargesMin = v; },
    get chargesMax() { return chargesMax; }, set chargesMax(v: string) { chargesMax = v; },
    get isRecurring() { return isRecurring; }, set isRecurring(v: boolean) { isRecurring = v; },
    get isNotRecurring() { return isNotRecurring; }, set isNotRecurring(v: boolean) { isNotRecurring = v; },
    get forceMin() { return forceMin; }, set forceMin(v: string) { forceMin = v; },
    get forceMax() { return forceMax; }, set forceMax(v: string) { forceMax = v; },
    get selectedUsedSlots() { return selectedUsedSlots; }, set selectedUsedSlots(v: string[]) { selectedUsedSlots = v; },
    get usedSlotFilterMode() { return usedSlotFilterMode; }, set usedSlotFilterMode(v: 'any' | 'all') { usedSlotFilterMode = v; },
    get selectedUsedDoubleSlots() { return selectedUsedDoubleSlots; }, set selectedUsedDoubleSlots(v: string[]) { selectedUsedDoubleSlots = v; },
    get usedDoubleSlotFilterMode() { return usedDoubleSlotFilterMode; }, set usedDoubleSlotFilterMode(v: 'any' | 'all') { usedDoubleSlotFilterMode = v; },
    get onlyMultiSlot() { return onlyMultiSlot; }, set onlyMultiSlot(v: boolean) { onlyMultiSlot = v; },
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
