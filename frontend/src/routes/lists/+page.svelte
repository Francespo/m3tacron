<script lang="ts">
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import ListRowCard from "$lib/components/ListRowCard.svelte";
    import LocalFilterBar from "$lib/components/LocalFilterBar.svelte";
    import FactionFilter from "$lib/components/FactionFilter.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import PilotFilter from "$lib/components/PilotFilter.svelte";
    import StatRangeFilter from "$lib/components/StatRangeFilter.svelte";
    import PendingIndicator from "$lib/components/PendingIndicator.svelte";
    import ContentLoader from "$lib/components/ContentLoader.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import { invalidateAll } from "$app/navigation";
    import { page as currentPage } from "$app/state";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    
    let { data } = $props();

    let filterOpen = $state(false);
    let page = $state(1);
    let minGames = $state(3);

    const size = 20;
    let _localRestored = false;
    $effect(() => {
        if (_localRestored) return;
        const _sp = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();
        filters.restoreLocalFilters('lists', _sp);
        _localRestored = true;
    });

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
        // Persist local filters per route (survives navigation, not shared across routes)
        queueMicrotask(() => filters.saveLocalFilters('lists'));
    });

    function prevPage() {
        if (page > 1) page--;
    }
    function nextPage() {
        if (page * size < total) page++;
    }

    // Default sort metric for the lists listing. The layout hydrates
    // `filters.sortBy` from the URL on first client mount, so we only seed a
    // default when the URL didn't supply one.
    $effect(() => { if (!filters.sortBy) filters.sortBy = "Games"; });
    function isGlobalChip(k:string){ return k.startsWith("format:")||k.startsWith("continent:")||k.startsWith("country:")||k.startsWith("city:")||k.startsWith("source:")||k==="dateStart"||k==="dateEnd"; }
    let listLocalChips = $derived(filters.activeChips.filter(c=>!isGlobalChip(c.key)));
    let datasetActive = $derived(filters.activeChips.filter(c=>isGlobalChip(c.key)).length);
    let listLocalCount = $derived(listLocalChips.length);
    function clearListFilters(){ for(const ch of [...listLocalChips]) filters.removeChip(ch.key); }
</script>

<svelte:head>
    <title>Lists | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <MobileFilterTrigger activeCount={datasetActive} label="Dataset" onClick={() => (filterOpen = true)} />
    <MobileFilterDrawer open={filterOpen} onClose={() => (filterOpen = false)} title="Dataset filters" activeCount={datasetActive} dataFilterTitle="Dataset filters" />

    <main class="flex-1 p-6 md:p-8 pb-20 lg:pb-8">
        <div class="flex flex-wrap items-baseline justify-between gap-3 mb-4">
            <h1 class="text-3xl font-sans font-bold text-primary leading-none shrink-0">Lists</h1>
            <div class="flex items-center gap-2 shrink-0 self-center">
                {#if resolved}<span class="hidden lg:inline text-xs font-mono text-secondary">{(resolved?.total ?? 0)} Lists Found</span><span class="hidden lg:inline w-px h-4 bg-white/10 shrink-0" aria-hidden="true"></span>
                {#if pending}<span class="hidden lg:inline"><PendingIndicator active mode="tag" label="Updating…" /></span>{/if}{/if}
                <span class="hidden sm:inline text-xs font-mono text-secondary uppercase tracking-wider">Sort by</span>
                <select class="bg-terminal-panel border border-border-dark rounded-md text-xs font-mono text-primary px-2 py-1.5 focus:outline-none" value={filters.sortBy || "Games"} onchange={(e)=>{filters.sortBy=(e.target as HTMLSelectElement).value;}} aria-label="Sort by"><option value="Games">Games</option><option value="Win Rate">Win Rate</option><option value="Entries">Entries</option><option value="Points Cost">Points</option></select>
                <button type="button" onclick={()=>{filters.sortDirection=filters.sortDirection==="asc"?"desc":"asc";}} class="inline-flex items-center justify-center w-7 h-7 bg-terminal-panel border border-border-dark rounded-md text-secondary hover:text-primary hover:bg-[#ffffff05] active:bg-[#ffffff14] transition-colors shrink-0" aria-label={filters.sortDirection==="asc"?"Sort ascending":"Sort descending"}>{#if filters.sortDirection==="asc"}<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>{:else}<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>{/if}</button>
            </div>
        </div>
        <div class="mb-6"><LocalFilterBar id="lists-local" label="List filters" activeCount={listLocalCount} chips={listLocalChips} onRemoveChip={(k)=>filters.removeChip(k)} onClear={clearListFilters}><div class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-4 items-start auto-rows-min"><FactionFilter /><StatRangeFilter label="Stat ranges" hideLists /><PilotFilter selectedFactions={filters.selectedFactions} /><ShipChassisFilter selectedFactions={filters.selectedFactions} /></div></LocalFilterBar></div>

        {#if !resolved}
            {#if failed}
                <div class="mb-6">
                    <ErrorPanel
                        title="Failed to load lists"
                        onRetry={retry}
                    />
                </div>
            {:else}
                <ContentLoader label="Loading Lists" />

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

            <div class="flex items-center gap-2.5 mt-1.5 mb-2 lg:hidden"><p class="text-secondary font-mono text-sm">{(resolved?.total ?? 0)} Lists Found</p><PendingIndicator active={pending} mode="tag" label="Updating…" /></div>

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

                                <div class="flex items-center justify-center gap-2 mt-6"><button class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed" onclick={prevPage} disabled={page <= 1}>← Prev</button><span class="text-xs font-mono text-secondary">Showing {resolvedTotal===0?0:(page-1)*size+1}–{Math.min(page*size,resolvedTotal)} of {resolvedTotal} · Page {page}/{Math.max(1,Math.ceil(resolvedTotal/size))}</span><button class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed" onclick={nextPage} disabled={page*size>=resolvedTotal}>Next →</button></div>
            </div>
        {/if}
    </main>
</div>