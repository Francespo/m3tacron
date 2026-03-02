<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import ActiveChips from "$lib/components/ActiveChips.svelte";
    import {
        getFactionColor,
        getFactionChar,
        getWinRateColor,
    } from "$lib/data/factions";
    import { goto } from "$app/navigation";
    import { filters } from "$lib/stores/filters.svelte";

    let { data } = $props();

    let items = $derived(data.items ?? []);
    let total = $derived(data.total ?? 0);
    let page = $state(1);
    const size = 50;

    // Trigger URL updates on filter changes
    $effect(() => {
        const params = new URLSearchParams();
        params.set("page", String(page - 1));
        params.set("size", String(size));
        params.set("data_source", filters.dataSource);
        for (const format of filters.selectedFormats)
            params.append("formats", format);

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
    <title>Ships | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <FilterPanel />

    <main class="flex-1 p-6 md:p-8">
        <ActiveChips />

        <h1 class="text-2xl font-sans font-bold text-primary mb-1">Ships</h1>
        <p class="text-secondary font-mono text-sm mb-6">{total} Ships Found</p>

        <!-- Ships Heatmap Grid -->
        <div
            class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3"
        >
            {#each items as ship}
                {@const wr = ship.win_rate ?? 0}
                {@const wrColor = getWinRateColor(wr)}
                {@const games = ship.games ?? 0}
                {@const lists = ship.lists ?? ship.count ?? 0}
                {@const factionKey = ship.faction ?? "unknown"}
                {@const factionColor = getFactionColor(factionKey)}
                <!-- Glow intensity proportional to games (popularity) -->
                {@const glowOpacity = Math.min(0.3, (games / 2000) * 0.3)}

                <div
                    class="relative bg-terminal-panel border border-border-dark rounded-md p-4 flex flex-col items-center gap-2 hover:border-secondary/50 transition-all group"
                    style="box-shadow: 0 0 20px {factionColor}{Math.round(
                        glowOpacity * 255,
                    )
                        .toString(16)
                        .padStart(2, '0')}; border-color: {factionColor}30;"
                >
                    <!-- Faction icon (small, top-right) -->
                    <span
                        class="absolute top-2 right-2 font-xwing text-sm opacity-50"
                        style="color: {factionColor};"
                    >
                        {getFactionChar(factionKey)}
                    </span>

                    <!-- Ship Icon (from X-Wing ship font via CSS pseudo-element) -->
                    <i
                        class="xwing-miniatures-ship xwing-miniatures-ship-{ship.ship_xws ||
                            ''} text-5xl group-hover:scale-110 transition-transform"
                        style="color: {factionColor};"
                    ></i>

                    <!-- Ship Name -->
                    <span
                        class="text-xs font-sans font-bold text-primary text-center leading-tight"
                    >
                        {ship.ship_name || "Unknown Ship"}
                    </span>

                    <!-- Stats Grid (2x2) -->
                    <div class="grid grid-cols-2 gap-1 w-full">
                        <div
                            class="text-center bg-[#ffffff05] rounded px-1 py-0.5"
                        >
                            <span
                                class="text-xs font-mono font-bold"
                                style="color: {wrColor};">{wr.toFixed(1)}%</span
                            >
                            <span
                                class="text-[9px] font-mono text-secondary block"
                                >WR</span
                            >
                        </div>
                        <div
                            class="text-center bg-[#ffffff05] rounded px-1 py-0.5"
                        >
                            <span class="text-xs font-mono text-primary"
                                >{games}</span
                            >
                            <span
                                class="text-[9px] font-mono text-secondary block"
                                >Games</span
                            >
                        </div>
                        <div
                            class="text-center bg-[#ffffff05] rounded px-1 py-0.5"
                        >
                            <span class="text-xs font-mono text-primary"
                                >{lists}</span
                            >
                            <span
                                class="text-[9px] font-mono text-secondary block"
                                >Lists</span
                            >
                        </div>
                        <div
                            class="text-center bg-[#ffffff05] rounded px-1 py-0.5"
                        >
                            <span class="text-xs font-mono text-primary"
                                >{ship.pilots_count ?? "?"}</span
                            >
                            <span
                                class="text-[9px] font-mono text-secondary block"
                                >Pilots</span
                            >
                        </div>
                    </div>
                </div>
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
