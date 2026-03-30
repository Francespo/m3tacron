<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import SortSelector from "$lib/components/SortSelector.svelte";
    import AdvancedFilters from "$lib/components/AdvancedFilters.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import PilotCard from "$lib/components/PilotCard.svelte";
    import UpgradeCard from "$lib/components/UpgradeCard.svelte";
    import {
        getWinRateColor,
        ALL_FACTIONS,
        getFactionColor,
        getFactionChar,
        getFactionLabel,
    } from "$lib/data/factions";
    import { filters } from "$lib/stores/filters.svelte";
    import { goto } from "$app/navigation";
    import { xwingData } from "$lib/stores/xwingData.svelte";

    let { data } = $props();

    let page = $state(1);
    let sortBy = $state("Popularity");
    let sortDirection = $state("desc");
    let textSearch = $state("");
    let selectedFactions = $state<string[]>([]);
    let factionOpen = $state(false);
    const size = 20;

    let items = $derived(data.items ?? []);
    let total = $derived(data.total ?? 0);
    let isXwa = $derived(filters.dataSource === "xwa");

    let isAdvanced = $state(false);

    // Let URL load logic handle the tab, we will drive updates
    $effect(() => {
        // Ensure data is loaded
        xwingData.setSource(filters.dataSource as any);

        const params = new URLSearchParams();
        params.set("tab", data.tab);
        params.set("page", String(page - 1));
        params.set("size", String(size));
        params.set("data_source", filters.dataSource);
        params.set("sort_metric", sortBy);
        params.set("sort_direction", sortDirection);
        if (textSearch) params.set("search", textSearch);
        for (const format of filters.selectedFormats)
            params.append("formats", format);
        for (const f of selectedFactions) params.append("factions", f);
        for (const s of filters.selectedShips) params.append("ships", s);
        for (const p of filters.selectedSources)
            params.append("sources", p);
        for (const c of filters.selectedContinents)
            params.append("continent", c);
        for (const c of filters.selectedCountries) params.append("country", c);
        for (const c of filters.selectedCities) params.append("city", c);
        if (filters.dateStart) params.set("date_start", filters.dateStart);
        if (filters.dateEnd) params.set("date_end", filters.dateEnd);

        // Advanced Filters
        if (filters.pointsMin) params.set("points_min", filters.pointsMin);
        if (filters.pointsMax) params.set("points_max", filters.pointsMax);
        if (filters.loadoutMin && filters.dataSource === "xwa")
            params.set("loadout_min", filters.loadoutMin);
        if (filters.loadoutMax && filters.dataSource === "xwa")
            params.set("loadout_max", filters.loadoutMax);
        if (filters.isUnique) params.set("is_unique", "true");
        if (filters.isLimited) params.set("is_limited", "true");
        if (filters.isGeneric) params.set("is_not_limited", "true");
        for (const b of filters.selectedBaseSizes)
            params.append("base_sizes", b);

        if (data.tab === "pilots") {
            if (filters.initMin) params.set("init_min", filters.initMin);
            if (filters.initMax) params.set("init_max", filters.initMax);
            if (filters.hullMin) params.set("hull_min", filters.hullMin);
            if (filters.hullMax) params.set("hull_max", filters.hullMax);
            if (filters.shieldsMin)
                params.set("shields_min", filters.shieldsMin);
            if (filters.shieldsMax)
                params.set("shields_max", filters.shieldsMax);
            if (filters.agilityMin)
                params.set("agility_min", filters.agilityMin);
            if (filters.agilityMax)
                params.set("agility_max", filters.agilityMax);
            if (filters.attackMin) params.set("attack_min", filters.attackMin);
            if (filters.attackMax) params.set("attack_max", filters.attackMax);
        }
        goto(`?${params.toString()}`, {
            keepFocus: true,
            noScroll: true,
            replaceState: true,
        });
    });

    function prevPage() {
        if (page > 1) page--;
    }
    function nextPage() {
        if (page * size < total) page++;
    }

    function toggleFaction(f: string) {
        if (selectedFactions.includes(f)) {
            selectedFactions = selectedFactions.filter((x) => x !== f);
        } else {
            selectedFactions = [...selectedFactions, f];
        }
    }
</script>

