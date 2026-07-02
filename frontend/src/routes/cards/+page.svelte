<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import AdvancedFilters from "$lib/components/AdvancedFilters.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import PilotCard from "$lib/components/PilotCard.svelte";
    import UpgradeCard from "$lib/components/UpgradeCard.svelte";
    import Toggle from "$lib/components/Toggle.svelte";
    import {
        getWinRateColor,
        ALL_FACTIONS,
        getFactionLabel,
    } from "$lib/data/factions";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import DebouncedTextInput from "$lib/components/DebouncedTextInput.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { goto } from "$app/navigation";
    import FactionIcon from "$lib/components/FactionIcon.svelte";

    let { data } = $props();

    let filterOpen = $state(false);
    let page = $state(1);
    let factionOpen = $state(false);
    const size = 20;

    let total = $state(0);
    let isXwa = $derived(filters.dataSource === "xwa");

    let isAdvanced = $state(false);

    // Track total from the latest promise resolution (for nextPage guard).
    // Clamp to a non-negative integer: backend already clamps (Phase 0) but
    // a missing/garbage value should never produce a negative `total`.
    $effect(() => {
        data.itemsPromise.then((resolved: any) => {
            total = Math.max(0, Math.floor(Number(resolved.total ?? 0)));
        });
    });

    // Default sort: when the store starts empty (no URL, no prior visit),
    // set a real metric so the SortBy in the main content header always
    // has a valid selection. "Popularity" is a sensible default for both
    // Pilots and Upgrades.
    $effect(() => {
        if (!filters.sortBy) {
            filters.sortBy = "Popularity";
        }
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

        <!-- Sort By was moved to the main content section header
             (rendered by SortBy) to give the list a single canonical
             sort control. The old sidebar SortSelector was removed. -->

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
                <div
                    class="pb-3 space-y-1 max-h-[180px] overflow-y-auto custom-scrollbar pl-2"
                >
                    {#each ALL_FACTIONS as f}
                        <label
                            class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                        >
                            <Toggle
                                size="xs"
                                ariaLabel={`Toggle faction ${getFactionLabel(f)}`}
                                checked={filters.selectedFactions.includes(f)}
                                onchange={() => toggleFaction(f)}
                            />
                            <FactionIcon faction={f} size="sm" />
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
        <h1 class="text-3xl font-sans font-bold text-primary mb-1">
            Cards
        </h1>

        <!-- Tabs: Pilots / Upgrades + SortBy -->
        <div class="flex items-center justify-between gap-4 flex-wrap mb-6">
            <div class="flex items-center gap-6">
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

            <SortBy
                value={filters.sortBy || "Popularity"}
                direction={filters.sortDirection}
                options={[
                    { value: "Name", label: "Name" },
                    { value: "Cost", label: "Points Cost" },
                    { value: "Games", label: "Games" },
                    { value: "Popularity", label: "Lists" },
                    { value: "Win Rate", label: "Win Rate" },
                ]}
                onChange={(v, d) => {
                    filters.sortBy = v;
                    filters.sortDirection = d;
                }}
            />
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
            {@const resolvedTotal = Math.max(0, Math.floor(Number(resolved.total ?? 0)))}
            {@const cardItems = (resolved.items ?? []).map((c: any) => ({
                // Sanitize numeric stats before passing into the card
                // components. Phase 0 backend already clamps at the source,
                // but defensive guards here mean a stale or out-of-band
                // payload can never show "-3 games" or "NaN%".
                ...c,
                games_count: Math.max(0, Number(c?.games_count ?? 0)),
                list_count: Math.max(0, Number(c?.list_count ?? c?.lists ?? 0)),
                different_lists_count: Math.max(
                    0,
                    Number(c?.different_lists_count ?? c?.different_list_count ?? 0),
                ),
                wins: Math.max(0, Number(c?.wins ?? 0)),
            }))}
            <!-- Result count in the same "N x Found" style as squadrons,
                 lists, ships, and tournaments listings. -->
            <p class="text-secondary font-mono text-sm mb-6">
                {resolvedTotal} {data.tab === "pilots" ? "Pilots" : "Upgrades"} Found
            </p>
            <div
                class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
            >
                {#each cardItems as card (card.xws)}
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
                        class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                        onclick={prevPage}
                        disabled={page <= 1}>← Prev</button
                    >
                    <span class="text-xs font-mono text-secondary">Page {page}</span
                    >
                    <button
                        class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
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
