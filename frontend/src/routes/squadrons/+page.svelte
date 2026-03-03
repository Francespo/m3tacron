<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import ActiveChips from "$lib/components/ActiveChips.svelte";
    import SquadronRowCard from "$lib/components/SquadronRowCard.svelte";
    import {
        ALL_FACTIONS,
        getFactionLabel,
        getFactionColor,
    } from "$lib/data/factions";

    let { data } = $props();

    let page = $state(1);
    let sortBy = $state("games");
    let selectedFactions = $state<string[]>([]);

    const size = 20;
    let items = $derived(data.items ?? []);
    let total = $derived(data.total ?? 0);

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

{#snippet listFilters()}
    <div class="space-y-3">
        <span class="text-xs font-bold tracking-widest text-primary font-mono">
            SQUADRON FILTERS
        </span>

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
                <option value="games">Games (Most)</option>
                <option value="win_rate">Win Rate (Best)</option>
                <option value="popularity">Popularity</option>
            </select>
        </div>

        <!-- Faction Checkboxes -->
        <div class="space-y-1">
            <span
                class="text-xs font-mono font-bold tracking-wider text-secondary"
                >Faction</span
            >
            <div class="space-y-1 max-h-[200px] overflow-y-auto">
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
                        >
                            {#if f === "rebelalliance"}!{:else if f === "galacticempire"}@{:else if f === "scumandvillainy"}#{:else if f === "resistance"}!{:else if f === "firstorder"}+{:else if f === "galacticrepublic"}/{:else if f === "separatistalliance"}.{/if}
                        </span>
                        <span class="font-mono">{getFactionLabel(f)}</span>
                    </label>
                {/each}
            </div>
        </div>
    </div>
{/snippet}

<svelte:head>
    <title>Squadrons | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <FilterPanel extra={listFilters} />

    <main class="flex-1 p-6 md:p-8">
        <ActiveChips />

        <h1 class="text-[32px] font-sans font-bold text-primary mb-1">
            Squadrons
        </h1>
        <p class="text-secondary font-mono text-sm mb-6">
            {total} UNIQUE SQUADRONS
        </p>

        <!-- Squadron Cards -->
        <div class="space-y-3">
            {#each items as list}
                <SquadronRowCard {list} />
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
