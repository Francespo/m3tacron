<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import PendingIndicator from "$lib/components/PendingIndicator.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import { invalidateAll } from "$app/navigation";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import { getFormatLabel, getFormatColor } from "$lib/data/formats";

    let { data } = $props();

    let filterOpen = $state(false);
    let page = $state(1);
    const size = 20;

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
    <!-- Filter Panel (2nd column). No children: the page's only filter
         (sort) lives in the main content section header so there is no
         sidebar content to render. -->
    <FilterPanel />

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
        {#snippet children()}
            <!-- No sidebar filters on this page; sort lives in the main content. -->
        {/snippet}
    </MobileFilterDrawer>

    <!-- Main Content (3rd column) -->
    <main class="flex-1 min-w-0 p-6 md:p-8 pb-20 lg:pb-8">
        <div class="flex items-start justify-between gap-3 mb-1 flex-wrap">
            <h1 class="text-3xl font-sans font-bold text-primary">
                Tournaments
            </h1>
            <SortBy
                value={filters.sortBy || "Date"}
                direction={filters.sortDirection}
                options={[
                    { value: "Date", label: "Date" },
                    { value: "Players", label: "Players" },
                    { value: "Name", label: "Name" },
                ]}
                onChange={(v, d) => {
                    filters.sortBy = v;
                    filters.sortDirection = d;
                }}
            />
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
                <p class="text-secondary font-mono text-sm mb-6">Loading…</p>

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

            <!-- Stale rows stay visible while a refetch runs: the rows
                 container dims while `pending` and smoothly returns to full
                 opacity; the neutral inline tag next to the count says the
                 update is in flight. -->
            <div class="flex items-center gap-2.5 mb-6">
                <p class="text-secondary font-mono text-sm">
                    {resolvedTotal} Tournaments Found
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
