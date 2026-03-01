<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import ActiveChips from "$lib/components/ActiveChips.svelte";
    import {
        getWinRateColor,
        ALL_FACTIONS,
        getFactionColor,
        getFactionChar,
        getFactionLabel,
    } from "$lib/data/factions";
    import { filters } from "$lib/stores/filters.svelte";

    let { data } = $props();

    let tab = $state<"pilots" | "upgrades">("pilots");
    let page = $state(1);
    let sortBy = $state("popularity");
    let textSearch = $state("");
    let selectedFactions = $state<string[]>([]);
    const size = 20;

    let items = $derived(data.items ?? []);
    let total = $derived(data.total ?? 0);
    let isXwa = $derived(filters.dataSource === "xwa");

    function prevPage() {
        if (page > 1) page--;
    }
    function nextPage() {
        if (page * size < total) page++;
    }

    function toggleFaction(f: string) {
        if (selectedFactions.includes(f)) {
            selectedFactions = selectedFactions.filter((x) => x !== f);
        } else {
            selectedFactions = [...selectedFactions, f];
        }
    }
</script>

{#snippet cardFilters()}
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
                class="flex-1 py-1 text-xs font-mono text-center bg-[#ffffff14] text-primary"
                >Basic</button
            >
            <button
                class="flex-1 py-1 text-xs font-mono text-center text-secondary hover:text-primary"
                >Advanced</button
            >
        </div>

        <!-- Sort By -->
        <div class="space-y-1">
            <span
                class="text-xs font-mono font-bold tracking-wider text-secondary"
                >Sort By</span
            >
            <select
                class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                bind:value={sortBy}
            >
                <option value="popularity">Popularity</option>
                <option value="win_rate">Win Rate</option>
                <option value="games">Games</option>
                <option value="name">Name</option>
            </select>
        </div>

        <!-- Text Search -->
        <div class="space-y-1">
            <span
                class="text-xs font-mono font-bold tracking-wider text-secondary"
                >Text Search</span
            >
            <input
                type="text"
                placeholder="Search card text"
                class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary placeholder:text-[#555] focus:border-primary focus:outline-none"
                bind:value={textSearch}
            />
        </div>

        <!-- Faction -->
        <div class="space-y-1">
            <span
                class="text-xs font-mono font-bold tracking-wider text-secondary"
                >Faction</span
            >
            <div class="space-y-1 max-h-[180px] overflow-y-auto">
                {#each ALL_FACTIONS as f}
                    <label
                        class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                    >
                        <input
                            type="checkbox"
                            class="rounded border-border-dark bg-black w-3 h-3"
                            checked={selectedFactions.includes(f)}
                            onchange={() => toggleFaction(f)}
                        />
                        <span
                            class="font-xwing text-sm"
                            style="color: {getFactionColor(f)};"
                            >{getFactionChar(f)}</span
                        >
                        <span class="font-mono">{getFactionLabel(f)}</span>
                    </label>
                {/each}
            </div>
        </div>

        <!-- Ship Chassis (placeholder) -->
        <div class="space-y-1">
            <span
                class="text-xs font-mono font-bold tracking-wider text-secondary"
                >Ship Chassis</span
            >
            <div class="text-xs text-secondary font-mono italic">
                Expand to filter by chassis
            </div>
        </div>
    </div>
{/snippet}

<svelte:head>
    <title>Cards | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <FilterPanel extra={cardFilters} />

    <main class="flex-1 p-6 md:p-8">
        <ActiveChips />

        <!-- Tabs: Pilots / Upgrades -->
        <div class="flex items-center gap-6 mb-6">
            <button
                class="text-lg font-sans font-bold transition-colors {tab ===
                'pilots'
                    ? 'text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => {
                    tab = "pilots";
                    page = 1;
                }}
            >
                Pilots
            </button>
            <button
                class="text-lg font-sans font-bold transition-colors {tab ===
                'upgrades'
                    ? 'text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => {
                    tab = "upgrades";
                    page = 1;
                }}
            >
                Upgrades
            </button>
        </div>

        <!-- Card Grid -->
        <div
            class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
        >
            {#each items as card}
                {@const wr = card.win_rate ?? 0}
                {@const wrColor = getWinRateColor(wr)}

                <div
                    class="bg-terminal-panel border border-border-dark rounded-md overflow-hidden hover:border-secondary/40 transition-colors group"
                >
                    <!-- Card Image -->
                    {#if card.image}
                        <div
                            class="relative w-full aspect-[5/7] overflow-hidden bg-black"
                        >
                            <img
                                src={card.image}
                                alt={card.name}
                                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                loading="lazy"
                            />
                        </div>
                    {:else}
                        <div
                            class="w-full aspect-[5/7] bg-[#0a0a0a] flex items-center justify-center"
                        >
                            <span
                                class="font-xwingship text-5xl text-secondary/30"
                                >{card.ship_icon || "?"}</span
                            >
                        </div>
                    {/if}

                    <!-- Info -->
                    <div class="p-3 space-y-2">
                        <!-- Name + Ship -->
                        <div>
                            <h3
                                class="text-sm font-sans font-bold text-primary leading-tight"
                            >
                                {card.name}
                            </h3>
                            {#if card.ship_name}
                                <p class="text-xs font-mono text-secondary">
                                    {card.ship_name}
                                </p>
                            {/if}
                        </div>

                        <!-- Stats Grid (2x2 or 2x2+1 for XWA) -->
                        <div class="grid grid-cols-2 gap-1">
                            <div
                                class="text-center bg-[#ffffff05] rounded px-1 py-1"
                            >
                                <span class="text-xs font-mono text-primary"
                                    >{card.lists ?? 0}</span
                                >
                                <span
                                    class="text-[9px] font-mono text-secondary block"
                                    >LISTS</span
                                >
                            </div>
                            <div
                                class="text-center bg-[#ffffff05] rounded px-1 py-1"
                            >
                                <span class="text-xs font-mono text-primary"
                                    >{card.games ?? 0}</span
                                >
                                <span
                                    class="text-[9px] font-mono text-secondary block"
                                    >GAMES</span
                                >
                            </div>
                            <div
                                class="text-center bg-[#ffffff05] rounded px-1 py-1"
                            >
                                <span
                                    class="text-xs font-mono font-bold"
                                    style="color: {wrColor};"
                                    >{wr.toFixed(1)}%</span
                                >
                                <span
                                    class="text-[9px] font-mono text-secondary block"
                                    >WR</span
                                >
                            </div>
                            <div
                                class="text-center bg-[#ffffff05] rounded px-1 py-1"
                            >
                                <span class="text-xs font-mono text-primary"
                                    >{card.points ?? 0}</span
                                >
                                <span
                                    class="text-[9px] font-mono text-secondary block"
                                    >PTS</span
                                >
                            </div>
                            {#if isXwa}
                                <div
                                    class="col-span-2 text-center bg-violet-900/10 rounded px-1 py-1"
                                >
                                    <span
                                        class="text-xs font-mono text-violet-300"
                                        >{card.loadout ?? 0}</span
                                    >
                                    <span
                                        class="text-[9px] font-mono text-violet-300/60 block"
                                        >LV</span
                                    >
                                </div>
                            {/if}
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
                    disabled={page <= 1}>← Prev</button
                >
                <span class="text-xs font-mono text-secondary">Page {page}</span
                >
                <button
                    class="px-3 py-1 text-xs font-mono border border-border-dark rounded hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
                    onclick={nextPage}
                    disabled={page * size >= total}>Next →</button
                >
            </div>
        {/if}
    </main>
</div>
