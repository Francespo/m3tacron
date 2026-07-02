<script lang="ts">
    import { onMount } from "svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import { API_BASE } from "$lib/api";
    import { getFormatFullLabel } from "$lib/data/formats";
    import DebouncedTextInput from "./DebouncedTextInput.svelte";
    import Toggle from "./Toggle.svelte";

    let dateOpen = $state(false);
    let locationOpen = $state(false);
    let formatOpen = $state(false);
    let sourceOpen = $state(false);

    let locationSearch = $state("");
    let locationHierarchy = $state<Record<string, Record<string, string[]>>>(
        {},
    );

    onMount(async () => {
        try {
            const res = await fetch(`${API_BASE}/tournaments/locations`);
            if (res.ok) {
                locationHierarchy = await res.json();
            }
        } catch (e) {
            console.error("Failed to load locations", e);
        }
    });

    let availableContinents = $derived(Object.keys(locationHierarchy).sort());

    let availableCountries = $derived.by(() => {
        let countries = new Set<string>();
        let conts =
            filters.selectedContinents.length > 0
                ? filters.selectedContinents
                : availableContinents;
        for (const c of conts) {
            if (locationHierarchy[c]) {
                Object.keys(locationHierarchy[c]).forEach((co) =>
                    countries.add(co),
                );
            }
        }
        return Array.from(countries).sort();
    });

    let availableCities = $derived.by(() => {
        let cities = new Set<string>();
        let conts =
            filters.selectedContinents.length > 0
                ? filters.selectedContinents
                : availableContinents;
        for (const c of conts) {
            if (!locationHierarchy[c]) continue;
            let countryKeys =
                filters.selectedCountries.length > 0
                    ? filters.selectedCountries.filter(
                          (cO) => locationHierarchy[c][cO],
                      )
                    : Object.keys(locationHierarchy[c]);

            for (const co of countryKeys) {
                locationHierarchy[c][co]?.forEach((city) => cities.add(city));
            }
        }
        return Array.from(cities).sort();
    });

    let filteredContinents = $derived(
        availableContinents.filter((c) =>
            c.toLowerCase().includes(locationSearch.toLowerCase()),
        ),
    );
    let filteredCountries = $derived(
        availableCountries.filter((c) =>
            c.toLowerCase().includes(locationSearch.toLowerCase()),
        ),
    );
    let filteredCities = $derived(
        availableCities.filter((c) =>
            c.toLowerCase().includes(locationSearch.toLowerCase()),
        ),
    );

    const sources = [
        { id: "longshanks", label: "Longshanks" },
        { id: "listfortress", label: "ListFortress" },
        { id: "rollbetter", label: "Rollbetter" },
    ];

    // Hierarchical formats matching backend logic
    const formatGroups = [
        {
            label: "2.5",
            formats: [
                { id: "amg", label: getFormatFullLabel("amg") },
                { id: "xwa", label: getFormatFullLabel("xwa") },
            ],
        },
        {
            label: "2.0",
            formats: [
                { id: "legacy_x2po", label: getFormatFullLabel("legacy_x2po") },
                { id: "legacy_xlc", label: getFormatFullLabel("legacy_xlc") },
                { id: "ffg", label: getFormatFullLabel("ffg") },
            ],
        },
        {
            label: "Unknown",
            formats: [{ id: "other", label: getFormatFullLabel("other") }],
        },
    ];

    function toggleContinent(c: string) {
        if (filters.selectedContinents.includes(c)) {
            filters.selectedContinents = filters.selectedContinents.filter(
                (x) => x !== c,
            );
        } else {
            filters.selectedContinents = [...filters.selectedContinents, c];
        }
    }

    function toggleCountry(c: string) {
        if (filters.selectedCountries.includes(c)) {
            filters.selectedCountries = filters.selectedCountries.filter(
                (x) => x !== c,
            );
        } else {
            filters.selectedCountries = [...filters.selectedCountries, c];
        }
    }

    function toggleCity(c: string) {
        if (filters.selectedCities.includes(c)) {
            filters.selectedCities = filters.selectedCities.filter(
                (x) => x !== c,
            );
        } else {
            filters.selectedCities = [...filters.selectedCities, c];
        }
    }

    function toggleSource(pId: string) {
        if (filters.selectedSources.includes(pId)) {
            filters.selectedSources = filters.selectedSources.filter(
                (x) => x !== pId,
            );
        } else {
            filters.selectedSources = [...filters.selectedSources, pId];
        }
    }

    function toggleFormat(fId: string) {
        if (filters.selectedFormats.includes(fId)) {
            filters.selectedFormats = filters.selectedFormats.filter(
                (x) => x !== fId,
            );
        } else {
            filters.selectedFormats = [...filters.selectedFormats, fId];
        }
    }
