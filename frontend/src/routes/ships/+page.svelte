<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import {
        getFactionColor,
        getFactionLabel,
        getWinRateColor,
        ALL_FACTIONS,
    } from "$lib/data/factions";
    import { invalidateAll } from "$app/navigation";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import Toggle from "$lib/components/Toggle.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";

    let { data } = $props();

    let filterOpen = $state(false);
    let total = $state(0);
    let page = $state(1);
    let factionOpen = $state(false);
    const size = 50;

    // Default sort for the ships page when the URL didn't specify one.
    // "Popularity" = list_count, the most useful default for browsing ships.
    if (!filters.sortBy) {
        filters.sortBy = "Popularity";
    }

    // Merged ship data: all ships from xwingData + stats from API
    let mergedShips = $state<any[]>([]);

    // Sync state FROM the URL so direct navigation (e.g. ?page=2) works.
    // URL hydration is now handled centrally by the layout via
    // `filters.applyFromSearchParams` + `clearPendingSync`; routes only need
    // the round-trip write effect below.

    // Merge API data with xwingData when any dependency changes
    $effect(() => {
        // Read reactive values synchronously so $effect tracks them
        const epic = filters.includeEpic;
        const currentSortBy = filters.sortBy;
        const currentSortDir = filters.sortDirection;
        // Chassis filter — backend already receives `?ships=...`, but the merge
        // iterates over the full xwingData manifest, so we have to apply the
        // filter client-side too or un-selected ships leak through with 0 stats.
        const selectedShips = filters.selectedShips;
        // Trigger xwingData load (and re-run this effect when it resolves).
        xwingData.setSource(filters.dataSource as any);

        data.apiShipsPromise.then((apiShips: any[]) => {
            const xwingShips = xwingData.data[xwingData.currentSource]?.ships;
            if (!xwingShips) return; // xwingData not loaded yet

            // Build lookup from API response
            const apiMap = new Map<string, any>();
            for (const s of apiShips) apiMap.set(s.xws, s);

            // Start with ALL ships from xwingData
            const merged: any[] = [];
            for (const [xws, ship] of Object.entries(xwingShips)) {
                // Skip epic-only (Huge) ships unless includeEpic is on
                if (!epic && ship.size === "Huge") continue;
                // Skip ships not in the chassis filter (when one is active)
                if (selectedShips.length > 0 && !selectedShips.includes(xws)) continue;

                const apiData = apiMap.get(xws);
                merged.push({
                    xws,
                    name: ship.name,
                    factions: ship.factions ?? [],
                    games_count: apiData?.games_count ?? 0,
                    wins: apiData?.wins ?? 0,
                    list_count: apiData?.list_count ?? 0,
                    pilots_count: xwingData.getPilotCountByShip(xws),
                });
            }

            // Sort
            const reverse = currentSortDir === "desc";
            if (currentSortBy === "Win Rate") {
                merged.sort((a, b) => {
                    const wrA = a.games_count > 0 ? a.wins / a.games_count : 0;
                    const wrB = b.games_count > 0 ? b.wins / b.games_count : 0;
                    return reverse ? wrB - wrA : wrA - wrB;
                });
            } else if (currentSortBy === "Name") {
                merged.sort((a, b) => reverse ? b.name.localeCompare(a.name) : a.name.localeCompare(b.name));
            } else if (currentSortBy === "Games") {
                merged.sort((a, b) => reverse ? b.games_count - a.games_count : a.games_count - b.games_count);
            } else {
                // Popularity = list_count
                merged.sort((a, b) => reverse ? b.list_count - a.list_count : a.list_count - b.list_count);
            }

            mergedShips = merged;
            total = merged.length;
        });
    });

    // Trigger URL updates on filter changes
    $effect(() => {
        // Ensure data is active
        xwingData.setSource(filters.dataSource as any);

        const params = filters.toSearchParams('ships');
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
        <div class="flex items-center gap-2">
            <span class="text-xs font-bold tracking-widest text-primary font-mono">
                SHIP FILTERS
            </span>
        </div>

        <!-- Sort By was moved to the main content section header
             (rendered by SortBy) to give the list a single canonical
             sort control. The old sidebar SortSelector was removed. -->

        <!-- Faction -->
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
                <div class="pb-3 space-y-1 max-h-[180px] overflow-y-auto pl-2">
                    {#each ALL_FACTIONS as f}
                        <label
                            class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                        >
                            <Toggle
                                size="xs"
                                ariaLabel={`Toggle faction ${getFactionLabel(f)}`}
                                checked={filters.selectedFactions.includes(f)}
                                onchange={() => toggleFaction(f)}
                            />
                            <FactionIcon faction={f} size="sm" />
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
    <title>Ships | M3taCron</title>
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
        <div class="flex items-start justify-between gap-3 mb-1 flex-wrap">
            <h1 class="text-3xl font-sans font-bold text-primary">Ships</h1>
            <SortBy
                value={filters.sortBy || "Popularity"}
                direction={filters.sortDirection}
                options={[
                    { value: "Popularity", label: "Lists" },
                    { value: "Win Rate", label: "Win Rate" },
                    { value: "Games", label: "Games" },
                ]}
                onChange={(v, d) => {
                    filters.sortBy = v;
                    filters.sortDirection = d;
                }}
            />
        </div>

        {#await data.itemsPromise}
            <p class="text-secondary font-mono text-sm mb-6">Loading...</p>

            <!-- Loading Skeleton -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each Array(6) as _}
                    <div class="animate-pulse bg-[#ffffff06] rounded-md h-64 border border-border-dark"></div>
                {/each}
            </div>
        {:then _resolved}
            {@const resolvedTotal = mergedShips.length}
            <!-- Client-side paginate mergedShips -->
            {@const startIdx = (page - 1) * size}
            {@const shipItems = mergedShips.slice(startIdx, startIdx + size)}
            <p class="text-secondary font-mono text-sm mb-6">
                {resolvedTotal} Ships Found
            </p>

            <!-- Ships Heatmap Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each shipItems as ship}
                    {@const games = Math.max(0, ship.games_count ?? 0)}
                    {@const wins = Math.max(0, ship.wins ?? 0)}
                    {@const wr = games > 0 ? (wins / games) * 100 : 0}
                    {@const wrColor = getWinRateColor(wr)}
                    {@const lists = Math.max(0, ship.list_count ?? 0)}
                    {@const factionKey = ship.factions?.[0] ?? "unknown"}
                    {@const factionColor = getFactionColor(factionKey)}
                    {@const pilotsCount = Math.max(0, ship.pilots_count ?? 0)}
                    <!-- Glow intensity proportional to games (popularity) -->
                    {@const glowOpacity = Math.min(0.3, (games / 2000) * 0.3)}
                    <!-- Multi-faction gradient: vertical color stripes, one per faction.
                         For 1 faction: empty (CSS uses --faction fallback). For 2+:
                         equal-width stops so the ship icon is visibly split. -->
                    {@const factionCount = ship.factions?.length ?? 0}
                    <!-- Only the canonical factions (Rebels, Empire, Scum, etc.) get
                         real colors. "all", "unknown", "galactic20empire" and other
                         dirty values are filtered out so the gradient stays clean.
                         Factions are sorted by `ALL_FACTIONS` index so the stripe
                         order is stable across ships and re-renders (e.g. Rebel is
                         always left-most, Empire always second). -->
                    {@const realFactions = (ship.factions ?? [])
                        .filter((f: string) => ALL_FACTIONS.includes(f))
                        .sort((a: string, b: string) => ALL_FACTIONS.indexOf(a) - ALL_FACTIONS.indexOf(b))}
                    {@const realCount = realFactions.length}
                    {@const isMulti = realCount > 1}
                    <!-- Equal-width hard stripes: each color gets a `start% end%`
                         range so the browser paints distinct bands instead of
                         interpolating all stops at the same position (which would
                         collapse to a single red→tan blend). Example for 5 factions:
                         red 0% 20%, green 20% 40%, blue 40% 60%, grey 60% 80%, tan 80% 100% -->
                    {@const factionGradient = isMulti
                        ? `linear-gradient(to right, ${realFactions.map((f: string, i: number) => `${getFactionColor(f)} ${((i * 100) / realCount).toFixed(2)}% ${(((i + 1) * 100) / realCount).toFixed(2)}%`).join(', ')})`
                        : ''}
                    <!-- Split halo as a multi-layer box-shadow. `box-shadow` can't
                         paint a gradient natively, so we emit one layer per faction
                         with a horizontal offset that spreads the colors left↔right
                         (matching the ship-icon gradient above). Each layer's alpha
                         is the ship popularity (`--glow-alpha`) so popular ships glow
                         brighter. `box-shadow` is painted outside the element's
                         border-box, so unlike the old `::after` (which used
                         `z-index: -1` and bled through the card background) the glow
                         never enters the card content area. -->
                    {@const multiGlow = isMulti
                        ? realFactions.map((f: string, i: number) => {
                            const step = realCount <= 1 ? 0 : 16 / Math.max(1, realCount - 1);
                            const offset = (i - (realCount - 1) / 2) * step;
                            const alpha = Math.round(glowOpacity * 255).toString(16).padStart(2, '0');
                            return `${offset}px 0px 14px 3px ${getFactionColor(f)}${alpha}`;
                        }).join(', ')
                        : ''}

                    <a href="/ship/{ship.xws}" class="block group">
                        <div
                            class="ship-card relative bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col items-center gap-2 hover:border-secondary/50 group-hover:scale-[1.03] group-hover:-translate-y-1 transition-all duration-200"
                            style="--faction: {factionColor}; --faction-gradient: {factionGradient}; --wr: {wrColor}; --glow-alpha: {glowOpacity}; --multi-glow: {multiGlow};"
                            class:ship-card--multi={isMulti}
                        >
                            <!-- Faction icon(s) (small, top-right) -->
                            <!-- Multi-faction ships (e.g. Z-95 AF4 in Rebels+Republic+Scum) show all
                                 canonical faction glyphs in a row. Dirty values like
                                 "all" / "unknown" / "galactic20empire" are filtered out. -->
                            <div
                                class="absolute top-2 right-2 flex items-center gap-1 opacity-80"
                            >
                                {#if realCount > 1}
                                    {#each realFactions as f}
                                        <FactionIcon faction={f} size="sm" />
                                    {/each}
                                {:else if realCount === 1}
                                    <FactionIcon
                                        faction={realFactions[0]}
                                        size="sm"
                                    />
                                {/if}
                            </div>

                            <!-- Ship Icon (from X-Wing ship font via CSS pseudo-element).
                                 Multi-faction ships render the glyph with a multi-color
                                 horizontal gradient (one stripe per faction). -->
                            <i
                                class="ship-icon xwing-miniatures-ship xwing-miniatures-ship-{ship.xws ? ship.xws.replace(/[^a-z0-9]/g, '') : ''} transition-transform"
                                class:ship-icon--multi={isMulti}
                            ></i>

                            <!-- Ship Name -->
                            <span
                                class="text-xs font-sans font-bold text-primary text-center leading-tight"
                            >
                                {ship.name || ship.xws || "Unknown Ship"}
                            </span>

                            <!-- Stats Grid (2x2) -->
                            <div class="grid grid-cols-2 gap-1 w-full">
                                <div
                                    class="text-center bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5"
                                >
                                    <span
                                        class="wr-text text-xs font-mono font-bold"
                                        >{games === 0
                                            ? "NA"
                                            : Number(wr).toFixed(1) + "%"}</span
                                    >
                                    <span
                                        class="text-[9px] font-mono text-secondary block"
                                        >WR</span
                                    >
                                </div>
                                <div
                                    class="text-center bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5"
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
                                    class="text-center bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5"
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
                                    class="text-center bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5"
                                >
                                    <span class="text-xs font-mono text-primary"
                                        >{pilotsCount}</span
                                    >
                                    <span
                                        class="text-[9px] font-mono text-secondary block"
                                        >Pilots</span
                                    >
                                </div>
                            </div>
                        </div>
                    </a>
                {/each}
            </div>

            <!-- Pagination -->
            {#if resolvedTotal > size}
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
                        disabled={page * size >= resolvedTotal}
                    >
                        Next →
                    </button>
                </div>
            {/if}
        {:catch error}
            <p class="text-red-400 font-mono text-sm mb-6">
                Failed to load ships: {error.message}
            </p>
        {/await}
    </main>
</div>

<style>
    .ship-card {
        --faction: #888;
        --wr: #888;
        --glow-alpha: 0;
        box-shadow: 0 0 20px color-mix(in srgb, var(--faction) calc(var(--glow-alpha) * 100%), transparent);
        border-color: color-mix(in srgb, var(--faction) 30%, transparent);
    }
    .ship-icon {
        color: var(--faction);
        opacity: 0.9;
        font-size: clamp(3rem, 18vw, 8rem);
        line-height: 1;
    }
    .faction-text {
        color: var(--faction);
    }
    .wr-text {
        color: var(--wr);
    }

    /* Multi-faction ships: paint the X-Wing font glyph with a horizontal
       gradient (one stripe per faction). `background-clip: text` makes the
       gradient fill the glyph shape; the surrounding `transparent` color
       keeps the rest of the card untouched. */
    .ship-icon--multi {
        color: transparent;
        background: var(--faction-gradient, var(--faction));
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        /* keep the glow readable against multi-color */
        filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.6));
    }

    /* Multi-faction cards: a 1px gradient border that respects rounded-md.
       We layer a `::before` over the border area, then mask out the
       interior so the underlying panel shows through. */
    .ship-card--multi {
        border-color: transparent;
        /* Override the single-color box-shadow from .ship-card with a
           split halo built from the per-faction colors. The template
           precomputes one box-shadow layer per faction (with a horizontal
           offset) and passes it via the `--multi-glow` custom property.
           `box-shadow` is painted outside the element's border-box, so
           the glow is strictly OUTSIDE the card and never bleeds into
           the ship icon / stats inside it. */
        box-shadow: var(--multi-glow, none);
    }
    .ship-card--multi::before {
        content: '';
        position: absolute;
        inset: 0;
        padding: 1px;
        border-radius: inherit;
        background: var(--faction-gradient, var(--faction));
        /* Mask trick: the first linear-gradient is the "hole" that reveals
           the panel underneath; the second is the "border" itself. */
        -webkit-mask:
            linear-gradient(#000 0 0) content-box,
            linear-gradient(#000 0 0);
        mask:
            linear-gradient(#000 0 0) content-box,
            linear-gradient(#000 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
    }
</style>
