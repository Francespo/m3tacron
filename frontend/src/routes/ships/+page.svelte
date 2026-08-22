<script lang="ts">
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import PendingIndicator from "$lib/components/PendingIndicator.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
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
    import { page as appPage } from "$app/state";

    let { data } = $props();

    let filterOpen = $state(false);
    // Page is now driven solely by client-side pagination over mergedShips.
    // URL's ?page param is only used to seed initial page after navigation.
    let page = $state(typeof window !== 'undefined'
        ? Math.max(1, Number(new URLSearchParams(window.location.search).get('page') || 0) + 1)
        : 1);
    let factionOpen = $state(false);
    const size = 50;

    // Default sort for the ships page when the URL didn't specify one.
    // "Lists" = list_count, the most useful default for browsing ships.
    if (!filters.sortBy) {
        filters.sortBy = "Lists";
    }

    // Merged ship data: all ships from xwingData + stats from API.
    let mergedShips = $state<any[]>([]);
    // First paint gate: `mergedShips` starts empty, so the skeleton shows
    // until the first merge lands. Afterwards a refetch keeps the stale
    // grid visible under the "Updating…" bar instead of blanking it.
    let hasLoaded = $state(false);
    let pending = $state(true);
    let failed = $state(false);
    let lastPromise: any = null;

    function retry() {
        invalidateAll();
    }

    // Per-card faction toggle (multi-faction ships only). The value is the
    // selected faction xws; `undefined`/missing means "all factions".
    // Single-faction ships never write to this map.
    let selectedFactionByShip = $state<Record<string, string>>({});

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

        // A new API promise means a refetch is in flight: keep the stale grid
        // visible and show the updating bar until the new data is merged.
        const p = data.apiShipsPromise;
        if (p !== lastPromise) {
            lastPromise = p;
            pending = true;
            failed = false;
        }

        p.then((apiShips: any[]) => {
            const xwingShips = xwingData.data[xwingData.currentSource]?.ships;
            if (!xwingShips) return; // xwingData not loaded yet

            // Build lookup from API response
            const apiMap = new Map<string, any>();
            for (const s of apiShips) apiMap.set(s.xws, s);

            // Start with ALL ships from xwingData
            const merged: any[] = [];
            // Strict dedupe by ship xws: every chassis may appear in the
            // manifest once and must render exactly once (never once with
            // data and once without).
            const seen = new Set<string>();
            for (const [xws, ship] of Object.entries(xwingShips)) {
                if (seen.has(xws)) continue;
                seen.add(xws);
                // Skip epic-only ships (ships with no standard-legal pilots) unless includeEpic is on
                if (!epic && ship.epic) continue;
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
                    entries_count: apiData?.entries_count ?? apiData?.list_count ?? 0,
                    squadron_count: apiData?.squadron_count ?? 0,
                    // Per-faction breakdown for capsule faction toggle
                    faction_stats: apiData?.faction_stats ?? {},
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
            } else if (currentSortBy === "Entries") {
                merged.sort((a, b) => reverse ? (b.entries_count ?? 0) - (a.entries_count ?? 0) : (a.entries_count ?? 0) - (b.entries_count ?? 0));
            } else if (currentSortBy === "Squadrons") {
                merged.sort((a, b) => reverse ? (b.squadron_count ?? 0) - (a.squadron_count ?? 0) : (a.squadron_count ?? 0) - (b.squadron_count ?? 0));
            } else {
                // Lists = distinct builds
                merged.sort((a, b) => reverse ? b.list_count - a.list_count : a.list_count - b.list_count);
            }

            mergedShips = merged;
            hasLoaded = true;
            pending = false;
        }).catch(() => {
            failed = true;
            pending = false;
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
        if (page * size < mergedShips.length) page++;
    }

    function toggleFaction(f: string) {
        if (filters.selectedFactions.includes(f)) {
            filters.selectedFactions = filters.selectedFactions.filter((x: string) => x !== f);
        } else {
            filters.selectedFactions = [...filters.selectedFactions, f];
        }
    }

    // Per-card faction toggle: select one faction (card recolors + stats
    // filter to that faction) or back to "all factions".
    function selectShipFaction(xws: string, faction: string) {
        selectedFactionByShip[xws] = faction;
    }
    function selectShipAll(xws: string) {
        delete selectedFactionByShip[xws];
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
                class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary active:text-primary active:bg-[#ffffff06] rounded-sm transition-colors"
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
                value={filters.sortBy || "Lists"}
                direction={filters.sortDirection}
                options={[
                    { value: "Lists", label: "Lists" },
                    { value: "Squadrons", label: "Squadrons" },
                    { value: "Entries", label: "Entries" },
                    { value: "Win Rate", label: "Win Rate" },
                    { value: "Games", label: "Games" },
                ]}
                onChange={(v, d) => {
                    filters.sortBy = v;
                    filters.sortDirection = d;
                }}
            />
        </div>

        {#if !hasLoaded}
            {#if failed}
                <div class="mb-6">
                    <ErrorPanel
                        title="Failed to load ships"
                        onRetry={retry}
                    />
                </div>
            {:else}
                <p class="text-secondary font-mono text-sm mb-6">Loading…</p>

                <!-- Loading Skeleton (matches ship card shape: centered icon
                     area + stats grid) -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {#each Array(6) as _}
                        <div
                            class="bg-terminal-panel border border-border-dark rounded-lg p-4 h-64 flex flex-col items-center gap-3"
                        >
                            <div
                                class="flex-1 w-full flex items-center justify-center"
                            >
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded-full w-28 h-28"
                                ></div>
                            </div>
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-3.5 w-2/3"
                            ></div>
                            <div class="grid grid-cols-2 gap-1 w-full">
                                {#each Array(4) as _}
                                    <div
                                        class="animate-pulse bg-[#ffffff06] rounded-md h-9"
                                    ></div>
                                {/each}
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        {:else}
            {@const resolvedTotal = mergedShips.length}
            <!-- Client-side paginate mergedShips -->
            {@const startIdx = (page - 1) * size}
            {@const shipItems = mergedShips.slice(startIdx, startIdx + size)}

            <!-- Stale ships stay visible while a refetch runs: the grid
                 container dims while `pending` and smoothly returns to full
                 opacity; the neutral inline tag next to the count says the
                 update is in flight. -->
            <div class="flex items-center gap-2.5 mb-6">
                <p class="text-secondary font-mono text-sm">
                    {resolvedTotal} Ships Found
                </p>
                <PendingIndicator
                    active={pending}
                    mode="tag"
                    label="Updating…"
                />
            </div>

            <div
                class="transition-opacity duration-200 {pending
                    ? 'opacity-50'
                    : 'opacity-100'}"
            >

                {#if shipItems.length > 0}
                    <!-- Ships Heatmap Grid -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {#each shipItems as ship}
                    {@const shipFactions = (ship.factions ?? [])}
                    <!-- Only the canonical factions (Rebels, Empire, Scum, etc.) get
                         real colors. "all", "unknown", "galactic20empire" and other
                         dirty values are filtered out so the gradient stays clean.
                         Factions are sorted by `ALL_FACTIONS` index so the stripe
                         order is stable across ships and re-renders (e.g. Rebel is
                         always left-most, Empire always second). -->
                    {@const realFactions = shipFactions
                        .filter((f: string) => ALL_FACTIONS.includes(f))
                        .sort((a: string, b: string) => ALL_FACTIONS.indexOf(a) - ALL_FACTIONS.indexOf(b))}
                    {@const realCount = realFactions.length}
                    {@const isMulti = realCount > 1}
                    <!-- Per-card faction toggle state: undefined -> "all factions" -->
                    {@const selectedFaction = selectedFactionByShip[ship.xws] ?? "all"}
                    {@const activeFaction = isMulti && selectedFaction !== "all" ? selectedFaction : null}
                    <!-- The card's visual factions: all of them by default, the
                         selected faction alone when the pill toggle is active. -->
                    {@const cardFactions = activeFaction ? [activeFaction] : realFactions}
                    {@const cardMulti = cardFactions.length > 1}
                    {@const factionKey = cardFactions[0] ?? "unknown"}
                    {@const factionColor = getFactionColor(factionKey)}
                    <!-- Faction-scoped stats (from the API's faction_stats
                         breakdown) or the ship-wide aggregates. When a faction
                         is selected but has no tournament data, the stats are
                         0 (no data) — never the ship-wide totals. -->
                    {@const fStats = activeFaction ? (ship.faction_stats?.[activeFaction] ?? null) : null}
                    {@const games = Math.max(0, activeFaction ? (fStats?.games_count ?? 0) : (ship.games_count ?? 0))}
                    {@const wins = Math.max(0, activeFaction ? (fStats?.wins ?? 0) : (ship.wins ?? 0))}
                    {@const wr = games > 0 ? (wins / games) * 100 : 0}
                    {@const wrColor = getWinRateColor(wr)}
                    {@const lists = Math.max(0, activeFaction ? (fStats?.list_count ?? 0) : (ship.list_count ?? 0))}
                    {@const pilotsCount = Math.max(0, activeFaction ? xwingData.getPilotCountByShipForFaction(ship.xws, activeFaction) : ship.pilots_count ?? 0)}
                    {@const hasData = games > 0}
                    <!-- Glow intensity proportional to games (popularity) -->
                    {@const glowOpacity = Math.min(0.3, (games / 2000) * 0.3)}
                    <!-- Multi-faction gradient: vertical color stripes, one per faction.
                         For 1 faction: empty (CSS uses --faction fallback). For 2+:
                         equal-width stops so the ship icon is visibly split. -->
                    {@const factionGradient = cardMulti
                        ? `linear-gradient(to right, ${cardFactions.map((f: string, i: number) => `${getFactionColor(f)} ${((i * 100) / cardFactions.length).toFixed(2)}% ${(((i + 1) * 100) / cardFactions.length).toFixed(2)}%`).join(', ')})`
                        : ''}

                    <!-- Clicking the capsule opens the ship detail page. Carry
                         forward all active global filters (formats, dates,
                         location, platforms, etc.) so the detail stats stay
                         consistent with the overview card, plus the per-card
                         faction toggle as ?faction=X when a specific faction
                         is selected. -->
                    {@const shipHref = (() => {
                        const sp = new URLSearchParams(appPage.url.search);
                        sp.delete('page');
                        sp.delete('size');
                        sp.delete('sort_metric');
                        sp.delete('sort_direction');
                        if (activeFaction) sp.set('faction', activeFaction);
                        else sp.delete('faction');
                        const qs = sp.toString();
                        return `/ship/${ship.xws}${qs ? `?${qs}` : ''}`;
                    })()}

                    <a href={shipHref} class="block group relative" style="--glow-alpha: {glowOpacity};">
                        <div
                            class="ship-card relative z-[1] bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col items-center gap-2 hover:border-secondary/50 transition-all duration-200"
                            style="--faction: {cardMulti ? '#888' : factionColor}; --wr: {wrColor};"
                            class:ship-card--multi={cardMulti}
                        >
                            <!-- Ship Icon (from X-Wing ship font via CSS pseudo-element).
                                 Single-faction: colored by --faction. Multi-faction:
                                 multi-color horizontal gradient stripes. -->
                            <i
                                class="ship-icon xwing-miniatures-ship xwing-miniatures-ship-{ship.xws ? ship.xws.replace(/[^a-z0-9]/g, '') : ''} transition-transform"
                                style="--icon-faction: {factionColor}; --icon-gradient: {factionGradient};"
                                class:ship-icon--multi={cardMulti}
                            ></i>
                            <!-- Faction pill (top-right corner of EVERY card).
                                 Multi-faction ships: one clickable icon per faction
                                 + a circled "A" (All factions) toggle. Single-faction
                                 ships: a non-clickable badge with the faction icon. -->
                            <div class="absolute top-2 right-2">
                                <div
                                    class="flex items-center gap-1 rounded-full border border-border-dark bg-[#0d0d14]/90 p-0.5"
                                >
                                    {#if realCount > 0}
                                        {#each realFactions as f}
                                            {#if isMulti}
                                                <button
                                                    type="button"
                                                    title={getFactionLabel(f)}
                                                    aria-label={`Show ${getFactionLabel(f)} stats`}
                                                    class="flex h-4 w-4 shrink-0 items-center justify-center rounded-full leading-none transition-opacity {activeFaction === f
                                                        ? 'opacity-100 ring-1 ring-white/40'
                                                        : 'opacity-50 hover:opacity-100'}"
                                                    onclick={(e) => {
                                                        e.preventDefault();
                                                        e.stopPropagation();
                                                        selectShipFaction(ship.xws, f);
                                                    }}
                                                >
                                                    <FactionIcon faction={f} size="xs" className="leading-none" />
                                                </button>
                                            {:else}
                                                <span
                                                    class="flex h-4 w-4 shrink-0 items-center justify-center rounded-full leading-none opacity-80"
                                                    title={getFactionLabel(f)}
                                                >
                                                    <FactionIcon faction={f} size="xs" className="leading-none" />
                                                </span>
                                            {/if}
                                        {/each}
                                    {:else}
                                        <!-- No canonical factions: neutral unknown badge -->
                                        <span class="flex h-4 w-4 shrink-0 items-center justify-center rounded-full leading-none opacity-80" title="Unknown faction">
                                            <FactionIcon faction="unknown" size="xs" className="leading-none" />
                                        </span>
                                    {/if}

                                    {#if isMulti}
                                        <button
                                            type="button"
                                            title="All factions"
                                            aria-label="Show stats across all factions"
                                            class="flex h-4 w-4 shrink-0 items-center justify-center rounded-full font-sans text-[10px] font-bold leading-none transition-colors {activeFaction === null
                                                ? 'border border-primary bg-white/10 text-primary'
                                                : 'border border-transparent text-secondary hover:text-primary'}"
                                            onclick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                selectShipAll(ship.xws);
                                            }}
                                        >
                                            A
                                        </button>
                                    {/if}
                                </div>
                            </div>

                            <!-- Ship Name -->
                            <span
                                class="text-xs font-sans font-bold text-primary text-center leading-tight"
                            >
                                {ship.name || ship.xws || "Unknown Ship"}
                            </span>

                            <!-- Stats Grid: row1 Squadrons/Lists/Entries, row2 Games/WR/Pilots (all L→R) -->
                            <div class="grid grid-cols-3 gap-1 w-full text-center">
                                <div class="bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5">
                                    <span class="text-xs font-mono text-primary">{ship.squadron_count ?? 0}</span>
                                    <span class="text-[9px] font-mono text-secondary block">Squadrons</span>
                                </div>
                                <div class="bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5">
                                    <span class="text-xs font-mono text-primary">{lists}</span>
                                    <span class="text-[9px] font-mono text-secondary block">Lists</span>
                                </div>
                                <div class="bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5">
                                    <span class="text-xs font-mono text-primary">{ship.entries_count ?? lists}</span>
                                    <span class="text-[9px] font-mono text-secondary block">Entries</span>
                                </div>
                                <div class="bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5">
                                    <span class="text-xs font-mono text-primary">{games}</span>
                                    <span class="text-[9px] font-mono text-secondary block">Games</span>
                                </div>
                                <div class="bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5">
                                    <span class="wr-text text-xs font-mono font-bold">{games === 0 ? "NA" : Number(wr).toFixed(1) + "%"}</span>
                                    <span class="text-[9px] font-mono text-secondary block">WR</span>
                                </div>
                                <div class="bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5">
                                    <span class="text-xs font-mono text-primary">{pilotsCount}</span>
                                    <span class="text-[9px] font-mono text-secondary block">Pilots</span>
                                </div>
                            </div>
                        </div>
                    </a>
                {/each}
                    </div>
                {:else}
                    <!-- Empty state: no ships matched the current filters -->
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center space-y-2"
                    >
                        <p
                            class="text-primary font-sans font-bold text-lg tracking-wide"
                        >
                            No ships found
                        </p>
                        <p class="text-secondary font-mono text-sm">
                            Try adjusting your filters, or retry the query.
                        </p>
                        <div class="pt-2">
                            <button
                                type="button"
                                onclick={retry}
                                class="px-4 py-1.5 text-xs font-mono border border-border-dark text-secondary rounded-md hover:bg-[#ffffff08] hover:text-primary active:bg-[#ffffff14] transition-colors"
                            >
                                Try again
                            </button>
                        </div>
                    </div>
                {/if}

                <!-- Pagination -->
                {#if resolvedTotal > size}
                    <div
                        class="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-border-dark"
                    >
                        <button
                            class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                            onclick={prevPage}
                            disabled={page <= 1}
                        >
                            ← Prev
                        </button>
                        <span class="text-xs font-mono text-secondary">Page {page}</span
                        >
                        <button
                            class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                            onclick={nextPage}
                            disabled={page * size >= resolvedTotal}
                        >
                            Next →
                        </button>
                    </div>
                {/if}
            </div>
        {/if}
    </main>
</div>

<style>
    .ship-card {
        --faction: #888;
        --wr: #888;
        /* --glow-alpha intentionally NOT set here: it comes from the card
           wrapper's inline style and is inherited by this element, so the
           single-faction glow keeps the ship's popularity alpha. */
        box-shadow: 0 0 20px color-mix(in srgb, var(--faction) calc(var(--glow-alpha, 0) * 100%), transparent);
        border-color: color-mix(in srgb, var(--faction) 30%, transparent);
    }
    .ship-icon {
        color: var(--icon-faction, var(--faction, #888));
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
        background: var(--icon-gradient, var(--icon-faction, var(--faction)));
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        /* keep the glow readable against multi-color */
        filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.6));
    }

    /* Multi-faction cards: GRAY border + halo (like single-faction ships
       with no data), while the multi-color gradient stays on the icon.
       The gray is set inline via `--faction: #888` on the card. */
    .ship-card--multi {
        /* (no --faction here: it comes inline; this class exists to keep
           the selector semantics explicit) */
    }

    /* All cards scale up on hover (single- and multi-faction alike). The
       transform lives on the wrapper so the glow moves in sync with the
       card expansion. */
    a.block.group.relative {
        transition: transform 0.2s;
    }
    a.block.group.relative:hover {
        transform: scale(1.03) translateY(-0.25rem);
    }

    /* The multi-faction halo/border uses the plain gray box-shadow and
       border from `.ship-card` (via --faction: #888) — same neutral look as
       single-faction ships. The multi-color gradient lives on the icon only
       (--icon-gradient). No extra pseudo-elements needed. */
</style>
