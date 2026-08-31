<script lang="ts">
    import { onMount } from "svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import { API_BASE } from "$lib/api";
    import { cachedFetchJson } from "$lib/api/cache";
    import { getFormatFullLabel } from "$lib/data/formats";
    import DebouncedTextInput from "./DebouncedTextInput.svelte";
    import DateRangeField from "./DateRangeField.svelte";
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
            locationHierarchy = await cachedFetchJson(
                `${API_BASE}/tournaments/locations`,
            );
        } catch (e) {
            console.error("Failed to load locations", e);
        }
    });

    let availableContinents = $derived(Object.keys(locationHierarchy).sort());

    let availableCountries = $derived.by(() => {
        let countries = new Set<string>();
        let conts =
            filters.tournamentContinents.length > 0
                ? filters.tournamentContinents
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
            filters.tournamentContinents.length > 0
                ? filters.tournamentContinents
                : availableContinents;
        for (const c of conts) {
            if (!locationHierarchy[c]) continue;
            let countryKeys =
                filters.tournamentCountries.length > 0
                    ? filters.tournamentCountries.filter(
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
                { id: "legacy_pandorum", label: getFormatFullLabel("legacy_pandorum") },
                { id: "ffg", label: getFormatFullLabel("ffg") },
            ],
        },
        {
            label: "Unknown",
            formats: [{ id: "other", label: getFormatFullLabel("other") }],
        },
    ];

    function toggleContinent(c: string) {
        if (filters.tournamentContinents.includes(c)) {
            filters.tournamentContinents = filters.tournamentContinents.filter(
                (x) => x !== c,
            );
        } else {
            filters.tournamentContinents = [...filters.tournamentContinents, c];
        }
    }

    function toggleCountry(c: string) {
        if (filters.tournamentCountries.includes(c)) {
            filters.tournamentCountries = filters.tournamentCountries.filter(
                (x) => x !== c,
            );
        } else {
            filters.tournamentCountries = [...filters.tournamentCountries, c];
        }
    }

    function toggleCity(c: string) {
        if (filters.tournamentCities.includes(c)) {
            filters.tournamentCities = filters.tournamentCities.filter(
                (x) => x !== c,
            );
        } else {
            filters.tournamentCities = [...filters.tournamentCities, c];
        }
    }

    function toggleSource(pId: string) {
        if (filters.tournamentSources.includes(pId)) {
            filters.tournamentSources = filters.tournamentSources.filter(
                (x) => x !== pId,
            );
        } else {
            filters.tournamentSources = [...filters.tournamentSources, pId];
        }
    }

    function toggleFormat(fId: string) {
        if (filters.tournamentFormats.includes(fId)) {
            filters.tournamentFormats = filters.tournamentFormats.filter(
                (x) => x !== fId,
            );
        } else {
            filters.tournamentFormats = [...filters.tournamentFormats, fId];
        }
    }
</script>

<div class="w-full space-y-4">
    <div class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-5 items-start">
    <div class="relative rounded-xl border border-white/5 bg-black/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] overflow-hidden self-start h-fit">
        <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
        <button type="button" onclick={() => (dateOpen = !dateOpen)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
            <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">Date Range</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {dateOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
        </button>
        {#if dateOpen}<div class="px-3.5 pb-3.5 pt-1"><DateRangeField hideLabel={true} bind:startDate={filters.tournamentDateStart} bind:endDate={filters.tournamentDateEnd} /></div>{/if}
    </div>

    <div class="relative rounded-xl border border-white/5 bg-black/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] overflow-hidden lg:col-span-2 2xl:col-span-1 2xl:col-start-3 2xl:row-start-1 self-start h-fit">
        <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
        <button type="button" onclick={() => (locationOpen = !locationOpen)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
            <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">Location</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {locationOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
        </button>
        {#if locationOpen}<div class="px-3.5 pb-3.5 pt-1 space-y-3 text-xs">
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
                                        checked={filters.tournamentContinents.includes(
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
                                        checked={filters.tournamentCountries.includes(
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
                                        checked={filters.tournamentCities.includes(
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
            </div>{/if}
    </div>

    <!-- Format — card style -->
    <div class="relative rounded-xl border border-white/5 bg-black/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] overflow-hidden self-start h-fit">
        <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
        <button type="button" onclick={() => (formatOpen = !formatOpen)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
            <span class="flex items-center gap-2 text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">Format {#if filters.tournamentFormats.length > 0}<span class="min-w-5 h-5 px-1 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center">{filters.tournamentFormats.length}</span>{/if}</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {formatOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
        </button>
        {#if formatOpen}<div class="px-3.5 pb-3.5 pt-1 space-y-3 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">
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
                                    checked={filters.tournamentFormats.includes(
                                        f.id,
                                    )}
                                    onchange={() => toggleFormat(f.id)}
                                />
                                <span class="font-mono">{f.label}</span>
                            </label>
                        {/each}
                    </div>
                {/each}
            </div>{/if}
    </div>

    <div class="relative rounded-xl border border-white/5 bg-black/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] overflow-hidden self-start h-fit">
        <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
        <button type="button" onclick={() => (sourceOpen = !sourceOpen)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
            <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">Source</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {sourceOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
        </button>
        {#if sourceOpen}<div class="px-3.5 pb-3.5 pt-1 space-y-1">
                {#each sources as source}
                    <label
                        class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                    >
                        <Toggle
                            size="xs"
                            ariaLabel={`Toggle source ${source.id}`}
                            checked={filters.tournamentSources.includes(
                                source.id,
                            )}
                            onchange={() => toggleSource(source.id)}
                        />
                        <span class="font-mono">{source.label}</span>
                    </label>
                {/each}
            </div>{/if}
    </div>

    </div>

    <div class="relative rounded-xl border border-white/5 bg-black/20 overflow-hidden lg:col-span-2 2xl:col-span-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] self-start h-fit">
        <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
        <div class="p-3.5">
        <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">Search Name</span
        >
        <DebouncedTextInput
            value={filters.tournamentSearchName}
            onDebouncedChange={(v) => {
                filters.tournamentSearchName = v;
                scheduleSync(250);
            }}
            placeholder="Search name..."
            ariaLabel="Search tournament name"
        />
        </div>
    </div>
</div>
