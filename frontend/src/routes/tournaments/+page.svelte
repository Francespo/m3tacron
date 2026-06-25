<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import SortSelector from "$lib/components/SortSelector.svelte";
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
</script>

{#snippet filterBody()}
    <SortSelector
        bind:sortBy={filters.sortBy}
        bind:sortDirection={filters.sortDirection}
        options={[
            { value: "Date", label: "Date" },
            { value: "Players", label: "Players" },
            { value: "Name", label: "Name" },
        ]}
    />
{/snippet}

<svelte:head>
    <title>Tournaments | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <!-- Filter Panel (2nd column) -->
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

    <!-- Main Content (3rd column) -->
    <main class="flex-1 p-6 md:p-8 pb-20 lg:pb-8">
        <h1 class="text-2xl font-sans font-bold text-primary mb-1">
            Tournaments
        </h1>
        <p class="text-secondary font-mono text-sm mb-6">
            {total} Tournaments Found
        </p>

        <!-- Tournament Rows -->
        <div class="space-y-2">
            {#each items as t}
                <a
                    href="/tournaments/{t.id}"
                    class="flex items-center gap-4 bg-terminal-panel border border-border-dark rounded-md px-4 py-3 hover:border-secondary/40 transition-colors group"
                >
                    <!-- Format Badge -->
                    <div
                        class="flex items-center justify-center min-w-[60px] self-stretch text-center"
                    >
                        <span
                            class="text-[10px] font-mono font-bold tracking-wider uppercase"
                            style="color: {getFormatColor(t.format)};"
                        >
                            {getFormatLabel(t.format)}
                        </span>
                    </div>

                    <!-- Info -->
                    <div class="flex-1 min-w-0">
                        <div class="mb-1.5">
                            <h3
                                class="text-sm font-sans font-bold text-primary truncate group-hover:text-white"
                                title={t.name}
                            >
                                {t.name}
                            </h3>
                        </div>
                        <div class="flex items-center text-xs font-mono text-secondary">
                            <span class="w-[88px] shrink-0" title={t.date}>
                                {t.date}
                            </span>
                            <span class="mx-2 text-secondary/60">•</span>
                            <span class="truncate" title={t.location || "Unknown Location"}>
                                {t.location || "Unknown Location"}
                            </span>
                        </div>
                    </div>

                    <!-- Player Count -->
                    <div class="w-12 shrink-0 flex flex-col items-center justify-center text-center">
                        <span class="text-2xl font-sans font-bold text-primary"
                            >{t.players ?? "?"}</span
                        >
                        <span class="text-[10px] font-mono text-secondary block"
                            >PLY</span
                        >
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
                    class="px-3 py-1 text-xs font-mono border border-border-dark rounded hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                    onclick={prevPage}
                    disabled={page <= 1}
                >
                    ← Prev
                </button>
                <span class="text-xs font-mono text-secondary">Page {page}</span
                >
                <button
                    class="px-3 py-1 text-xs font-mono border border-border-dark rounded hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                    onclick={nextPage}
                    disabled={page * size >= total}
                >
                    Next →
                </button>
            </div>
        {/if}
    </main>
</div>
