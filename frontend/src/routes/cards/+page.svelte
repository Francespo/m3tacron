<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import SortSelector from "$lib/components/SortSelector.svelte";
    import AdvancedFilters from "$lib/components/AdvancedFilters.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import {
        getWinRateColor,
        ALL_FACTIONS,
        getFactionColor,
        getFactionChar,
        getFactionLabel,
    } from "$lib/data/factions";
    import { filters } from "$lib/stores/filters.svelte";
    import { goto } from "$app/navigation";

    let { data } = $props();

    let page = $state(1);
    let sortBy = $state("Popularity");
    let sortDirection = $state("desc");
    let textSearch = $state("");
    let selectedFactions = $state<string[]>([]);
    const size = 20;

    let items = $derived(data.items ?? []);
    let total = $derived(data.total ?? 0);
    let isXwa = $derived(filters.dataSource === "xwa");

    let isAdvanced = $state(false);

    // Let URL load logic handle the tab, we will drive updates
    $effect(() => {
        const params = new URLSearchParams();
        params.set("tab", data.tab);
        params.set("page", String(page - 1));
        params.set("size", String(size));
        params.set("data_source", filters.dataSource);
        params.set("sort_metric", sortBy);
        params.set("sort_direction", sortDirection);
        if (textSearch) params.set("search", textSearch);
        for (const format of filters.selectedFormats)
            params.append("formats", format);
        for (const f of selectedFactions) params.append("factions", f);
        for (const s of filters.selectedShips) params.append("ships", s);

        // Advanced Filters
        if (filters.pointsMin) params.set("points_min", filters.pointsMin);
        if (filters.pointsMax) params.set("points_max", filters.pointsMax);
        if (filters.loadoutMin && filters.dataSource === "xwa")
            params.set("loadout_min", filters.loadoutMin);
        if (filters.loadoutMax && filters.dataSource === "xwa")
            params.set("loadout_max", filters.loadoutMax);
        if (filters.isUnique) params.set("is_unique", "true");
        if (filters.isLimited) params.set("is_limited", "true");
        if (filters.isGeneric) params.set("is_not_limited", "true");
        for (const b of filters.selectedBaseSizes)
            params.append("base_sizes", b);

        if (data.tab === "pilots") {
            if (filters.initMin) params.set("init_min", filters.initMin);
            if (filters.initMax) params.set("init_max", filters.initMax);
            if (filters.hullMin) params.set("hull_min", filters.hullMin);
            if (filters.hullMax) params.set("hull_max", filters.hullMax);
            if (filters.shieldsMin)
                params.set("shields_min", filters.shieldsMin);
            if (filters.shieldsMax)
                params.set("shields_max", filters.shieldsMax);
            if (filters.agilityMin)
                params.set("agility_min", filters.agilityMin);
            if (filters.agilityMax)
                params.set("agility_max", filters.agilityMax);
            if (filters.attackMin) params.set("attack_min", filters.attackMin);
            if (filters.attackMax) params.set("attack_max", filters.attackMax);
        }
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
                class="flex-1 py-1 text-xs font-mono text-center transition-colors {!isAdvanced
                    ? 'bg-[#ffffff14] text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => (isAdvanced = false)}>Basic</button
            >
            <button
                class="flex-1 py-1 text-xs font-mono text-center transition-colors {isAdvanced
                    ? 'bg-[#ffffff14] text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => (isAdvanced = true)}>Advanced</button
            >
        </div>

        {#if isAdvanced}
            <AdvancedFilters isPilotsTab={data.tab === "pilots"} />
        {/if}

        <SortSelector
            bind:sortBy
            bind:sortDirection
            options={[
                { value: "Popularity", label: "Popularity (Lists)" },
                { value: "Win Rate", label: "Win Rate" },
                { value: "Games", label: "Popularity (Games)" },
                { value: "Name", label: "Name" },
                { value: "Cost", label: "Points Cost" },
                ...(data.tab === "pilots" && isXwa
                    ? [{ value: "Loadout", label: "Loadout Value" }]
                    : []),
            ]}
        />

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

        {#if data.tab === "pilots"}
            <ShipChassisFilter {selectedFactions} />
        {/if}
    </div>
{/snippet}

<svelte:head>
    <title>Cards | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <FilterPanel extra={cardFilters} />

    <main class="flex-1 p-6 md:p-8">
        <!-- Tabs: Pilots / Upgrades -->
        <div class="flex items-center gap-6 mb-6">
            <button
                class="text-lg font-sans font-bold transition-colors {data.tab ===
                'pilots'
                    ? 'text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => {
                    import("$app/navigation").then(({ goto }) =>
                        goto("?tab=pilots&page=0", {
                            keepFocus: true,
                            noScroll: true,
                            replaceState: true,
                        }),
                    );
                }}
            >
                Pilots
            </button>
            <button
                class="text-lg font-sans font-bold transition-colors {data.tab ===
                'upgrades'
                    ? 'text-primary'
                    : 'text-secondary hover:text-primary'}"
                onclick={() => {
                    import("$app/navigation").then(({ goto }) =>
                        goto("?tab=upgrades&page=0", {
                            keepFocus: true,
                            noScroll: true,
                            replaceState: true,
                        }),
                    );
                }}
            >
                Upgrades
            </button>
        </div>

        <!-- Card Grid -->
        <div
            class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
        >
            {#each items as card}
                {@const wr = Number(card.win_rate ?? 0)}
                {@const wrColor = getWinRateColor(wr)}
                {@const fColor = card.faction
                    ? getFactionColor(card.faction)
                    : undefined}
                {@const fChar = card.faction
                    ? getFactionChar(card.faction)
                    : undefined}

                <a
                    href={`/${data.tab === "pilots" ? "pilot" : "upgrade"}/${card.xws}`}
                    class="block h-full group"
                >
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-xl overflow-hidden hover:border-primary/40 transition-all duration-300 hover:scale-[1.02] hover:z-10 flex flex-col relative h-full"
                    >
                        <!-- Card Image -->
                        {#if card.image}
                            <div
                                class="relative w-full overflow-hidden bg-black flex-shrink-0 flex items-center justify-center p-2"
                            >
                                <img
                                    src={card.image}
                                    alt={card.name}
                                    class="max-w-full max-h-[300px] object-contain drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]"
                                    loading="lazy"
                                />
                            </div>
                        {:else}
                            <div
                                class="w-full flex-shrink-0 h-[200px] bg-[#0a0a0a] flex items-center justify-center"
                            >
                                <i
                                    class="xwing-miniatures-ship xwing-miniatures-ship-{card.ship_xws ||
                                        ''} text-5xl text-secondary/30"
                                ></i>
                            </div>
                        {/if}

                        <!-- Info -->
                        <div
                            class="p-4 flex-1 flex flex-col justify-between bg-gradient-to-t from-black/60 to-transparent"
                        >
                            <!-- Name + Ship -->
                            <div class="mb-4">
                                <h3
                                    class="text-base font-sans font-bold text-primary leading-tight flex items-center gap-2"
                                    title={card.name}
                                >
                                    {card.name}
                                    {#if fChar}
                                        <span
                                            class="font-xwing font-normal opacity-90 drop-shadow-md text-lg"
                                            style={fColor
                                                ? `color: ${fColor};`
                                                : ""}>{fChar}</span
                                        >
                                    {/if}
                                </h3>
                                {#if card.ship_name}
                                    <p
                                        class="text-sm mt-1 font-mono text-secondary line-clamp-1 flex items-center gap-1.5"
                                        title={card.ship_name}
                                    >
                                        <i
                                            class="xwing-miniatures-ship xwing-miniatures-ship-{card.ship_xws ||
                                                ''} text-[14px]"
                                        ></i>
                                        {card.ship_name}
                                    </p>
                                {/if}
                            </div>

                            <!-- Stats Badges -->
                            <div class="flex flex-wrap gap-1.5 mt-auto">
                                <!-- WR -->
                                <div
                                    class="px-1.5 py-0.5 rounded bg-[#ffffff0a] border border-[#ffffff10] flex items-center gap-1"
                                >
                                    <span
                                        class="text-[10px] font-bold"
                                        style="color: {wrColor};"
                                        >{wr.toFixed(1)}%</span
                                    >
                                    <span
                                        class="text-[9px] font-mono text-secondary"
                                        >WR</span
                                    >
                                </div>
                                <!-- Games -->
                                <div
                                    class="px-1.5 py-0.5 rounded bg-[#ffffff0a] border border-[#ffffff10] flex items-center gap-1"
                                >
                                    <span
                                        class="text-[10px] font-bold text-primary"
                                        >{card.games ?? 0}</span
                                    >
                                    <span
                                        class="text-[9px] font-mono text-secondary"
                                        >G</span
                                    >
                                </div>
                                <!-- Lists -->
                                <div
                                    class="px-1.5 py-0.5 rounded bg-[#ffffff0a] border border-[#ffffff10] flex items-center gap-1"
                                >
                                    <span
                                        class="text-[10px] font-bold text-primary"
                                        >{card.lists ?? 0}</span
                                    >
                                    <span
                                        class="text-[9px] font-mono text-secondary"
                                        >L</span
                                    >
                                </div>
                                <!-- PTS -->
                                <div
                                    class="px-1.5 py-0.5 rounded bg-emerald-900/30 border border-emerald-500/30 flex items-center gap-1"
                                >
                                    <span
                                        class="text-[10px] font-bold text-emerald-400"
                                        >{card.points ?? 0}</span
                                    >
                                    <span
                                        class="text-[9px] font-mono text-emerald-500/80"
                                        >PTS</span
                                    >
                                </div>
                                <!-- LV (XWA Only) -->
                                {#if isXwa}
                                    <div
                                        class="px-1.5 py-0.5 rounded bg-violet-900/20 border border-violet-500/20 flex items-center gap-1"
                                    >
                                        <span
                                            class="text-[10px] font-bold text-violet-300"
                                            >{card.loadout ?? 0}</span
                                        >
                                        <span
                                            class="text-[9px] font-mono text-violet-400/80"
                                            >LV</span
                                        >
                                    </div>
                                {/if}
                            </div>
                        </div>
                    </div></a
                >
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
