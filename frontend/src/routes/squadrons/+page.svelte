<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import ActiveChips from "$lib/components/ActiveChips.svelte";
    import SquadronRowCard from "$lib/components/SquadronRowCard.svelte";
    import SortSelector from "$lib/components/SortSelector.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import {
        ALL_FACTIONS,
        getFactionLabel,
        getFactionColor,
        getFactionChar,
    } from "$lib/data/factions";
    import { goto } from "$app/navigation";
    import { filters } from "$lib/stores/filters.svelte";

    let { data } = $props();

    let page = $state(1);
    let sortBy = $state("Games");
    let sortDirection = $state("desc");
    let selectedFactions = $state<string[]>([]);
    let factionOpen = $state(false);

    const size = 20;
    let items = $derived(data.items ?? []);
    let total = $derived(data.total ?? 0);

    // Re-fetch when filters change (URL synchronization)
    $effect(() => {
        const params = new URLSearchParams();
        params.set("page", String(page - 1));
        params.set("size", String(size));
        params.set("sort_metric", sortBy);
        params.set("sort_direction", sortDirection);
        params.set("data_source", filters.dataSource);
        for (const f of selectedFactions) params.append("factions", f);
        for (const s of filters.selectedShips) params.append("ships", s);

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
        <SortSelector
            bind:sortBy
            bind:sortDirection
            options={[
                { value: "Games", label: "Games (Most)" },
                { value: "Win Rate", label: "Win Rate (Best)" },
                { value: "Popularity", label: "Popularity" },
            ]}
        />

        <!-- Faction Checkboxes -->
        <div class="border-b border-border-dark mt-1">
            <button
                class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
                onclick={() => (factionOpen = !factionOpen)}
            >
                <div class="flex items-center gap-2">
                    <span class="text-xs font-mono font-bold tracking-wider">
                        Faction
                    </span>
                    {#if selectedFactions.length > 0}
                        <span
                            class="text-[10px] bg-white/10 text-secondary px-1.5 rounded-full font-mono"
                        >
                            {selectedFactions.length}
                        </span>
                    {/if}
                </div>
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="transition-transform {factionOpen
                        ? 'rotate-180'
                        : ''}"><path d="m6 9 6 6 6-6" /></svg
                >
            </button>

            {#if factionOpen}
                <div class="pb-3 space-y-1 max-h-[200px] overflow-y-auto pl-2">
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
                                {getFactionChar(f)}
                            </span>
                            <span class="font-mono">{getFactionLabel(f)}</span>
                        </label>
                    {/each}
                </div>
            {/if}
        </div>

        <ShipChassisFilter {selectedFactions} />
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
