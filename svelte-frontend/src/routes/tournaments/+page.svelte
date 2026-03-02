<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import ActiveChips from "$lib/components/ActiveChips.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { goto } from "$app/navigation";

    let { data } = $props();

    let page = $state(1);
    const size = 20;

    // Derive filtered items from data + global filters
    let items = $derived(data.items ?? []);
    let total = $derived(data.total ?? 0);

    $effect(() => {
        const params = new URLSearchParams();
        params.set("page", String(page - 1));
        params.set("size", String(size));
        params.set("data_source", filters.dataSource);
        for (const format of filters.selectedFormats)
            params.append("formats", format);
        // Date filters
        if (filters.dateStart) params.set("date_start", filters.dateStart);
        if (filters.dateEnd) params.set("date_end", filters.dateEnd);
        // Location filters
        for (const c of filters.selectedContinents)
            params.append("continent", c);
        for (const c of filters.selectedCountries) params.append("country", c);
        for (const c of filters.selectedCities) params.append("city", c);

        goto(`?${params.toString()}`, {
            keepFocus: true,
            noScroll: true,
            replaceState: true,
        });
    });

    function prevPage() {
        if (page > 1) page--;
    }
    function nextPage() {
        if (page * size < total) page++;
    }
</script>

<svelte:head>
    <title>Tournaments | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <!-- Filter Panel (2nd column) -->
    <FilterPanel />

    <!-- Main Content (3rd column) -->
    <main class="flex-1 p-6 md:p-8">
        <ActiveChips />

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
                        class="flex flex-col items-center justify-center min-w-[50px] text-center"
                    >
                        <span
                            class="text-[10px] font-mono font-bold text-primary tracking-wider"
                        >
                            {t.badge_l1 || "STD"}
                        </span>
                        <span class="text-[10px] font-mono text-secondary">
                            {t.badge_l2 || ""}
                        </span>
                    </div>

                    <!-- Info -->
                    <div class="flex-1 min-w-0">
                        <h3
                            class="text-sm font-sans font-bold text-primary truncate group-hover:text-white"
                        >
                            {t.name}
                        </h3>
                        <p class="text-xs font-mono text-secondary truncate">
                            <span class="text-[#00e5ff]"
                                >{t.platform_label || "LONGSHANKS"}</span
                            >
                            <span class="mx-1">•</span>
                            {t.date}
                            <span class="mx-1">•</span>
                            {t.location || "Unknown"}
                        </p>
                    </div>

                    <!-- Player Count -->
                    <div class="text-right shrink-0">
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