{#snippet cardFilters()}
    <div class="space-y-3">
        <div class="flex items-center gap-2">
            <span
                class="text-xs font-bold tracking-widest text-primary font-mono"
            >
                CARD FILTERS
            </span>
        </div>

        <!-- Basic / Advanced toggle -->
        <div
            class="flex bg-black border border-border-dark rounded-md overflow-hidden"
        >
            <button
                class="flex-1 py-1 text-xs font-mono text-center transition-colors {!isAdvanced
                    ? 'bg-[#ffffff14] text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => (isAdvanced = false)}>Basic</button
            >
            <button
                class="flex-1 py-1 text-xs font-mono text-center transition-colors {isAdvanced
                    ? 'bg-[#ffffff14] text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => (isAdvanced = true)}>Advanced</button
            >
        </div>

        {#if isAdvanced}
            <AdvancedFilters isPilotsTab={data.tab === "pilots"} />
        {/if}

        <SortSelector
            bind:sortBy
            bind:sortDirection
            options={[
                { value: "Popularity", label: "Popularity (Lists)" },
                { value: "Win Rate", label: "Win Rate" },
                { value: "Games", label: "Popularity (Games)" },
                { value: "Name", label: "Name" },
                { value: "Cost", label: "Points Cost" },
                ...(data.tab === "pilots" && isXwa
                    ? [{ value: "Loadout", label: "Loadout Value" }]
                    : []),
            ]}
        />

        <!-- Text Search -->
        <div class="space-y-1">
            <span
                class="text-xs font-mono font-bold tracking-wider text-secondary"
                >Text Search</span
            >
            <input
                type="text"
                placeholder="Search card text"
                class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary placeholder:text-[#555] focus:border-primary focus:outline-none"
                bind:value={textSearch}
            />
        </div>

        <!-- Faction -->
        <div class="border-b border-border-dark mt-1">
            <button
                class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
                onclick={() => (factionOpen = !factionOpen)}
            >
                <div class="flex items-center gap-2">
                    <span class="text-xs font-mono font-bold tracking-wider">
                        Faction
                    </span>
                    {#if selectedFactions.length > 0}
                        <span
                            class="text-[10px] bg-white/10 text-secondary px-1.5 rounded-full font-mono"
                        >
                            {selectedFactions.length}
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
                    class="transition-transform {factionOpen
                        ? 'rotate-180'
                        : ''}"><path d="m6 9 6 6 6-6" /></svg
                >
            </button>

            {#if factionOpen}
                <div class="pb-3 space-y-1 max-h-[180px] overflow-y-auto pl-2">
                    {#each ALL_FACTIONS as f}
                        <label
                            class="flex items-center gap-2 py-1.5 cursor-pointer text-xs text-secondary hover:text-primary"
                        >
                            <input
                                type="checkbox"
                                class="rounded border-border-dark bg-black w-4 h-4"
                                checked={selectedFactions.includes(f)}
                                onchange={() => toggleFaction(f)}
                            />
                            <span
                                class="font-xwing text-sm"
                                style="color: {getFactionColor(f)};"
                                >{getFactionChar(f)}</span
                            >
                            <span class="font-mono">{getFactionLabel(f)}</span>
                        </label>
                    {/each}
                </div>
            {/if}
        </div>

        {#if data.tab === "pilots"}
            <ShipChassisFilter {selectedFactions} />
        {/if}
    </div>
{/snippet}

<svelte:head>
    <title>Cards | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <FilterPanel extra={cardFilters} />

    <main class="flex-1 p-6 md:p-8">
        <!-- Tabs: Pilots / Upgrades -->
        <div class="flex items-center gap-6 mb-6">
            <button
                class="text-lg font-sans font-bold transition-colors {data.tab ===
                'pilots'
                    ? 'text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => {
                    import("$app/navigation").then(({ goto }) =>
                        goto("?tab=pilots&page=0", {
                            keepFocus: true,
                            noScroll: true,
                            replaceState: true,
                        }),
                    );
                }}
            >
                Pilots
            </button>
            <button
                class="text-lg font-sans font-bold transition-colors {data.tab ===
                'upgrades'
                    ? 'text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => {
                    import("$app/navigation").then(({ goto }) =>
                        goto("?tab=upgrades&page=0", {
                            keepFocus: true,
                            noScroll: true,
                            replaceState: true,
                        }),
                    );
                }}
            >
                Upgrades
            </button>
        </div>

        <!-- Card Grid -->
        <div
            class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
        >
            {#each items as card}
                <a
                    href={`/${data.tab === "pilots" ? "pilot" : "upgrade"}/${card.xws}`}
                    class="block h-full group"
                >
                    {#if data.tab === "pilots"}
                        <PilotCard pilot={card} />
                    {:else}
                        <UpgradeCard upgrade={card} />
                    {/if}
                </a>
            {/each}
        </div>

        <!-- Pagination -->
        {#if total > size}
            <div
                class="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-border-dark"
            >
                <button
                    class="min-h-11 px-4 py-2 text-sm font-mono border border-border-dark rounded hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                    onclick={prevPage}
                    disabled={page <= 1}>← Prev</button
                >
                <span class="text-xs font-mono text-secondary">Page {page}</span
                >
                <button
                    class="min-h-11 px-4 py-2 text-sm font-mono border border-border-dark rounded hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                    onclick={nextPage}
                    disabled={page * size >= total}>Next →</button
                >
            </div>
        {/if}
    </main>
</div>
