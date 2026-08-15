<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import AdvancedFilters from "$lib/components/AdvancedFilters.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import PilotCard from "$lib/components/PilotCard.svelte";
    import UpgradeCard from "$lib/components/UpgradeCard.svelte";
    import PendingIndicator from "$lib/components/PendingIndicator.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import Toggle from "$lib/components/Toggle.svelte";
    import {
        getWinRateColor,
        ALL_FACTIONS,
        getFactionLabel,
    } from "$lib/data/factions";
    import { invalidateAll } from "$app/navigation";
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

    // The loader streams card rows in via `itemsPromise` (non-blocking
    // navigation). `resolved` keeps the LAST good payload so filter/sort/
    // page changes never blank the list: stale rows stay visible under a
    // thin "Updating…" bar while the next query runs. Tab switches reset
    // `resolved` because pilots vs upgrades are different content types —
    // a skeleton is the honest feedback there.
    let resolved = $state<any>(null);
    let pending = $state(true);
    let failed = $state(false);
    let lastPromise: any = null;
    let lastTab: string | undefined = undefined;
    let generation = 0;
    let total = $derived(Math.max(0, Math.floor(Number(resolved?.total ?? 0))));
    let isXwa = $derived(filters.dataSource === "xwa");

    let isAdvanced = $state(false);

    $effect(() => {
        const p = data.itemsPromise;
        if (p === lastPromise) return;
        lastPromise = p;
        if (lastTab !== data.tab) {
            lastTab = data.tab;
            resolved = null;
        }
        const gen = ++generation;
        pending = true;
        failed = false;
        p.then((r: any) => {
            if (gen !== generation) return;
            resolved = r;
            pending = false;
        }).catch(() => {
            if (gen !== generation) return;
            failed = true;
            pending = false;
        });
    });

    function retry() {
        invalidateAll();
    }

    // Default sort: when the store starts empty (no URL, no prior visit),
    // set a real metric so the SortBy in the main content header always
    // has a valid selection. "Lists" is a sensible default for both
    // Pilots and Upgrades.
    $effect(() => {
        if (!filters.sortBy) {
            filters.sortBy = "Lists";
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
                    : 'text-secondary hover:text-primary active:bg-[#ffffff08]'}"
                onclick={() => (isAdvanced = false)}>Basic</button
            >
            <button
                class="flex-1 py-1 text-xs font-mono text-center transition-colors {isAdvanced
                    ? 'bg-[#ffffff14] text-primary'
                    : 'text-secondary hover:text-primary active:bg-[#ffffff08]'}"
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
                class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary active:text-primary active:bg-[#ffffff06] rounded-sm transition-colors"
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
                        : 'text-secondary hover:text-primary active:text-primary'}"
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
                        : 'text-secondary hover:text-primary active:text-primary'}"
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
                value={filters.sortBy || "Lists"}
                direction={filters.sortDirection}
                options={[
                    { value: "Name", label: "Name" },
                    { value: "Cost", label: "Points Cost" },
                    { value: "Games", label: "Games" },
                    { value: "Lists", label: "Lists" },
                    { value: "Unique Lists", label: "Unique Lists" },
                    { value: "Win Rate", label: "Win Rate" },
                ]}
                onChange={(v, d) => {
                    filters.sortBy = v;
                    filters.sortDirection = d;
                }}
            />
        </div>

        <!-- Card Grid -->
        {#if !resolved}
            {#if failed}
                <div class="mb-6">
                    <ErrorPanel
                        title="Failed to load cards"
                        onRetry={retry}
                    />
                </div>
            {:else}
                <p class="text-secondary font-mono text-sm mb-6">Loading…</p>

                <!-- Loading Skeleton (matches PilotCard / UpgradeCard shape) -->
                <div
                    class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
                >
                    {#each Array(6) as _}
                        <div
                            class="bg-terminal-panel border border-border-dark rounded-md p-4 h-48 flex flex-col gap-2"
                        >
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-16 w-full"
                            ></div>
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-3.5 w-3/4"
                            ></div>
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-3 w-1/2"
                            ></div>
                            <div
                                class="mt-auto animate-pulse bg-[#ffffff06] rounded h-3 w-1/3"
                            ></div>
                        </div>
                    {/each}
                </div>
            {/if}
        {:else}
            {@const resolvedTotal = Math.max(0, Math.floor(Number(resolved?.total ?? 0)))}
            {@const cardItems = (resolved?.items ?? []).map((c: any) => ({
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

            <!-- Stale cards stay visible while a refetch runs: the grid
                 container dims while `pending` and smoothly returns to full
                 opacity; the neutral inline tag next to the count says the
                 update is in flight. -->
            <div class="flex items-center gap-2.5 mb-6">
                <!-- Result count in the same "N x Found" style as squadrons,
                     lists, ships, and tournaments listings. -->
                <p class="text-secondary font-mono text-sm">
                    {resolvedTotal} {data.tab === "pilots" ? "Pilots" : "Upgrades"} Found
                </p>
                <PendingIndicator
                    active={pending}
                    mode="tag"
                    label="Updating…"
                />
            </div>

            <div
                class="transition-opacity duration-200 {pending
                    ? 'opacity-50'
                    : 'opacity-100'}"
            >
                {#if cardItems.length > 0}
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
                {:else}
                    <!-- Empty state: no cards matched the current filters -->
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center space-y-2"
                    >
                        <p
                            class="text-primary font-sans font-bold text-lg tracking-wide"
                        >
                            No {data.tab === "pilots" ? "pilots" : "upgrades"} found
                        </p>
                        <p class="text-secondary font-mono text-sm">
                            Try adjusting your filters, or retry the query.
                        </p>
                        <div class="pt-2">
                            <button
                                type="button"
                                onclick={retry}
                                class="px-4 py-1.5 text-xs font-mono border border-border-dark text-secondary rounded-md hover:bg-[#ffffff08] hover:text-primary active:bg-[#ffffff14] transition-colors"
                            >
                                Try again
                            </button>
                        </div>
                    </div>
                {/if}

                <!-- Pagination -->
                {#if resolvedTotal > size}
                    <div
                        class="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-border-dark"
                    >
                        <button
                            class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                            onclick={prevPage}
                            disabled={page <= 1}>← Prev</button
                        >
                        <span class="text-xs font-mono text-secondary">Page {page}</span
                        >
                        <button
                            class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                            onclick={nextPage}
                            disabled={page * size >= resolvedTotal}>Next →</button
                        >
                    </div>
                {/if}
            </div>
        {/if}
    </main>
</div>
