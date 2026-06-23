<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import SortSelector from "$lib/components/SortSelector.svelte";
    import ListRowCard from "$lib/components/ListRowCard.svelte";
    import {
        ALL_FACTIONS,
        getFactionLabel,
        getFactionColor,
        getFactionChar,
    } from "$lib/data/factions";
    import { goto } from "$app/navigation";
    import { page as currentPage } from "$app/state";
    import { filters } from "$lib/stores/filters.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";

    let { data } = $props();

    let page = $state(1);
    let sortBy = $state("Games");
    let sortDirection = $state("desc");
    let selectedFactions = $state<string[]>([]);
    let factionOpen = $state(false);
    let minGames = $state(3);

    const size = 20;
    let total = $state(0);

    // Sync state FROM the URL so direct navigation (e.g. ?page=2) works.
    $effect(() => {
        const urlPage = Number(currentPage.url.searchParams.get('page') ?? '0');
        page = urlPage + 1; // URL is 0-indexed, state is 1-indexed
        const urlSort = currentPage.url.searchParams.get('sort_metric');
        if (urlSort) sortBy = urlSort;
        const urlDir = currentPage.url.searchParams.get('sort_direction');
        if (urlDir) sortDirection = urlDir;
        const urlMinGames = currentPage.url.searchParams.get('min_games');
        if (urlMinGames) minGames = Number(urlMinGames);
    });

    // Track total from the latest promise resolution (for nextPage guard)
    $effect(() => {
        data.itemsPromise.then((resolved: any) => {
            total = Number(resolved.total ?? 0);
        });
    });

    // Re-fetch when local filters change
    $effect(() => {
        // Ensure data is active
        xwingData.setSource(filters.dataSource as any);

        const params = new URLSearchParams();
        params.set("page", String(page - 1));
        params.set("size", String(size));
        params.set("sort_metric", sortBy);
        params.set("sort_direction", sortDirection);
        params.set("min_games", String(minGames));
        params.set("data_source", filters.dataSource);

        for (const f of selectedFactions) params.append("factions", f);
        for (const s of filters.selectedShips) params.append("ships", s);
        for (const format of filters.selectedFormats)
            params.append("formats", format);
        for (const p of filters.selectedSources)
            params.append("sources", p);
        for (const c of filters.selectedContinents)
            params.append("continent", c);
        for (const c of filters.selectedCountries) params.append("country", c);
        for (const c of filters.selectedCities) params.append("city", c);
        if (filters.dateStart) params.set("date_start", filters.dateStart);
        if (filters.dateEnd) params.set("date_end", filters.dateEnd);
        // Skip if URL hasn't changed (prevents loop on mount)
        const newUrl = `?${params.toString()}`;
        if (newUrl === `?${currentPage.url.searchParams.toString()}`) return;
        goto(newUrl, {
            keepFocus: true,
            noScroll: true,
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
            LIST FILTERS
        </span>

        <SortSelector
            bind:sortBy
            bind:sortDirection
            options={[
                { value: "Games", label: "Popularity (Games)" },
                { value: "Win Rate", label: "Win Rate" },
                { value: "Points Cost", label: "Points" },
            ]}
        />

        <!-- Min Games -->
        <div class="space-y-1">
            <span
                class="text-xs font-mono font-bold tracking-wider text-secondary"
                >Min Games</span
            >
            <input
                type="number"
                min="1"
                class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                bind:value={minGames}
            />
        </div>

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
    <title>Lists | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <FilterPanel extra={listFilters} />

    <main class="flex-1 p-6 md:p-8">
        <h1 class="text-2xl font-sans font-bold text-primary mb-1">
            List Browser
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
            {@const listItems = resolved.items ?? []}
            <p class="text-secondary font-mono text-sm mb-6">
                {resolvedTotal} Lists Found
            </p>

            <!-- List Cards -->
            <div class="space-y-3">
                {#each listItems as list}
                    <ListRowCard {list} />
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
                Failed to load lists: {error.message}
            </p>
        {/await}
    </main>
</div>
