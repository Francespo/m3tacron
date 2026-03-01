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

// Active filter chips (derived)
function getActiveChips(): { key: string; label: string }[] {
    const chips: { key: string; label: string }[] = [];
    if (dateStart) chips.push({ key: 'dateStart', label: `From ${dateStart}` });
    if (dateEnd) chips.push({ key: 'dateEnd', label: `To ${dateEnd}` });
    for (const c of selectedContinents) chips.push({ key: `continent:${c}`, label: c });
    for (const c of selectedCountries) chips.push({ key: `country:${c}`, label: c });
    for (const c of selectedCities) chips.push({ key: `city:${c}`, label: c });
    for (const f of selectedFormats) chips.push({ key: `format:${f}`, label: f });
    if (searchName) chips.push({ key: 'search', label: `"${searchName}"` });
    return chips;
}

function removeChip(key: string) {
    if (key === 'dateStart') dateStart = '';
    else if (key === 'dateEnd') dateEnd = '';
    else if (key === 'search') searchName = '';
    else if (key.startsWith('continent:'))
        selectedContinents = selectedContinents.filter(c => c !== key.slice(10));
    else if (key.startsWith('country:'))
        selectedCountries = selectedCountries.filter(c => c !== key.slice(8));
    else if (key.startsWith('city:'))
        selectedCities = selectedCities.filter(c => c !== key.slice(5));
    else if (key.startsWith('format:'))
        selectedFormats = selectedFormats.filter(f => f !== key.slice(7));
}

function resetAll() {
    dateStart = '';
    dateEnd = '';
    selectedContinents = [];
    selectedCountries = [];
    selectedCities = [];
    selectedFormats = [];
    searchName = '';
}

export const filters = {
    get dataSource() { return dataSource; },
    set dataSource(v: 'xwa' | 'legacy') { dataSource = v; },
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
    get activeChips() { return getActiveChips(); },
    removeChip,
    resetAll
};
