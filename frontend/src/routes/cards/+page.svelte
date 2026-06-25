<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
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
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import DebouncedTextInput from "$lib/components/DebouncedTextInput.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { goto } from "$app/navigation";

    let { data } = $props();

    let filterOpen = $state(false);
    let page = $state(1);
    let factionOpen = $state(false);
    const size = 20;

    let total = $state(0);
    let isXwa = $derived(filters.dataSource === "xwa");

    let isAdvanced = $state(false);

    // Track total from the latest promise resolution (for nextPage guard)
    $effect(() => {
        data.itemsPromise.then((resolved: any) => {
            total = Number(resolved.total ?? 0);
        });
    });

    // Ensure data is loaded for the current data source, then push the
    // store + route-local overlay (page, size, tab) to the URL.
    $effect(() => {
        xwingData.setSource(filters.dataSource as any);

        const params = filters.toSearchParams('cards');
        // Overlay route-local URL state (page is 0-indexed in the URL,
        // 1-indexed in the UI; tab/size are route-local concerns).
        params.set('page', String(page - 1));
        params.set('size', String(size));
        if (data.tab) params.set('tab', data.tab);
        scheduleSync(0, params);
    });

    function prevPage() {
        if (page > 1) page--;
    }
    function nextPage() {
        if (page * size < total) page++;
    }

    function toggleFaction(f: string) {
        if (filters.selectedFactions.includes(f)) {
            filters.selectedFactions = filters.selectedFactions.filter(
                (x) => x !== f,
            );
        } else {
            filters.selectedFactions = [...filters.selectedFactions, f];
        }
    }
</script>

{#snippet filterBody()}
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
            bind:sortBy={filters.sortBy}
            bind:sortDirection={filters.sortDirection}
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
            <DebouncedTextInput
                value={filters.searchName}
                onDebouncedChange={(v) => {
                    filters.searchName = v;
                    scheduleSync(250);
                }}
                placeholder="Search card text"
                ariaLabel="Search card text"
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
                    {#if filters.selectedFactions.length > 0}
                        <span
                            class="text-[10px] bg-white/10 text-secondary px-1.5 rounded-full font-mono"
                        >
                            {filters.selectedFactions.length}
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
                            class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                        >
                            <input
                                type="checkbox"
                                class="rounded border-border-dark bg-black w-3 h-3"
                                checked={filters.selectedFactions.includes(f)}
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
            <ShipChassisFilter selectedFactions={filters.selectedFactions} />
        {/if}
    </div>
{/snippet}

<svelte:head>
    <title>Cards | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <FilterPanel>
        {@render filterBody()}
    </FilterPanel>

    <MobileFilterTrigger
        activeCount={filters.activeChips.length}
        onClick={() => (filterOpen = true)}
    />
    <MobileFilterDrawer
        open={filterOpen}
        onClose={() => (filterOpen = false)}
        title="Filters"
        activeCount={filters.activeChips.length}
    >
        {@render filterBody()}
    </MobileFilterDrawer>

    <main class="flex-1 p-6 md:p-8 pb-20 lg:pb-8">
        <!-- Tabs: Pilots / Upgrades -->
        <div class="flex items-center gap-6 mb-6">
            <button
                class="text-lg font-sans font-bold transition-colors {data.tab ===
                'pilots'
                    ? 'text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => {
                    goto("?tab=pilots&page=0", {
                        keepFocus: true,
                        noScroll: true,
                        replaceState: true,
                    });
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
                    goto("?tab=upgrades&page=0", {
                        keepFocus: true,
                        noScroll: true,
                        replaceState: true,
                    });
                }}
            >
                Upgrades
            </button>
        </div>

        <!-- Card Grid -->
        {#await data.itemsPromise}
            <div
                class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
            >
                {#each Array(6) as _}
                    <div class="animate-pulse bg-[#ffffff06] rounded-md h-48 border border-border-dark"></div>
                {/each}
            </div>
        {:then resolved}
            {@const resolvedTotal = Number(resolved.total ?? 0)}
            {@const cardItems = resolved.items ?? []}
            <div
                class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
            >
                {#each cardItems as card}
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
            {#if resolvedTotal > size}
                <div
                    class="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-border-dark"
                >
                    <button
                        class="px-3 py-1 text-xs font-mono border border-border-dark rounded hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                        onclick={prevPage}
                        disabled={page <= 1}>← Prev</button
                    >
                    <span class="text-xs font-mono text-secondary">Page {page}</span
                    >
                    <button
                        class="px-3 py-1 text-xs font-mono border border-border-dark rounded hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                        onclick={nextPage}
                        disabled={page * size >= resolvedTotal}>Next →</button
                    >
                </div>
            {/if}
        {:catch error}
            <p class="text-red-400 font-mono text-sm">
                Failed to load cards: {error.message}
            </p>
        {/await}
    </main>
</div>
