<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import { getFormatLabel, getFormatColor } from "$lib/data/formats";

    let { data } = $props();

    let filterOpen = $state(false);
    let page = $state(1);
    const size = 20;

    // Derive filtered items from data + global filters
    let items = $derived(data.items ?? []);
    let total = $derived(data.total ?? 0);

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
        <p class="text-secondary font-mono text-sm mb-6">
            {total} Tournaments Found
        </p>

        <!-- Tournament Rows -->
        <div class="space-y-2">
            {#each items as t}
                {@const formatLabel = getFormatLabel(t.format)}
                {@const formatColor = getFormatColor(t.format)}
                <a
                    href="/tournaments/{t.id}"
                    class="flex items-center gap-3 sm:gap-4 min-w-0 bg-terminal-panel border border-border-dark rounded-lg px-4 py-3 min-h-[44px] hover:border-secondary/40 transition-colors group"
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

        <!-- Pagination -->
        {#if total > size}
            <div
                class="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-border-dark"
            >
                <button
                    class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                    onclick={prevPage}
                    disabled={page <= 1}
                >
                    ← Prev
                </button>
                <span class="text-xs font-mono text-secondary">Page {page}</span
                >
                <button
                    class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                    onclick={nextPage}
                    disabled={page * size >= total}
                >
                    Next →
                </button>
            </div>
        {/if}
    </main>
</div>
