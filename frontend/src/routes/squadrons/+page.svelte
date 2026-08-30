<script lang="ts">
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import SquadronRowCard from "$lib/components/SquadronRowCard.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import PendingIndicator from "$lib/components/PendingIndicator.svelte";
    import ContentLoader from "$lib/components/ContentLoader.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import LocalFilterBar from "$lib/components/LocalFilterBar.svelte";
    import FactionFilter from "$lib/components/FactionFilter.svelte";
    import StatRangeFilter from "$lib/components/StatRangeFilter.svelte";
    import { invalidateAll } from "$app/navigation";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import { filters } from "$lib/stores/filters.svelte";

    let { data } = $props();

    let filterOpen = $state(false);
    let page = $state(1);

    const size = 20;
    let _localRestored = false;
    $effect(() => {
        if (_localRestored) return;
        const _sp = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();
        filters.restoreLocalFilters('squadrons', _sp);
        _localRestored = true;
    });

    // The loader streams squadron rows in via `itemsPromise` (non-blocking
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

    if (!filters.sortBy) { filters.sortBy = "Games"; }
    function isGlobalChip(k:string){ return k.startsWith("format:")||k.startsWith("continent:")||k.startsWith("country:")||k.startsWith("city:")||k.startsWith("source:")||k==="dateStart"||k==="dateEnd"; }
    let squadLocalChips = $derived(filters.activeChips.filter(c=>!isGlobalChip(c.key)));
    let datasetActive = $derived(filters.activeChips.filter(c=>isGlobalChip(c.key)).length);
    let squadLocalCount = $derived(squadLocalChips.length);
    function clearSquadFilters(){ for(const ch of [...squadLocalChips]) filters.removeChip(ch.key); }

    // Re-fetch when filters change (URL synchronization)
    $effect(() => {
        const params = filters.toSearchParams('squadrons');
        params.set('page', String(page - 1));
        params.set('size', String(size));
        scheduleSync(0, params);
        // Persist local filters per route (survives navigation, not shared across routes)
        queueMicrotask(() => filters.saveLocalFilters('squadrons'));
    });

    function prevPage() {
        if (page > 1) page--;
    }
    function nextPage() {
        if (page * size < total) page++;
    }

</script>

