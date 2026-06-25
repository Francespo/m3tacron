<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
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
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import { filters } from "$lib/stores/filters.svelte";

    let { data } = $props();

    let filterOpen = $state(false);
    let page = $state(1);
    let factionOpen = $state(false);

    const size = 20;
    let total = $state(0);

    // Track total from the latest promise resolution (for nextPage guard)
    $effect(() => {
        data.itemsPromise.then((resolved: any) => {
            total = Number(resolved.total ?? 0);
        });
    });

    // Re-fetch when filters change (URL synchronization)
    $effect(() => {
        const params = filters.toSearchParams('squadrons');
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

    function toggleFaction(f: string) {
        if (filters.selectedFactions.includes(f)) {
            filters.selectedFactions = filters.selectedFactions.filter((x: string) => x !== f);
        } else {
            filters.selectedFactions = [...filters.selectedFactions, f];
        }
    }
</script>

{#snippet filterBody()}
    <div class="space-y-3">
        <span class="text-xs font-bold tracking-widest text-primary font-mono">
            SQUADRON FILTERS
        </span>

        <!-- Sort By -->
        <SortSelector
            bind:sortBy={filters.sortBy}
            bind:sortDirection={filters.sortDirection}
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
                    {#if filters.selectedFactions.length > 0}
                        <span
                            class="text-[10px] bg-white/10 text-secondary px-1.5 rounded-full font-mono"
                        >
                            {filters.selectedFactions.length}
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
                                checked={filters.selectedFactions.includes(f)}
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

        <ShipChassisFilter selectedFactions={filters.selectedFactions} />
    </div>
{/snippet}

<svelte:head>
    <title>Squadrons | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
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

    <main class="flex-1 p-6 md:p-8 pb-20 lg:pb-8">
        <ActiveChips />

        <h1 class="text-[32px] font-sans font-bold text-primary mb-1">
            Squadrons
        </h1>

        {#await data.itemsPromise}
            <p class="text-secondary font-mono text-sm mb-6">Loading...</p>

            <!-- Loading Skeleton -->
            <div class="space-y-3">
                {#each Array(5) as _}
                    <div class="animate-pulse bg-[#ffffff06] rounded-lg h-24 border border-border-dark"></div>
                {/each}
            </div>
        {:then resolved}
            {@const resolvedTotal = Number(resolved.total ?? 0)}
            {@const squadronItems = resolved.items ?? []}
            <p class="text-secondary font-mono text-sm mb-6">
                {resolvedTotal} UNIQUE SQUADRONS
            </p>

            <!-- Squadron Cards -->
            <div class="space-y-3">
                {#each squadronItems as list}
                    <SquadronRowCard {list} />
                {/each}
            </div>

            <!-- Pagination -->
            {#if resolvedTotal > size}
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
                        disabled={page * size >= resolvedTotal}
                    >
                        Next →
                    </button>
                </div>
            {/if}
        {:catch error}
            <p class="text-red-400 font-mono text-sm mb-6">
                Failed to load squadrons: {error.message}
            </p>
        {/await}
    </main>
</div>
