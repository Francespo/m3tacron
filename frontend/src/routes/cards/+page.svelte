<script lang="ts">
    import MobileFilterDrawer from "$lib/components/MobileFilterDrawer.svelte";
    import MobileFilterTrigger from "$lib/components/MobileFilterTrigger.svelte";
    import CardFiltersPanels from "$lib/components/CardFiltersPanels.svelte";
    import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
    import StatRangeFilter from "$lib/components/StatRangeFilter.svelte";
    import PilotCard from "$lib/components/PilotCard.svelte";
    import UpgradeCard from "$lib/components/UpgradeCard.svelte";
    import PendingIndicator from "$lib/components/PendingIndicator.svelte";
    import ContentLoader from "$lib/components/ContentLoader.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import LocalFilterBar from "$lib/components/LocalFilterBar.svelte";
    import { page as pageState } from "$app/state";
    import {
        getWinRateColor,
        ALL_FACTIONS,
        getFactionColor,
        getFactionLabel,
    } from "$lib/data/factions";
    import { invalidateAll } from "$app/navigation";
    import { filters } from "$lib/stores/filters.svelte";
    import { scheduleSync } from "$lib/sync/urlSync.svelte";
    import DebouncedTextInput from "$lib/components/DebouncedTextInput.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { goto } from "$app/navigation";

    let { data } = $props();

    let filterOpen = $state(false);
    let page = $state(1);
    let factionOpen = $state(true);
    let textSearchOpen = $state(true);
    const size = 21;
    let isAdvanced = $state(false);
    const cardSortOpts = [{ value: "Name", label: "Name" },{ value: "Cost", label: "Points Cost" },{ value: "Games", label: "Games" },{ value: "Lists", label: "Lists" },{ value: "Entries", label: "Entries" },{ value: "Squadrons", label: "Squadrons" },{ value: "Win Rate", label: "Win Rate" }] as const;
    // Tab style for Pilots/Upgrades: text tabs (underline) vs pill — user asked to try alternatives to the pill
    const tabStyle: "text" = "text";

    let globalInputOpen = $state(false);
    // Restore per-route local filters from storage if URL has no local params
    let _localRestored = false;
    $effect(() => {
        if (_localRestored) return;
        // Trigger on first mount by reading search string
        const _sp = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();
        filters.restoreLocalFilters('cards', _sp);
        _localRestored = true;
    });
    let globalActive = $derived(
        filters.selectedFormats.length +
        filters.selectedContinents.length +
        filters.selectedCountries.length +
        filters.selectedCities.length +
        filters.selectedSources.length +
        (filters.dateStart || filters.dateEnd ? 1 : 0)
    );

    // Capsules: show real active chips per-type beyond the badge
    let cardLocalChips = $derived(filters.activeChips.filter((chip) => {
        const k = chip.key;
        const isGlobal = k.startsWith("format:") || k.startsWith("continent:") || k.startsWith("country:") || k.startsWith("city:") || k.startsWith("source:") || k === "dateStart" || k === "dateEnd";
        return !isGlobal;
    }));
    let cardLocalCount = $derived(cardLocalChips.length);

    function clearCardFilters() {
        // remove only card-local chips (keep dataset global intact)
        for (const chip of [...cardLocalChips]) filters.removeChip(chip.key);
        isAdvanced = false;
        factionOpen = false;
    }

    // The loader streams card rows in via `itemsPromise` (non-blocking
    // navigation). `resolved` keeps the LAST good payload so filter/sort/
    // page changes never blank the list: stale rows stay visible under a
    // thin "Updating…" bar while the next query runs. Tab switches reset
    // `resolved` because pilots vs upgrades are different content types —
    // a skeleton is the honest feedback there.
    let resolved = $state<any>(null);
    let pending = $state(true);
    let failed = $state(false);
    let lastPromise: any = null;
    let lastTab: string | undefined = undefined;
    let generation = 0;
    let total = $derived(Math.max(0, Math.floor(Number(resolved?.total ?? 0))));
    let isXwa = $derived(filters.dataSource === "xwa");

    $effect(() => {
        const p = data.itemsPromise;
        if (p === lastPromise) return;
        lastPromise = p;
        if (lastTab !== data.tab) {
            lastTab = data.tab;
            resolved = null;
        }
        const gen = ++generation;
        pending = true;
        failed = false;
        p.then((r: any) => {
            if (gen !== generation) return;
            resolved = r;
            pending = false;
        }).catch(() => {
            if (gen !== generation) return;
            failed = true;
            pending = false;
        });
    });

    function retry() {
        invalidateAll();
    }

    // Default sort: when the store starts empty (no URL, no prior visit),
    // set a real metric so the SortBy in the main content header always
    // has a valid selection. "Lists" is a sensible default for both
    // Pilots and Upgrades.
    $effect(() => {
        if (!filters.sortBy) {
            filters.sortBy = "Lists";
        }
    });

    // Ensure data is loaded for the current data source, then push the
    // store + route-local overlay (page, size, tab) to the URL.
    $effect(() => {
        xwingData.setSource(filters.dataSource as any);
        const params = filters.toSearchParams('cards');
        // Overlay route-local URL state (page is 0-indexed in the URL,
        // 1-indexed in the UI; tab/size are route-local concerns).
        params.set('page', String(page - 1));
        params.set('size', String(size));
        if (data.tab) params.set('tab', data.tab);

        scheduleSync(0, params);
        // Persist local filters per route (survives navigation, not shared across routes)
        queueMicrotask(() => filters.saveLocalFilters('cards'));
    });

    function prevPage() {
        if (page > 1) page--;
    }
    function nextPage() {
        if (page * size < total) page++;
    }

    function toggleFaction(f: string) {
        if (filters.selectedFactions.includes(f)) {
            filters.selectedFactions = filters.selectedFactions.filter(
                (x) => x !== f,
            );
        } else {
            filters.selectedFactions = [...filters.selectedFactions, f];
        }
    }
