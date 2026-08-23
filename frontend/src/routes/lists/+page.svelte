<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import ListRowCard from "$lib/components/ListRowCard.svelte";
    import PendingIndicator from "$lib/components/PendingIndicator.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import {
        ALL_FACTIONS,
        getFactionLabel,
    } from "$lib/data/factions";
    import { invalidateAll } from "$app/navigation";
    import { page as currentPage } from "$app/state";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import Toggle from "$lib/components/Toggle.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";

    let { data } = $props();

    let filterOpen = $state(false);
    let page = $state(1);
    let factionOpen = $state(false);
    let minGames = $state(3);

    const size = 20;

    // The loader streams list rows in via `itemsPromise` (non-blocking
    // navigation). `resolved` keeps the LAST good payload so filter/sort/
    // page changes never blank the list: stale rows stay visible under a
    // thin "Updating…" bar while the next query runs; only the first load
    // shows the skeleton.
    let resolved = $state<any>(null);
    let pending = $state(true);
    let failed = $state(false);
    let lastPromise: any = null;
    let generation = 0;
    let total = $derived(resolved?.total ?? 0);

    $effect(() => {
        const p = data.itemsPromise;
        if (p === lastPromise) return;
        lastPromise = p;
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

    // Sync route-local state FROM the URL so direct navigation (e.g. ?page=2)
    // works. Filter store fields (sortBy, sortDirection, selectedFactions)
    // are hydrated by the layout via filters.applyFromSearchParams.
    $effect(() => {
        const urlPage = Number(currentPage.url.searchParams.get('page') ?? '0');
        page = urlPage + 1; // URL is 0-indexed, state is 1-indexed
        const urlMinGames = currentPage.url.searchParams.get('min_games');
        if (urlMinGames) minGames = Number(urlMinGames);
    });

    // Re-fetch when local filters change
    $effect(() => {
        // Ensure data is active
        xwingData.setSource(filters.dataSource as any);

        const params = filters.toSearchParams('lists');
        params.set('page', String(page - 1));
        params.set('size', String(size));
        params.set('min_games', String(minGames));
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

    // Default sort metric for the lists listing. The layout hydrates
    // `filters.sortBy` from the URL on first client mount, so we only seed a
    // default when the URL didn't supply one.
    $effect(() => {
        if (!filters.sortBy) {
            filters.sortBy = "Games";
        }
    });
</script>

{#snippet filterBody()}
    <div class="space-y-3">
        <div class="flex items-center gap-2">
            <span class="text-xs font-bold tracking-widest text-primary font-mono">
                LIST FILTERS
            </span>
        </div>

        <!-- Sort By was moved to the main content section header
             (rendered by SortBy) to give the list a single canonical
             sort control. The old sidebar SortSelector was removed. -->

        <!-- Min Games -->
        <div class="space-y-1">
            <span
                class="text-xs font-mono font-bold tracking-wider text-secondary"
                >Min Games</span
            >
            <input
                type="number"
                min="1"
                class="w-full bg-black border border-border-dark rounded-md px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                bind:value={minGames}
            />
        </div>

        <!-- Faction Checkboxes -->
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
                <div class="pb-3 space-y-1 max-h-[200px] overflow-y-auto pl-2">
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

        <ShipChassisFilter selectedFactions={filters.selectedFactions} />
    </div>
{/snippet}

<svelte:head>
    <title>Lists | M3taCron</title>
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
            List Browser
        </h1>

        {#if !resolved}
            {#if failed}
                <div class="mb-6">
                    <ErrorPanel
                        title="Failed to load lists"
                        onRetry={retry}
                    />
                </div>
            {:else}
                <p class="text-secondary font-mono text-sm mb-6">Loading…</p>

                <!-- Loading Skeleton (matches ListRowCard shape) -->
                <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
                    {#each Array(4) as _}
                        <div
                            class="bg-terminal-panel border border-border-dark border-l-[3px] rounded-lg p-3 md:p-4 space-y-3"
                        >
                            <div class="flex items-center justify-between gap-2">
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-4 w-2/5"
                                ></div>
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-4 w-10"
                                ></div>
                            </div>
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-3 w-3/5"
                            ></div>
                            <div class="flex gap-2">
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-12 w-full"
                                ></div>
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-12 w-full"
                                ></div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        {:else}
            {@const resolvedTotal = Number(resolved?.total ?? 0)}
            {@const listItems = resolved?.items ?? []}

            <!-- Stale rows stay visible while a refetch runs: the list
                 container dims while `pending` and smoothly returns to full
                 opacity; the neutral inline tag next to the count says the
                 update is in flight. -->
            <div
                class="flex items-center justify-between flex-wrap gap-3 mb-6"
            >
                <div class="flex items-center gap-2.5">
                    <p class="text-secondary font-mono text-sm">
                        {resolvedTotal} Lists Found
                    </p>
                    <PendingIndicator
                        active={pending}
                        mode="tag"
                        label="Updating…"
                    />
                </div>

                    <SortBy
                        value={filters.sortBy || "Games"}
                        direction={filters.sortDirection}
                        options={[
                            { value: "Games", label: "Games" },
                            { value: "Win Rate", label: "Win Rate" },
                            { value: "Entries", label: "Entries" },
                            { value: "Points Cost", label: "Points" },
                        ]}
                        onChange={(v, d) => {
                            filters.sortBy = v;
                            filters.sortDirection = d;
                        }}
                    />
                </div>

                <!-- Stale rows stay fully visible and clickable, dimmed
                     while the refetch is in flight. -->
                <div
                    class="transition-opacity duration-200 {pending
                        ? 'opacity-50'
                        : 'opacity-100'}"
                >
                <!-- List Cards -->
                {#if listItems.length > 0}
                    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
                        {#each listItems as list}
                            <ListRowCard {list} />
                        {/each}
                    </div>
                {:else}
                    <!-- Empty state: no lists matched the current filters -->
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center space-y-2"
                    >
                        <p
                            class="text-primary font-sans font-bold text-lg tracking-wide"
                        >
                            No lists found
                        </p>
                        <p class="text-secondary font-mono text-sm">
                            Try adjusting your filters or lowering the minimum games
                            threshold.
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
                        disabled={page <= 1}
                    >
                        ← Prev
                    </button>
                    <span class="text-xs font-mono text-secondary">Page {page}</span
                    >
                    <button
                        class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        onclick={nextPage}
                        disabled={page * size >= resolvedTotal}
                    >
                        Next →
                    </button>
                    </div>
                {/if}
            </div>
        {/if}
    </main>
</div>