</script>

<div class="w-full space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
            <span class="text-xs font-bold tracking-widest text-primary font-mono">
                TOURNAMENT FILTERS
            </span>
            <button
                type="button"
                class="group relative inline-flex items-center justify-center w-4 h-4 rounded-full text-secondary hover:text-primary focus:outline-none focus:ring-1 focus:ring-primary"
                aria-label="How tournament filters work"
            >
                <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="16" x2="12" y2="12" />
                    <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                <div
                    class="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-64 p-2 bg-terminal-panel border border-border-dark rounded-md text-[10px] font-mono text-secondary opacity-0 invisible group-hover:opacity-100 group-hover:visible group-focus-within:opacity-100 group-focus-within:visible transition-opacity z-50 pointer-events-none"
                >
                    Tournament filters are applied to the page's input data. The
                    page-specific filters and the tournament filters are
                    complementary — for example, if you filter for tournaments
                    on a list page, only data from tournaments that match your
                    filter is shown.
                </div>
            </button>
        </div>
    </div>

    <!-- Date Range Accordion -->
    <div class="border-b border-border-dark">
        <button
            class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
            onclick={() => (dateOpen = !dateOpen)}
        >
            <span class="text-xs font-mono font-bold tracking-wider"
                >Date Range</span
            >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="transition-transform {dateOpen ? 'rotate-180' : ''}"
                ><path d="m6 9 6 6 6-6" /></svg
            >
        </button>
        {#if dateOpen}
            <div class="pb-3 space-y-1.5 pl-2">
                <input
                    type="date"
                    class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.dateStart}
                />
                <span class="text-xs text-secondary block text-center">to</span>
                <input
                    type="date"
                    class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.dateEnd}
                />
            </div>
        {/if}
    </div>

    <!-- Location Accordion -->
    <div class="border-b border-border-dark">
        <button
            class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
            onclick={() => (locationOpen = !locationOpen)}
        >
            <span class="text-xs font-mono font-bold tracking-wider"
                >Location</span
            >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="transition-transform {locationOpen ? 'rotate-180' : ''}"
                ><path d="m6 9 6 6 6-6" /></svg
            >
        </button>
        {#if locationOpen}
            <div class="pb-3 space-y-3 pl-2 pr-1 text-xs">
                <!-- Mini Search Bar -->
                <input
                    type="text"
                    placeholder="Search locations..."
                    class="w-full bg-black border border-border-dark rounded px-2 py-1.5 font-mono text-primary focus:border-primary focus:outline-none placeholder:text-secondary/50"
                    bind:value={locationSearch}
                />

                <!-- Continents -->
                {#if filteredContinents.length > 0}
                    <div>
                        <span
                            class="font-bold text-primary font-mono tracking-wider opacity-70 uppercase block mb-1"
                            >Continents</span
                        >
                        <div class="max-h-[100px] overflow-y-auto space-y-1">
                            {#each filteredContinents as c}
                                <label
                                    class="flex items-center gap-2 cursor-pointer text-secondary hover:text-primary"
                                >
                                    <Toggle
                                        size="xs"
                                        ariaLabel={`Toggle continent ${c}`}
                                        checked={filters.selectedContinents.includes(
                                            c,
                                        )}
                                        onchange={() => toggleContinent(c)}
                                    />
                                    <span class="font-mono truncate" title={c}
                                        >{c}</span
                                    >
                                </label>
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- Countries -->
                {#if filteredCountries.length > 0}
                    <div>
                        <span
                            class="font-bold text-primary font-mono tracking-wider opacity-70 uppercase block mb-1"
                            >Countries</span
                        >
                        <div class="max-h-[120px] overflow-y-auto space-y-1">
                            {#each filteredCountries as c}
                                <label
                                    class="flex items-center gap-2 cursor-pointer text-secondary hover:text-primary"
                                >
                                    <Toggle
                                        size="xs"
                                        ariaLabel={`Toggle country ${c}`}
                                        checked={filters.selectedCountries.includes(
                                            c,
                                        )}
                                        onchange={() => toggleCountry(c)}
                                    />
                                    <span class="font-mono truncate" title={c}
                                        >{c}</span
                                    >
                                </label>
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- Cities -->
                {#if filteredCities.length > 0}
                    <div>
                        <span
                            class="font-bold text-primary font-mono tracking-wider opacity-70 uppercase block mb-1"
                            >Cities</span
                        >
                        <div class="max-h-[120px] overflow-y-auto space-y-1">
                            {#each filteredCities as c}
                                <label
                                    class="flex items-center gap-2 cursor-pointer text-secondary hover:text-primary"
                                >
                                    <Toggle
                                        size="xs"
                                        ariaLabel={`Toggle city ${c}`}
                                        checked={filters.selectedCities.includes(
                                            c,
                                        )}
                                        onchange={() => toggleCity(c)}
                                    />
                                    <span class="font-mono truncate" title={c}
                                        >{c}</span
                                    >
                                </label>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>
        {/if}
    </div>

    <!-- Format Accordion -->
    <div class="border-b border-border-dark">
        <button
            class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
            onclick={() => (formatOpen = !formatOpen)}
        >
            <div class="flex items-center gap-2">
                <span class="text-xs font-mono font-bold tracking-wider"
                    >Format</span
                >
                {#if filters.selectedFormats.length > 0}
                    <span
                        class="text-[10px] bg-white/10 text-secondary px-1.5 rounded-full font-mono"
                    >
                        {filters.selectedFormats.length}
                    </span>
                {/if}
            </div>
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="transition-transform {formatOpen ? 'rotate-180' : ''}"
                ><path d="m6 9 6 6 6-6" /></svg
            >
        </button>
        {#if formatOpen}
            <div class="pb-3 space-y-3 pl-2 max-h-[300px] overflow-y-auto pr-1">
                {#each formatGroups as group}
                    <div class="space-y-1">
                        <span
                            class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase"
                            >{group.label}</span
                        >
                        {#each group.formats as f}
                            <label
                                class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary pl-1"
                            >
                                <Toggle
                                    size="xs"
                                    ariaLabel={`Toggle format ${f.id}`}
                                    checked={filters.selectedFormats.includes(
                                        f.id,
                                    )}
                                    onchange={() => toggleFormat(f.id)}
                                />
                                <span class="font-mono">{f.label}</span>
                            </label>
                        {/each}
                    </div>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Source Filter Section -->
    <div class="border-b border-border-dark">
        <button
            class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
            onclick={() => (sourceOpen = !sourceOpen)}
        >
            <span class="text-xs font-mono font-bold tracking-wider"
                >Source</span
            >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="transition-transform {sourceOpen ? 'rotate-180' : ''}"
                ><path d="m6 9 6 6 6-6" /></svg
            >
        </button>
        {#if sourceOpen}
            <div class="pb-3 space-y-1 pl-2">
                {#each sources as source}
                    <label
                        class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                    >
                        <Toggle
                            size="xs"
                            ariaLabel={`Toggle source ${source.id}`}
                            checked={filters.selectedSources.includes(
                                source.id,
                            )}
                            onchange={() => toggleSource(source.id)}
                        />
                        <span class="font-mono">{source.label}</span>
                    </label>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Search Name -->
    <div class="space-y-1">
        <span class="text-xs font-mono font-bold tracking-wider text-secondary"
            >Search Name</span
        >
        <DebouncedTextInput
            value={filters.searchName}
            onDebouncedChange={(v) => {
                filters.searchName = v;
                scheduleSync(250);
            }}
            placeholder="Search name..."
            ariaLabel="Search tournament name"
        />
    </div>
</div>
