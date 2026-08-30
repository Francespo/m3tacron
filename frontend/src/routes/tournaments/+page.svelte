<script lang="ts">
    import PendingIndicator from "$lib/components/PendingIndicator.svelte";
    import ContentLoader from "$lib/components/ContentLoader.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import LocalFilterBar from "$lib/components/LocalFilterBar.svelte";
    import TournamentPageFilters from "$lib/components/TournamentPageFilters.svelte";
    import { invalidateAll } from "$app/navigation";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import { getFormatLabel, getFormatColor } from "$lib/data/formats";

    let { data } = $props();

    let page = $state(1);
    const size = 20;
    let _localRestored = false;
    $effect(() => {
        if (_localRestored) return;
        const _sp = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();
        filters.restoreLocalFilters('tournaments', _sp);
        _localRestored = true;
    });

    // The loader streams the tournament rows in via `itemsPromise`
    // (non-blocking navigation). `resolved` keeps the LAST good payload so
    // filter/sort/page changes never blank the list: the stale rows stay
    // visible under a thin "Updating…" bar while the next query runs, and
    // only a first load (no data yet) shows the skeleton.
    let resolved = $state<{
        items: any[];
        total: number;
        page: number;
        size: number;
        search: string;
    } | null>(null);
    let pending = $state(true);
    let failed = $state(false);
    let lastPromise: any = null;
    let generation = 0;
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
    let total = $derived(resolved?.total ?? 0);

    function retry() {
        invalidateAll();
    }

    // Push the store + route-local overlay (page, size) to the URL.
    // Filter store fields (sortBy, sortDirection, search, etc.) are written
    // centrally via `filters.toSearchParams`; route-local fields are overlaid
    // on top. URL hydration on direct nav is handled by the layout via
    // `filters.applyFromSearchParams`.
    $effect(() => {
        const params = filters.toSearchParams('tournaments');
        params.set('page', String(page - 1));
        params.set('size', String(size));
        scheduleSync(0, params);
        // Persist local filters per route (survives navigation, not shared across routes)
        queueMicrotask(() => filters.saveLocalFilters('tournaments'));
    });

    function prevPage() {
        if (page > 1) page--;
    }
    function nextPage() {
        if (page * size < total) page++;
    }

    // Default sort metric for the tournaments listing. The layout hydrates
    // `filters.sortBy` from the URL on first client mount, so we only seed a
    // default when the URL didn't supply one. Keeps the URL stable (no
    // write-loop) while ensuring the SortBy in the main content header
    // always has a real value matching one of its options.
    $effect(() => {
        if (!filters.sortBy) {
            filters.sortBy = "Date";
        }
    });
    function isGlobalChip(k:string){ return k.startsWith("format:")||k.startsWith("continent:")||k.startsWith("country:")||k.startsWith("city:")||k.startsWith("source:")||k==="dateStart"||k==="dateEnd"; }
    let tournamentLocalChips = $derived(filters.activeChips.filter(c=>!isGlobalChip(c.key)));
    let tournamentLocalCount = $derived(tournamentLocalChips.length);
    let datasetActive = $derived(filters.activeChips.filter(c=>isGlobalChip(c.key)).length);
    function clearTournamentFilters(){ for (const ch of [...tournamentLocalChips]) filters.removeChip(ch.key); }
</script>

<!-- Sort By was moved to the main content section header (rendered by
     SortBy) to give the list a single canonical sort control. The old
     sidebar SortSelector and the entire filterBody snippet were
     removed; the FilterPanel + MobileFilterDrawer no longer receive
     children on this page. -->