<svelte:head>
    <title>Squadrons | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <MobileFilterTrigger activeCount={datasetActive} label="Dataset filters" onClick={() => (filterOpen = true)} />
    <MobileFilterDrawer open={filterOpen} onClose={() => (filterOpen = false)} title="Dataset filters" activeCount={datasetActive} dataFilterTitle="Dataset filters" />

    <main class="flex-1 p-6 md:p-8 pb-20 lg:pb-8">
        <div class="flex flex-wrap items-baseline justify-between gap-3 mb-4">
            <h1 class="text-3xl font-sans font-bold text-primary leading-none shrink-0">Squadrons</h1>
            <div class="flex items-center gap-2 shrink-0 self-center">
                {#if resolved}<span class="hidden lg:inline text-xs font-mono text-secondary">{total} Squadrons Found</span><span class="hidden lg:inline w-px h-4 bg-white/10 shrink-0" aria-hidden="true"></span>
                {#if pending}<span class="hidden lg:inline"><PendingIndicator active mode="tag" label="Updating…" /></span>{/if}{/if}
                <span class="hidden sm:inline text-xs font-mono text-secondary uppercase tracking-wider">Sort by</span>
                <select class="bg-terminal-panel border border-border-dark rounded-md text-xs font-mono text-primary px-2 py-1.5 focus:outline-none" value={filters.sortBy || "Games"} onchange={(e)=>{filters.sortBy=(e.target as HTMLSelectElement).value;}} aria-label="Sort by"><option value="Games">Games</option><option value="Lists">Lists</option><option value="Entries">Entries</option><option value="Win Rate">Win Rate</option></select>
                <button type="button" onclick={()=>{filters.sortDirection=filters.sortDirection==="asc"?"desc":"asc";}} class="inline-flex items-center justify-center w-7 h-7 bg-terminal-panel border border-border-dark rounded-md text-secondary hover:text-primary hover:bg-[#ffffff05] active:bg-[#ffffff14] transition-colors shrink-0" aria-label={filters.sortDirection==="asc"?"Sort ascending":"Sort descending"}>{#if filters.sortDirection==="asc"}<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>{:else}<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>{/if}</button>
            </div>
        </div>
        <div class="mb-6"><LocalFilterBar id="squadrons-local" label="Squadron filters" activeCount={squadLocalCount} chips={squadLocalChips} onRemoveChip={(k)=>filters.removeChip(k)} onClear={clearSquadFilters}><div class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-4 items-start auto-rows-min"><FactionFilter /><StatRangeFilter label="Stat ranges" /><ShipChassisFilter selectedFactions={filters.selectedFactions} /></div></LocalFilterBar></div>

        {#if !resolved}
            {#if failed}
                <div class="mb-6">
                    <ErrorPanel
                        title="Failed to load squadrons"
                        onRetry={retry}
                    />
                </div>
            {:else}
                <ContentLoader label="Loading Squadrons" />

                <!-- Loading Skeleton (matches SquadronRowCard shape) -->
                <div class="space-y-3">
                    {#each Array(5) as _}
                        <div
                            class="bg-terminal-panel border border-border-dark border-l-[3px] rounded-lg p-4 space-y-3"
                        >
                            <div class="flex items-center justify-between gap-2">
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-4 w-1/3"
                                ></div>
                                <div class="flex gap-1.5">
                                    <div
                                        class="animate-pulse bg-[#ffffff06] rounded h-4 w-10"
                                    ></div>
                                    <div
                                        class="animate-pulse bg-[#ffffff06] rounded h-4 w-10"
                                    ></div>
                                    <div
                                        class="animate-pulse bg-[#ffffff06] rounded h-4 w-10"
                                    ></div>
                                </div>
                            </div>
                            <div class="flex gap-2 flex-wrap">
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-9 w-24"
                                ></div>
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-9 w-28"
                                ></div>
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-9 w-20"
                                ></div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        {:else}
            {@const resolvedTotal = Number(resolved?.total ?? 0)}
            {@const squadronItems = resolved?.items ?? []}
            <!--
                Filter: exclude only multi-faction squadrons (ships from
                different factions illegally combined in one list).
                - Include all single-faction squadrons (the vast majority).
                - Include squadrons with no pilots array (legacy data we
                  cannot inspect for multi-faction content).
                - Exclude multi-faction squadrons (more than one unique
                  faction across the squadron's pilots).
            -->
            {@const visibleSquadrons = squadronItems.filter((s: any) => {
                if (!Array.isArray(s.pilots) || s.pilots.length === 0) return true;

                const factions = new Set<string>();
                for (const p of s.pilots) {
                    if (p.faction_xws) factions.add(p.faction_xws);
                }

                if (factions.size > 1) return false;

                return true;
            })}

            <div class="flex items-center gap-2.5 mt-1.5 mb-2 lg:hidden"><p class="text-secondary font-mono text-sm">{total} Squadrons Found</p><PendingIndicator active={pending} mode="tag" label="Updating…" /></div>

            <div
                class="transition-opacity duration-200 {pending
                    ? 'opacity-50'
                    : 'opacity-100'}"
            >

                {#if visibleSquadrons.length > 0}
                    <!-- Squadron Cards -->
                    <div class="space-y-3">
                        {#each visibleSquadrons as list}
                            <SquadronRowCard {list} />
                        {/each}
                    </div>
                {:else}
                    <!-- Empty state: no squadrons matched the current filters -->
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center space-y-2"
                    >
                        <p
                            class="text-primary font-sans font-bold text-lg tracking-wide"
                        >
                            No squadrons found
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

                <div class="flex items-center justify-center gap-2 mt-6"><button class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed" onclick={prevPage} disabled={page <= 1}>← Prev</button><span class="text-xs font-mono text-secondary">Showing {resolvedTotal===0?0:(page-1)*size+1}–{Math.min(page*size,resolvedTotal)} of {resolvedTotal} · Page {page}/{Math.max(1,Math.ceil(resolvedTotal/size))}</span><button class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed" onclick={nextPage} disabled={page*size>=resolvedTotal}>Next →</button></div>
            </div>
        {/if}
    </main>
</div>