</script>

{#snippet basicFiltersContent()}
    <div class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-4 items-start auto-rows-min">
        <div class="relative rounded-xl border border-white/5 bg-black/20 overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] w-full self-start">
            <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
            <button type="button" onclick={() => (textSearchOpen = !textSearchOpen)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
                <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">Text Search</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {textSearchOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
            </button>
            {#if textSearchOpen}<div class="px-3.5 pb-3.5 pt-1">
            <DebouncedTextInput value={filters.searchName} onDebouncedChange={(v) => { filters.searchName = v; scheduleSync(250); }} placeholder="Search card text" ariaLabel="Search card text" />
            </div>{/if}
        </div>
        <!-- Col 2: Faction — icon-only, uniform grid -->
        <div class="relative rounded-xl border border-white/5 bg-black/20 overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] w-full self-start">
            <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
            <button type="button" onclick={() => (factionOpen = !factionOpen)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
                <span class="flex items-center gap-1.5 text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">
                    Faction
                    {#if filters.selectedFactions.length > 0}<span class="min-w-5 h-5 px-1 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center">{filters.selectedFactions.length}</span>{/if}
                </span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {factionOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
            </button>
            {#if factionOpen}<div class="px-3.5 pb-3.5 pt-1">
                <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
                    {#each ALL_FACTIONS as f}
                        {@const _sel = filters.selectedFactions.includes(f)}
                        <button type="button" title={getFactionLabel(f)} aria-label={getFactionLabel(f)} aria-pressed={_sel} onclick={() => toggleFaction(f)} class="flex flex-col items-center justify-center gap-1 rounded-lg border px-1 py-2 transition-colors {_sel ? 'bg-white border-white shadow-sm' : 'bg-black/30 border-white/10 hover:border-white/20 hover:bg-white/[0.04]'}">
                            <span class="w-7 h-7 inline-flex items-center justify-center leading-none text-lg"><span class="font-xwing leading-none text-lg" style="color: {getFactionColor(f)};">{f === 'rebelalliance' ? '!' : f === 'galacticempire' ? '@' : f === 'scumandvillainy' ? '#' : f === 'resistance' ? '!' : f === 'firstorder' ? '+' : f === 'galacticrepublic' ? '/' : f === 'separatistalliance' ? '.' : '?'}</span></span>
                            <span class="w-3 h-3 rounded-[3px] border flex items-center justify-center shrink-0 {_sel ? 'bg-black/10 border-black/10' : 'bg-black/40 border-white/10'}">
                                {#if _sel}<svg width="7" height="7" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12 10 17 19 7"/></svg>{/if}
                            </span>
                        </button>
                    {/each}
                </div>
            </div>{/if}
        </div>
        {#if data.tab === "pilots"}
            <ShipChassisFilter selectedFactions={filters.selectedFactions} showModeToggle={false} />
        {/if}
    </div>
{/snippet}

{#snippet advancedFiltersContent()}
    <CardFiltersPanels isPilotsTab={data.tab === "pilots"} />
{/snippet}

<svelte:head>
    <title>Cards | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
    <MobileFilterTrigger
        activeCount={globalActive}
        label="Dataset"
        onClick={() => (globalInputOpen = true)}
    />
    <MobileFilterDrawer
        open={globalInputOpen}
        onClose={() => (globalInputOpen = false)}
        title="Dataset filters"
        activeCount={filters.activeChips.length}
        dataFilterTitle="Dataset filters"
        dataFilterDescription="These define the tournament dataset that feeds the card browser. They are separate from the card-specific filters below."
    >
    </MobileFilterDrawer>

    <main class="flex-1 p-6 md:p-8 pb-20 lg:pb-8">
        <!-- Page header — locked: Cards + text+underline tabs baseline-aligned; Sort by standard in header; header+footer count -->
        <div class="flex flex-wrap items-baseline justify-between gap-3 mb-4">
            <div class="flex flex-wrap items-baseline gap-3 sm:gap-5 min-w-0">
                <h1 class="text-3xl font-sans font-bold text-primary leading-none shrink-0">Cards</h1>
                <div class="flex items-baseline gap-5 shrink-0" role="tablist" aria-label="Card type">
                    <button role="tab" aria-selected={data.tab === 'pilots'} class="text-sm font-sans font-bold leading-none pb-2 border-b-2 -mb-px transition-colors {data.tab === 'pilots' ? 'text-primary border-primary' : 'text-secondary border-transparent hover:text-primary'}" onclick={() => goto("?tab=pilots&page=0", { keepFocus: true, noScroll: true, replaceState: true })}>Pilots</button>
                    <button role="tab" aria-selected={data.tab === 'upgrades'} class="text-sm font-sans font-bold leading-none pb-2 border-b-2 -mb-px transition-colors {data.tab === 'upgrades' ? 'text-primary border-primary' : 'text-secondary border-transparent hover:text-primary'}" onclick={() => goto("?tab=upgrades&page=0", { keepFocus: true, noScroll: true, replaceState: true })}>Upgrades</button>
                </div>
            </div>
            <div class="flex items-center gap-2 shrink-0 self-center">
                {#if resolved}
                    <span class="hidden lg:inline text-xs font-mono text-secondary">{Math.max(0, Math.floor(Number(resolved.total ?? 0)))} {data.tab === "pilots" ? "Pilots" : "Upgrades"} Found</span>
                    <span class="hidden lg:inline w-px h-4 bg-white/10 shrink-0" aria-hidden="true"></span>
                {#if pending}<span class="hidden lg:inline"><PendingIndicator active mode="tag" label="Updating…" /></span>{/if}
                {/if}
                <span class="hidden sm:inline text-xs font-mono text-secondary uppercase tracking-wider">Sort by</span>
                <select class="bg-terminal-panel border border-border-dark rounded-md text-xs font-mono text-primary px-2 py-1.5 focus:outline-none" value={filters.sortBy || "Lists"} onchange={(e) => { filters.sortBy = (e.target as HTMLSelectElement).value; }} aria-label="Sort by">
                    {#each cardSortOpts as opt}<option value={opt.value}>{opt.label}</option>{/each}
                </select>
                <button type="button" onclick={() => { filters.sortDirection = filters.sortDirection === "asc" ? "desc" : "asc"; }} class="inline-flex items-center justify-center w-7 h-7 bg-terminal-panel border border-border-dark rounded-md text-secondary hover:text-primary hover:bg-[#ffffff05] active:bg-[#ffffff14] transition-colors shrink-0" aria-label={filters.sortDirection === "asc" ? "Sort ascending" : "Sort descending"}>
                    {#if filters.sortDirection === "asc"}
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
                    {:else}
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>
                    {/if}
                </button>
            </div>
        </div>


        <div class="mb-6">
            <LocalFilterBar id="cards-local" label="Card filters" activeCount={cardLocalCount} chips={cardLocalChips} onRemoveChip={(k) => filters.removeChip(k)} onClear={clearCardFilters}>
                <div class="space-y-4">
                    <div class="flex items-center gap-2">
                        <div class="flex flex-1 bg-black/60 border border-white/10 rounded-full p-1 gap-1">
                            <button type="button" class="flex-1 py-1.5 rounded-full text-xs font-mono font-medium text-center transition-all duration-200 {!isAdvanced ? 'bg-white text-black shadow-sm' : 'text-secondary hover:text-primary'}" onclick={() => (isAdvanced = false)}>Basic</button>
                            <button type="button" class="flex-1 py-1.5 rounded-full text-xs font-mono font-medium text-center transition-all duration-200 {isAdvanced ? 'bg-white text-black shadow-sm' : 'text-secondary hover:text-primary'}" onclick={() => (isAdvanced = true)}>Advanced</button>
                        </div>

                    </div>
                    {#if !isAdvanced}
                        {@render basicFiltersContent()}
                    {:else}
                        {@render advancedFiltersContent()}
                    {/if}
                    <!-- Stat ranges now embedded inside Advanced (Resources row) — no duplicate card here -->
                </div>
            </LocalFilterBar>
        </div>

        <!-- Card Grid -->
        {#if !resolved}
            {#if failed}
                <div class="mb-6">
                    <ErrorPanel
                        title="Failed to load cards"
                        onRetry={retry}
                    />
                </div>
            {:else}
                <p class="text-secondary font-mono text-sm mb-6">Loading…</p>

                <!-- Loading Skeleton (matches PilotCard / UpgradeCard shape) -->
                <div
                    class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
                >
                    {#each Array(6) as _}
                        <div
                            class="bg-terminal-panel border border-border-dark rounded-md p-4 h-48 flex flex-col gap-2"
                        >
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-16 w-full"
                            ></div>
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-3.5 w-3/4"
                            ></div>
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-3 w-1/2"
                            ></div>
                            <div
                                class="mt-auto animate-pulse bg-[#ffffff06] rounded h-3 w-1/3"
                            ></div>
                        </div>
                    {/each}
                </div>
            {/if}
        {:else}
            {@const resolvedTotal = Math.max(0, Math.floor(Number(resolved?.total ?? 0)))}
            {@const cardItems = (resolved?.items ?? []).map((c: any) => ({
                // Sanitize numeric stats before passing into the card
                // components. Phase 0 backend already clamps at the source,
                // but defensive guards here mean a stale or out-of-band
                // payload can never show "-3 games" or "NaN%".
                ...c,
                games_count: Math.max(0, Number(c?.games_count ?? 0)),
                list_count: Math.max(0, Number(c?.list_count ?? c?.lists ?? 0)),
                different_lists_count: Math.max(
                    0,
                    Number(c?.different_lists_count ?? c?.different_list_count ?? 0),
                ),
                squadron_count: Math.max(0, Number(c?.squadron_count ?? 0)),
                entries_count: Math.max(0, Number(c?.entries_count ?? 0)),
                wins: Math.max(0, Number(c?.wins ?? 0)),
            }))}

            <!-- Count: header (always next to Sort) + footer pagination — no duplicate "below filters" row -->
            <div class="flex items-center gap-2.5 mt-1.5 mb-2 lg:hidden">
                <p class="text-secondary font-mono text-sm">{resolvedTotal} {data.tab === "pilots" ? "Pilots" : "Upgrades"} Found</p>
                <PendingIndicator active={pending} mode="tag" label="Updating…" />
            </div>


            <div
                class="transition-opacity duration-200 {pending
                    ? 'opacity-50'
                    : 'opacity-100'}"
            >
                {#if cardItems.length > 0}
                    <div
                        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
                    >
                        {#each cardItems as card (card.xws)}
                            <a
                                href={`/${data.tab === "pilots" ? "pilot" : "upgrade"}/${card.xws}`}
                                class="block h-full group"
                            >
                                {#if data.tab === "pilots"}
                                    <PilotCard pilot={card} />
                                {:else}
                                    <UpgradeCard upgrade={card} />
                                {/if}
                            </a>
                        {/each}
                    </div>
                    {@const _totalPages = Math.max(1, Math.ceil(resolvedTotal / size))}
                    {@const _from = resolvedTotal === 0 ? 0 : (page - 1) * size + 1}
                    {@const _to = Math.min(page * size, resolvedTotal)}
                    <div class="flex items-center justify-center gap-2 mt-6">
                        <button
                            class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                            onclick={prevPage}
                            disabled={page <= 1}>← Prev</button
                        >
                        <span class="text-xs font-mono text-secondary">Showing {_from}–{_to} of {resolvedTotal} · Page {page}/{_totalPages}</span>
                        <button
                            class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                            onclick={nextPage}
                            disabled={page * size >= resolvedTotal}>Next →</button
                        >
                    </div>
                {:else}
                    <!-- Empty state: no cards matched the current filters -->
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center space-y-2"
                    >
                        <p
                            class="text-primary font-sans font-bold text-lg tracking-wide"
                        >
                            No {data.tab === "pilots" ? "pilots" : "upgrades"} found
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
            </div>
        {/if}
    </main>
</div>
