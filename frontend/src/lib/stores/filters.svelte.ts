/**
 * Global Filter State.
 * Mirrors Reflex GlobalFilterState across all pages.
 */

// Reactive state using Svelte 5 runes (module-level $state)
let dataSource = $state<'xwa' | 'legacy'>('xwa');
let includeEpic = $state(false);
let dateStart = $state('');
let dateEnd = $state('');
let selectedContinents = $state<string[]>([]);
let selectedCountries = $state<string[]>([]);
let selectedCities = $state<string[]>([]);
let selectedFormats = $state<string[]>([]);
let searchName = $state('');
let selectedPlatforms = $state<string[]>([]);
let selectedShips = $state<string[]>([]);

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

function getActiveChips(): { key: string; label: string }[] {
    const chips: { key: string; label: string }[] = [];
    if (dateStart) chips.push({ key: 'dateStart', label: `From ${dateStart}` });
    if (dateEnd) chips.push({ key: 'dateEnd', label: `To ${dateEnd}` });
    for (const c of selectedContinents) chips.push({ key: `continent:${c}`, label: c });
    for (const c of selectedCountries) chips.push({ key: `country:${c}`, label: c });
    for (const c of selectedCities) chips.push({ key: `city:${c}`, label: c });
    for (const p of selectedPlatforms) chips.push({ key: `platform:${p}`, label: p });
    for (const s of selectedShips) chips.push({ key: `ship:${s}`, label: `Ship: ${s}` });

    // Map format IDs to labels
    const formatLabels: Record<string, string> = {
        'amg': 'AMG', 'xwa': 'XWA', 'legacy_x2po': 'Legacy (X2PO)',
        'legacy_xlc': 'Legacy (XLC)', 'ffg': 'FFG', 'other': 'Unknown'
    };
    for (const f of selectedFormats) {
        // Skip default active format chips if we want, but usually it's good to show them
        chips.push({ key: `format:${f}`, label: formatLabels[f] || f });
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
    else if (key.startsWith('format:'))
        selectedFormats = selectedFormats.filter(f => f !== key.slice(7));
    else if (key.startsWith('ship:'))
        selectedShips = selectedShips.filter(s => s !== key.slice(5));
}

function resetAll() {
    dateStart = '';
    dateEnd = '';
    selectedContinents = [];
    selectedCountries = [];
    selectedCities = [];
    selectedPlatforms = [];
    selectedShips = [];

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
    get selectedPlatforms() { return selectedPlatforms; },
    set selectedPlatforms(v: string[]) { selectedPlatforms = v; },
    get selectedShips() { return selectedShips; },
    set selectedShips(v: string[]) { selectedShips = v; },
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
    get activeChips() { return getActiveChips(); },
    removeChip,
    resetAll
};
