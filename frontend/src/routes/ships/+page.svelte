<script lang="ts">
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import LocalFilterBar from "$lib/components/LocalFilterBar.svelte";
    import FactionFilter from "$lib/components/FactionFilter.svelte";
    import StatRangeFilter from "$lib/components/StatRangeFilter.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";
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
            import { page as appPage } from "$app/state";

    let { data } = $props();

    let filterOpen = $state(false);
    // Page is now driven solely by client-side pagination over mergedShips.
    // URL's ?page param is only used to seed initial page after navigation.
    let page = $state(typeof window !== 'undefined'
        ? Math.max(1, Number(new URLSearchParams(window.location.search).get('page') || 0) + 1)
        : 1);

    const size = 50;
    let _localRestored = false;
    $effect(() => {
        if (_localRestored) return;
        const _sp = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();
        filters.restoreLocalFilters('ships', _sp);
        _localRestored = true;
    });

    if (!filters.sortBy) { filters.sortBy = "Games"; }
    function isGlobalChip(k:string){ return k.startsWith("format:")||k.startsWith("continent:")||k.startsWith("country:")||k.startsWith("city:")||k.startsWith("source:")||k==="dateStart"||k==="dateEnd"; }
    let shipsLocalChips = $derived(filters.activeChips.filter(c=>!isGlobalChip(c.key)));
    let datasetActive = $derived(filters.activeChips.filter(c=>isGlobalChip(c.key)).length);
    let shipsLocalCount = $derived(shipsLocalChips.length);
    function clearShipsFilters(){ for(const ch of [...shipsLocalChips]) filters.removeChip(ch.key); }

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
        // Persist local filters per route (survives navigation, not shared across routes)
        queueMicrotask(() => filters.saveLocalFilters('ships'));
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

<svelte:head>
    <title>Ships | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <MobileFilterTrigger activeCount={datasetActive} label="Dataset filters" onClick={() => (filterOpen = true)} />
    <MobileFilterDrawer open={filterOpen} onClose={() => (filterOpen = false)} title="Dataset filters" activeCount={datasetActive} dataFilterTitle="Dataset filters" />

    <main class="flex-1 p-6 md:p-8 pb-20 lg:pb-8">
        <div class="flex flex-wrap items-baseline justify-between gap-3 mb-4">
            <h1 class="text-3xl font-sans font-bold text-primary leading-none shrink-0">Ships</h1>
            <div class="flex items-center gap-2 shrink-0 self-center">
                {#if hasLoaded}<span class="hidden lg:inline text-xs font-mono text-secondary">{mergedShips.length} Ships Found</span><span class="hidden lg:inline w-px h-4 bg-white/10 shrink-0" aria-hidden="true"></span>
                {#if pending}<span class="hidden lg:inline"><PendingIndicator active mode="tag" label="Updating…" /></span>{/if}{/if}
                <span class="hidden sm:inline text-xs font-mono text-secondary uppercase tracking-wider">Sort by</span>
                <select class="bg-terminal-panel border border-border-dark rounded-md text-xs font-mono text-primary px-2 py-1.5 focus:outline-none" value={filters.sortBy || "Games"} onchange={(e)=>{filters.sortBy=(e.target as HTMLSelectElement).value;}} aria-label="Sort by"><option value="Lists">Lists</option><option value="Squadrons">Squadrons</option><option value="Entries">Entries</option><option value="Win Rate">Win Rate</option><option value="Games">Games</option></select>
                <button type="button" onclick={()=>{filters.sortDirection=filters.sortDirection==="asc"?"desc":"asc";}} class="inline-flex items-center justify-center w-7 h-7 bg-terminal-panel border border-border-dark rounded-md text-secondary hover:text-primary hover:bg-[#ffffff05] active:bg-[#ffffff14] transition-colors shrink-0" aria-label={filters.sortDirection==="asc"?"Sort ascending":"Sort descending"}>{#if filters.sortDirection==="asc"}<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>{:else}<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>{/if}</button>
            </div>
        </div>
        <div class="mb-6"><LocalFilterBar id="ships-local" label="Ship filters" activeCount={shipsLocalCount} chips={shipsLocalChips} onRemoveChip={(k)=>filters.removeChip(k)} onClear={clearShipsFilters}><div class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-4 items-start auto-rows-min"><FactionFilter /><ShipChassisFilter selectedFactions={filters.selectedFactions} showModeToggle={false} /><StatRangeFilter label="Stat ranges" /></div></LocalFilterBar></div>

        {#if !hasLoaded && failed}
            <div class="mb-6">
                <ErrorPanel
                    title="Failed to load ships"
                    onRetry={retry}
                />
            </div>
        {/if}

        {#if hasLoaded}
            {@const resolvedTotal = mergedShips.length}
            <!-- Client-side paginate mergedShips -->
            {@const startIdx = (page - 1) * size}
            {@const shipItems = mergedShips.slice(startIdx, startIdx + size)}

            <div class="flex items-center gap-2.5 mt-1.5 mb-2 lg:hidden"><p class="text-secondary font-mono text-sm">{resolvedTotal} Ships Found</p><PendingIndicator active={pending} mode="tag" label="Updating…" /></div>

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
                    {@const squadrons = Math.max(0, activeFaction ? (fStats?.squadron_count ?? 0) : (ship.squadron_count ?? 0))}
                    {@const entries = Math.max(0, activeFaction ? (fStats?.entries_count ?? 0) : (ship.entries_count ?? 0))}
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
                                    <span class="text-xs font-mono text-primary">{squadrons}</span>
                                    <span class="text-[9px] font-mono text-secondary block">Squadrons</span>
                                </div>
                                <div class="bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5">
                                    <span class="text-xs font-mono text-primary">{lists}</span>
                                    <span class="text-[9px] font-mono text-secondary block">Lists</span>
                                </div>
                                <div class="bg-[#ffffff05] border border-border-dark rounded-md px-1 py-0.5">
                                    <span class="text-xs font-mono text-primary">{entries}</span>
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

                <div class="flex items-center justify-center gap-2 mt-6"><button class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed" onclick={prevPage} disabled={page <= 1}>← Prev</button><span class="text-xs font-mono text-secondary">Showing {resolvedTotal===0?0:(page-1)*size+1}–{Math.min(page*size,resolvedTotal)} of {resolvedTotal} · Page {page}/{Math.max(1,Math.ceil(resolvedTotal/size))}</span><button class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed" onclick={nextPage} disabled={page*size>=resolvedTotal}>Next →</button></div>
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