<svelte:head>
    <title>Tournaments | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <!-- Filters now live in the right-side drawer (FAB) on all breakpoints.
         No fixed left filter panel — the FAB + drawer replace it on desktop
         too, matching the mobile pattern. -->
    <!-- Tournaments: no FAB — filters are inline in the collapsible bar below (standalone from dataset) -->

    <!-- Main Content (3rd column) -->
    <main class="flex-1 min-w-0 p-6 md:p-8 pb-20 lg:pb-8">
        <!-- Page header — standardized: title + count | Sort by (outside filters, always visible even collapsed) -->
        <div class="flex flex-wrap items-baseline justify-between gap-3 mb-4">
            <h1 class="text-3xl font-sans font-bold text-primary leading-none shrink-0">Tournaments</h1>
            <div class="flex items-center gap-2 shrink-0 self-center">
                {#if resolved}
                    <span class="hidden lg:inline text-xs font-mono text-secondary">{resolved.total ?? 0} Tournaments Found</span>
                    <span class="hidden lg:inline w-px h-4 bg-white/10 shrink-0" aria-hidden="true"></span>
                {#if pending}<span class="hidden lg:inline"><PendingIndicator active mode="tag" label="Updating…" /></span>{/if}
                {/if}
                <span class="hidden sm:inline text-xs font-mono text-secondary uppercase tracking-wider">Sort by</span>
                <select class="bg-terminal-panel border border-border-dark rounded-md text-xs font-mono text-primary px-2 py-1.5 focus:outline-none" value={filters.sortBy || "Date"} onchange={(e) => { filters.sortBy = (e.target as HTMLSelectElement).value; }} aria-label="Sort by">
                    <option value="Date">Date</option><option value="Players">Players</option><option value="Name">Name</option>
                </select>
                <button type="button" onclick={() => { filters.sortDirection = filters.sortDirection === "asc" ? "desc" : "asc"; }} class="inline-flex items-center justify-center w-7 h-7 bg-terminal-panel border border-border-dark rounded-md text-secondary hover:text-primary hover:bg-[#ffffff05] active:bg-[#ffffff14] transition-colors shrink-0" aria-label={filters.sortDirection === "asc" ? "Sort ascending" : "Sort descending"}>
                    {#if filters.sortDirection === "asc"}<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>{:else}<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>{/if}
                </button>
            </div>
        </div>
        <!-- Tournaments have no per-section game filters: the only page filters ARE the dataset filters (dates, locations, formats, sources, search). Expose them as an inline collapsible LocalFilterBar like Card filters, not just a FAB. Dataset is still the global concept; this bar just makes tournament dataset filters discoverable inline. -->
        <div class="mb-6">
            <LocalFilterBar id="tournaments-local" label="Tournament filters" activeCount={tournamentLocalCount} chips={tournamentLocalChips} onRemoveChip={(k) => filters.removeChip(k)} onClear={clearTournamentFilters}>
                <TournamentPageFilters />
            </LocalFilterBar>
        </div>
        {#if !resolved}
            {#if failed}
                <div class="mb-6">
                    <ErrorPanel
                        title="Failed to load tournaments"
                        onRetry={retry}
                    />
                </div>
            {:else}
                <ContentLoader label="Loading Tournaments" />

                <!-- Loading Skeleton (matches tournament row shape:
                     format badge / title+meta / player count) -->
                <div class="space-y-2">
                    {#each Array(6) as _}
                        <div
                            class="flex items-center gap-3 sm:gap-4 bg-terminal-panel border border-border-dark rounded-lg px-4 py-3 min-h-[44px]"
                        >
                            <div
                                class="hidden sm:flex w-[60px] shrink-0 justify-center"
                            >
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded-md h-4 w-12"
                                ></div>
                            </div>
                            <div class="flex-1 min-w-0 space-y-2">
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-3.5 w-3/5 max-w-[280px]"
                                ></div>
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-3 w-2/5 max-w-[200px]"
                                ></div>
                            </div>
                            <div
                                class="hidden sm:flex w-16 shrink-0 flex-col items-center gap-1"
                            >
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-4 w-6"
                                ></div>
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-2 w-8"
                                ></div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        {:else}
            {@const resolvedTotal = resolved?.total ?? 0}
            {@const items = resolved?.items ?? []}

            <div class="flex items-center gap-2.5 mt-1.5 mb-2 lg:hidden">
                <p class="text-secondary font-mono text-sm">{resolvedTotal} Tournaments Found</p>
                <PendingIndicator active={pending} mode="tag" label="Updating…" />
            </div>
            

            <div
                class="transition-opacity duration-200 {pending
                    ? 'opacity-50'
                    : 'opacity-100'}"
            >

                {#if items.length > 0}
                    <!-- Tournament Rows -->
                    <div class="space-y-2">
                        {#each items as t}
                        {@const formatLabel = getFormatLabel(t.format)}
                        {@const formatColor = getFormatColor(t.format)}
                        <a
                            href="/tournaments/{t.id}"
                            class="flex items-center gap-3 sm:gap-4 min-w-0 bg-terminal-panel border border-border-dark rounded-lg px-4 py-3 min-h-[44px] hover:border-secondary/40 hover:bg-[#ffffff04] active:bg-[#ffffff0a] transition-colors group"
                        >
                    <!-- Format Badge: left column on sm+, chip on mobile -->
                    <span
                        class="hidden sm:flex items-center justify-center min-w-[60px] self-stretch text-center"
                    >
                        <span
                            class="text-[10px] font-mono font-bold tracking-wider uppercase"
                            style="color: {formatColor};"
                        >
                            {formatLabel}
                        </span>
                    </span>

                    <!-- Info column -->
                    <div class="flex-1 min-w-0">
                        <!-- Top row: title + (mobile) format chip + player count -->
                        <div class="flex items-center gap-2 mb-1 sm:mb-1.5">
                            <h3
                                class="text-sm font-sans font-bold text-primary truncate group-hover:text-white flex-1 min-w-0"
                                title={t.name}
                            >
                                {t.name}
                            </h3>

                            <!-- Format chip: mobile only -->
                            <span
                                class="sm:hidden shrink-0 inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-mono font-bold tracking-wider uppercase border"
                                style="color: {formatColor}; border-color: {formatColor}40; background-color: {formatColor}14;"
                            >
                                {formatLabel}
                            </span>

                            <!-- Player Count: mobile (compact) -->
                            <span
                                class="sm:hidden shrink-0 px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                            >
                                PLY {t.players ?? "?"}
                            </span>
                        </div>

                        <!-- Bottom row: date • location -->
                        <div class="flex items-center gap-2 text-xs font-mono text-secondary min-w-0 flex-wrap">
                            <span
                                class="shrink-0 px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary truncate max-w-full"
                                title={t.date}
                            >
                                {t.date}
                            </span>
                            <span
                                class="shrink-0 px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-secondary truncate max-w-full"
                                title={t.location || "Unknown Location"}
                            >
                                {t.location || "Unknown Location"}
                            </span>
                        </div>
                    </div>

                    <!-- Player Count: sm+ column -->
                    <div
                        class="hidden sm:flex w-16 shrink-0 flex-col items-center justify-center text-center"
                    >
                        <span class="text-2xl font-sans font-bold text-primary leading-none"
                            >{t.players ?? "?"}</span
                        >
                        <span class="text-[10px] font-mono text-secondary block mt-0.5">PLY</span>
                    </div>
                </a>
            {/each}
            </div>
            {:else}
                <!-- Empty state: also covers a failed fetch, which the
                     loader resolves as an empty payload. -->
                <div
                    class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center space-y-2"
                >
                    <p
                        class="text-primary font-sans font-bold text-lg tracking-wide"
                    >
                        No tournaments found
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

            <div class="flex items-center justify-center gap-2 mt-6">
                <button class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed" onclick={prevPage} disabled={page <= 1}>← Prev</button>
                <span class="text-xs font-mono text-secondary">Showing {resolvedTotal === 0 ? 0 : (page - 1) * size + 1}–{Math.min(page * size, resolvedTotal)} of {resolvedTotal} · Page {page}/{Math.max(1, Math.ceil(resolvedTotal / size))}</span>
                <button class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed" onclick={nextPage} disabled={page * size >= resolvedTotal}>Next →</button>
            </div>
            </div>
        {/if}
    </main>
</div>


