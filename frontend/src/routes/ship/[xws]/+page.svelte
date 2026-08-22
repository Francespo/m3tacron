<script lang="ts">
    /**
     * Ship Detail Page
     * ----------------
     * Redesigned for readability & aesthetics.
     * Layout:
     *   1. Hero header (huge ship icon, name, faction chips, base stats, key metrics)
     *   2. Pilot breakdown (sortable rows w/ large pilot images)
     *   3. Top performing lists (ListRowCard grid)
     *   4. Top squadrons (custom ship-composition cards)
     *
     * Performance:
     *   - +page.ts already loads 4 endpoints in parallel via Promise.allSettled.
     *     The `data` prop is only available once the load completes, so the
     *     page does not render partial data.
     *   - All pilot / ship images are loaded lazily to keep first paint fast.
     *   - xwingData is kicked off early via an $effect so the manifest is
     *     available when the first row tries to resolve a name.
     */
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import {
        getFactionColor,
        getFactionLabel,
        getWinRateColor,
    } from "$lib/data/factions";
    import ListRowCard from "$lib/components/ListRowCard.svelte";
    import BackLink from "$lib/components/BackLink.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";
    import { API_BASE } from "$lib/api";

    let { data } = $props();

    let info = $derived(data.info ?? { name: data.shipXws, factions: [] });
    // `stats` is replaced by client-side refetches when the faction toggle
    // changes, so the key metrics recompute per faction.
    let stats = $state(data.stats ?? {});
    // `pilots` is replaced by client-side refetches when the faction toggle
    // changes; starts with the server-loaded data (which may already be
    // faction-scoped via ?faction=).
    let pilots = $state([...(data.pilots ?? [])]);
    let lists = $state([...(data.lists ?? [])]);
    let squadrons = $state([...(data.squadrons ?? [])]);

    // Selected faction for the detail view. Initialized from the URL
    // (?faction=rebelalliance carried over from the ships page per-card
    // pill or a global factions filter). Otherwise default to "all" so the
    // detail stats match the ships overview card exactly — even for
    // single-faction ships. Filtering by the ship's sole faction via
    // ps.faction_xws_normalized excludes a few lists with unknown/cross-
    // faction data (HMP: 763→760 games) so it must not be auto-applied.
    let selectedFaction = $state(
        (() => {
            const urlFaction = (data as any).faction && (data as any).faction !== "all" ? (data as any).faction : null;
            if (urlFaction) return urlFaction;
            // Also check actual URL for SSR hydration where data.faction may be missing
            if (typeof window !== 'undefined') {
                const qsFaction = new URLSearchParams(window.location.search).get('faction');
                if (qsFaction && qsFaction !== 'all') return qsFaction;
            }
            return "all";
        })(),
    );

    // True while a faction-scoped pilots refetch is in flight.
    let pilotsLoading = $state(false);

    // Trigger xwingData manifest load so pilot/ship lookups work as soon as
    // the page renders. setSource is a no-op once data is loaded.
    $effect(() => {
        xwingData.setSource(filters.dataSource as any);
    });

    // Primary faction for the glow / accent color.
    // When "all" is selected, use the ship's first faction for a subtle
    // default accent; when a specific faction is selected, use it.
    let primaryFaction = $derived(
        selectedFaction !== "all"
            ? selectedFaction
            : ((info.factions && info.factions[0]) || "unknown"),
    );
    let factionColor = $derived(getFactionColor(primaryFaction));

    // Accent color for borders/glows on sub-capsules: GRAY when "All" is
    // selected, faction-colored when a specific faction is selected.
    let accentColor = $derived(
        selectedFaction === "all" ? "#888888" : factionColor,
    );
    let accentBorder = $derived(
        `color-mix(in srgb, ${accentColor} 30%, transparent)`,
    );
    let accentGlow = $derived(
        `0 0 14px color-mix(in srgb, ${accentColor} 10%, transparent)`,
    );

    // True when the ship can be flown by more than one canonical faction.
    let hasMultipleFactions = $derived(
        (info.factions ?? []).filter((f: string) => f && f !== "unknown").length > 1,
    );

    // Fetch pilots whenever the selected faction changes. The server-scoped
    // data from +page.ts is already correct for the initial faction, so skip
    // the first run (that's what `data.faction` matched).
    let fetchedFaction = $state<string | null>(null);
    $effect(() => {
        // This effect drives client-side refetches (window) — never run it
        // during SSR. In the browser, `window` exists and the fetch fires.
        if (typeof window === "undefined") return;
        const faction = selectedFaction;
        if (fetchedFaction === faction) return;
        fetchedFaction = faction;
        const ds = filters.dataSource || "xwa";

        function buildUrl(path: string, extra?: Record<string, string>) {
            const u = new URL(`${API_BASE}${path}`, window.location.origin);
            // Carry forward every global filter currently in the page URL
            // (formats, date range, location, platforms, player counts,
            // data_source, epic, search, etc.) so the refetch stays
            // consistent with the ships overview the user came from. Skip
            // page/size/sort which are ships-list-specific.
            for (const [k, v] of new URLSearchParams(window.location.search).entries()) {
                if (k === 'page' || k === 'size' || k === 'sort_metric' || k === 'sort_direction') continue;
                if (k === 'faction') continue; // detail toggle handled below
                u.searchParams.append(k, v);
            }
            // data_source: keep server-provided default in sync with client store
            if (!u.searchParams.has('data_source')) u.searchParams.set('data_source', ds);
            if (!u.searchParams.has('epic')) u.searchParams.set('epic', String(filters.includeEpic || false));
            // detail faction toggle (overrides global factions)
            if (faction && faction !== 'all') u.searchParams.set('faction', faction);
            if (extra) for (const [k, v] of Object.entries(extra)) u.searchParams.set(k, v);
            return u;
        }

        const pilotsUrl = buildUrl(`/ship/${data.shipXws}/pilots`);
        const listsUrl = buildUrl(`/ship/${data.shipXws}/lists`, { limit: '10' });
        const squadronsUrl = buildUrl(`/ship/${data.shipXws}/squadrons`, { limit: '10' });
        const statsUrl = buildUrl(`/ship/${data.shipXws}`);

        // Keep the browser URL's `faction` param in sync so a refresh or copy-
        // paste preserves the per-ship faction breakdown. Preserve all other
        // global filters already in the URL.
        {
            const next = new URL(window.location.href);
            if (faction && faction !== 'all') next.searchParams.set('faction', faction);
            else next.searchParams.delete('faction');
            if (next.toString() !== window.location.href) {
                window.history.replaceState({}, '', next.toString());
            }
        }

        pilotsLoading = true;
        fetch(pilotsUrl.toString())
            .then((res) => {
                if (!res.ok) throw new Error(`Failed to load pilots: ${res.status}`);
                return res.json();
            })
            .then((body) => {
                if (fetchedFaction !== faction) return; // stale
                pilots = [...(body.pilots ?? [])];
            })
            .catch((e) => console.error("Failed to load pilots for faction:", faction, e))
            .finally(() => {
                if (fetchedFaction === faction) pilotsLoading = false;
            });
        fetch(listsUrl.toString())
            .then((res) => {
                if (!res.ok) throw new Error(`Failed to load lists: ${res.status}`);
                return res.json();
            })
            .then((body) => {
                if (fetchedFaction !== faction) return; // stale
                lists = [...(body.lists ?? [])];
            })
            .catch((e) => console.error("Failed to load lists for faction:", faction, e));
        fetch(squadronsUrl.toString())
            .then((res) => {
                if (!res.ok) throw new Error(`Failed to load squadrons: ${res.status}`);
                return res.json();
            })
            .then((body) => {
                if (fetchedFaction !== faction) return; // stale
                squadrons = [...(body.squadrons ?? [])];
            })
            .catch((e) => console.error("Failed to load squadrons for faction:", faction, e));
        fetch(statsUrl.toString())
            .then((res) => {
                if (!res.ok) throw new Error(`Failed to load stats: ${res.status}`);
                return res.json();
            })
            .then((body) => {
                if (fetchedFaction !== faction) return; // stale
                stats = body.stats ?? {};
            })
            .catch((e) => console.error("Failed to load stats for faction:", faction, e));
    });

    // Faction toggle handler: clicking a faction chip selects it; clicking
    // "All" (or the currently-selected faction again) returns to all.
    function toggleFaction(faction: string) {
        selectedFaction = selectedFaction === faction ? "all" : faction;
    }

    // Pulls the best-known display name for the ship. The +page.ts already
    // returns info.name (from xwingData2), so this is just a safety net.
    let shipName = $derived(info.name || data.shipXws);
    let shipIconUrl = $derived(
        info.icon || xwingData.getShip(data.shipXws)?.icon || null,
    );

    // ------------------------------------------------------------------------
    // Stats
    // ------------------------------------------------------------------------
    let totalGames = $derived(Math.max(0, stats.games_count || 0));
    let wins = $derived(Math.max(0, stats.wins || 0));
    let winRateNum = $derived(totalGames > 0 ? (wins / totalGames) * 100 : 0);
    let winRateStr = $derived(
        totalGames > 0 ? winRateNum.toFixed(1) + "%" : "NA",
    );
    let listCount = $derived(Math.max(0, stats.list_count || 0));
    let differentListCount = $derived(
        Math.max(0, stats.different_lists_count || 0),
    );
    // Pilot count filtered by the currently selected faction (or total for "all").
    let pilotCount = $derived(xwingData.getPilotCountByShipForFaction(data.shipXws, selectedFaction));

    // Ship base stats from xwingData2 (e.g. attack/agility/hull/shields).
    // Attack uses the firing-arc glyph (same icons as on the card PNG).
    const ARCS_TO_FONT_CLASS: Record<string, string> = {
        "Front Arc": "frontarc",
        "Rear Arc": "reararc",
        "Full Front Arc": "fullfrontarc",
        "Full Rear Arc": "fullreararc",
        "Bullseye Arc": "bullseyearc",
        "Single Turret Arc": "singleturretarc",
        "Double Turret Arc": "doubleturretarc",
        "Left Arc": "leftarc",
        "Right Arc": "rightarc",
    };
    let shipBaseStats = $derived.by(() => {
        const s = xwingData.getShip(data.shipXws);
        return s?.stats ?? info.stats ?? [];
    });

    // ------------------------------------------------------------------------
    // Pilot breakdown — client-side sorting
    // ------------------------------------------------------------------------
    type PilotSortKey =
        | "name"
        | "initiative"
        | "cost"
        | "loadout"
        | "games"
        | "pct"
        | "winrate";

    let pilotSortKey = $state<PilotSortKey>("games");
    let pilotSortDir = $state<"asc" | "desc">("desc");

    // Loadout value only exists for the XWA (2.5) ruleset. Show the sort
    // option + column only when the selected data source is XWA.
    let isXwa = $derived((filters.dataSource || "xwa") === "xwa");

    function togglePilotSort(key: PilotSortKey) {
        if (pilotSortKey === key) {
            pilotSortDir = pilotSortDir === "asc" ? "desc" : "asc";
        } else {
            pilotSortKey = key;
            pilotSortDir = key === "name" ? "asc" : "desc";
        }
    }

    function resolvePilotName(p: { xws: string; name?: string }): string {
        return (
            xwingData.getPilot(p.xws)?.name || p.name || p.xws || "Unknown Pilot"
        );
    }

    function pilotSortValue(p: any): number | string {
        const games = Math.max(0, p.games_count || 0);
        const wins = Math.max(0, p.wins || 0);
        const wr = games > 0 ? (wins / games) * 100 : -1;
        const pct = totalGames > 0 ? (games / totalGames) * 100 : 0;
        const pData = xwingData.getPilot(p.xws);
        const initiative = pData?.initiative ?? p.initiative ?? -1;
        const cost = pData?.cost ?? p.cost ?? 0;
        const loadout = pData?.loadout ?? p.loadout ?? 0;

        switch (pilotSortKey) {
            case "name":
                return resolvePilotName(p).toLowerCase();
            case "initiative":
                return initiative;
            case "cost":
                return cost;
            case "loadout":
                return loadout;
            case "games":
                return games;
            case "pct":
                return pct;
            case "winrate":
                return wr;
            default:
                return games;
        }
    }

    let sortedPilots = $derived.by(() => {
        const dir = pilotSortDir === "asc" ? 1 : -1;
        return [...pilots].sort((a, b) => {
            const va = pilotSortValue(a);
            const vb = pilotSortValue(b);
            if (typeof va === "string" && typeof vb === "string") {
                return va.localeCompare(vb) * dir;
            }
            return ((va as number) - (vb as number)) * dir;
        });
    });

    // ------------------------------------------------------------------------
    // Sort indicator (small arrow icon)
    // ------------------------------------------------------------------------
    function sortIndicator(key: PilotSortKey): string {
        if (pilotSortKey !== key) return "";
        return pilotSortDir === "asc" ? "▲" : "▼";
    }

    function sortHeaderClass(key: PilotSortKey): string {
        const base =
            "px-3 py-2 text-[11px] font-mono uppercase tracking-wider cursor-pointer select-none transition-colors hover:text-primary";
        return pilotSortKey === key
            ? `${base} text-primary`
            : `${base} text-secondary`;
    }

    // ------------------------------------------------------------------------
    // Top Performing Lists — client-side sort
    // ------------------------------------------------------------------------
    // SortBy in the section header drives this state. The backend
    // returns lists already sorted by some default metric; the SortBy
    // control re-sorts in the browser between win rate, games, and
    // popularity (list.popularity or list.count as a fallback).
    type ListSortKey = "winrate" | "games" | "lists";

    let listSortKey = $state<ListSortKey>("winrate");
    let listSortDir = $state<"asc" | "desc">("desc");

    function listSortValue(l: any): number {
        switch (listSortKey) {
            case "winrate": {
                const games = Math.max(0, l.games ?? 0);
                const wins = Math.max(0, l.wins ?? 0);
                if (typeof l.win_rate === "number") return l.win_rate;
                return games > 0 ? (wins / games) * 100 : -1;
            }
            case "games":
                return Math.max(0, l.games ?? 0);
            case "lists":
                return Math.max(0, l.popularity ?? l.count ?? 0);
        }
    }

    let sortedLists = $derived.by(() => {
        const dir = listSortDir === "asc" ? 1 : -1;
        return [...lists].sort((a, b) => {
            const diff = listSortValue(a) - listSortValue(b);
            if (diff !== 0) return diff * dir;
            // Stable tiebreaker: alphabetical by name.
            return (a.name || "").localeCompare(b.name || "");
        });
    });

    // ------------------------------------------------------------------------
    // Top Squadrons — client-side sort
    // ------------------------------------------------------------------------
    // SortBy drives this state. Options mirror the Top Performing Lists
    // control: win rate, games, and popularity (squad.popularity or
    // squad.count). The win_rate field on squadrons is already a
    // percentage; we fall back to wins/games if missing.
    type SquadSortKey = "winrate" | "games" | "lists" | "entries";

    let squadSortKey = $state<SquadSortKey>("winrate");
    let squadSortDir = $state<"asc" | "desc">("desc");

    function squadSortValue(s: any): number {
        switch (squadSortKey) {
            case "winrate": {
                if (typeof s.win_rate === "number") return s.win_rate;
                const games = Math.max(0, s.games ?? 0);
                const wins = Math.max(0, s.wins ?? 0);
                return games > 0 ? (wins / games) * 100 : -1;
            }
            case "games":
                return Math.max(0, s.games ?? 0);
            case "entries":
                return Math.max(0, s.count ?? s.popularity ?? 0);
            case "lists":
                return Math.max(0, s.different_lists_count ?? s.count ?? s.popularity ?? 0);
        }
    }

    let sortedSquadrons = $derived.by(() => {
        const dir = squadSortDir === "asc" ? 1 : -1;
        return [...squadrons].sort((a, b) => {
            const diff = squadSortValue(a) - squadSortValue(b);
            if (diff !== 0) return diff * dir;
            return (a.signature || "").localeCompare(b.signature || "");
        });
    });
</script>

<svelte:head>
    <title>{shipName} — Ship Detail | M3taCron</title>
    <meta
        name="description"
        content="Tournament statistics, pilots, lists, and squadrons flying the {shipName} in X-Wing Miniatures."
    />
</svelte:head>

<div class="min-h-screen p-4 md:p-8 font-sans max-w-7xl mx-auto">
    <!-- ====================================================================
         BACK LINK
         (Content source controls now live in the desktop Sidebar /
         mobile nav drawer; removed from this page header.)
    ===================================================================== -->
    <div class="mb-4">
        <BackLink href="/ships" ariaLabel="Back to Ships" />
    </div>

    <!-- ====================================================================
         HERO HEADER (the "outer capsule" containing image + name + factions)
         - Big ship icon (200px) on the left
         - Ship name, factions, base stats on the right
         - Subtle backdrop ship icon (xwing font) behind everything
         - Small external halo + colored border via accentColor/accentBorder
           (gray when "All" is selected, faction-colored otherwise).
    ===================================================================== -->
    <section
        class="relative bg-terminal-panel border rounded-2xl p-6 md:p-8 mb-6 overflow-hidden"
        style="border-color: {accentBorder}; box-shadow: 0 8px 30px rgba(0,0,0,0.4), {accentGlow};"
    >
        <!-- Backdrop huge xwing-font ship silhouette -->
        <i
            class="xwing-miniatures-ship xwing-miniatures-ship-{data.shipXws} absolute -right-8 -bottom-12 text-[320px] opacity-[0.04] pointer-events-none select-none"
            style="color: {factionColor};"
            aria-hidden="true"
        ></i>

        <div class="relative flex flex-col lg:flex-row gap-6 lg:gap-8 items-start lg:items-center">
            <!-- Big ship icon -->
            <div
                class="flex-shrink-0 w-40 h-40 lg:w-52 lg:h-52 flex items-center justify-center bg-black/50 rounded-2xl border border-white/5 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)]"
            >
                {#if shipIconUrl}
                    <img
                        src={shipIconUrl}
                        alt={shipName}
                        class="max-w-[85%] max-h-[85%] object-contain drop-shadow-[0_4px_20px_rgba(0,0,0,0.6)]"
                        loading="eager"
                    />
                {:else}
                    <i
                        class="xwing-miniatures-ship xwing-miniatures-ship-{data.shipXws} text-9xl"
                        style="color: {factionColor};"
                    ></i>
                {/if}
            </div>

            <!-- Ship identity + base stats -->
            <div class="flex-1 min-w-0 z-10 w-full">
                <!-- Faction chips (toggle) + size badge -->
                <div class="flex items-center gap-2 flex-wrap mb-3">
                    <!-- "All" chip: only for MULTI-faction ships (single-faction
                         ships go straight to their only faction's view). -->
                    {#if (info.factions ?? []).filter((f: string) => f && f !== "unknown").length > 1}
                        <button
                            type="button"
                            onclick={() => toggleFaction("all")}
                            class="faction-chip faction-chip-all inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider border transition-colors {selectedFaction === 'all'
                                ? 'border-primary bg-white/10 text-primary'
                                : 'border-border-dark bg-white/5 text-secondary hover:text-primary hover:border-primary/40'}"
                            aria-pressed={selectedFaction === 'all'}
                            title="Show stats for all factions"
                        >
                            All
                        </button>
                    {/if}
                    {#each info.factions ?? [] as faction}
                        {@const fActive = selectedFaction === faction}
                        {@const fColor = getFactionColor(faction)}
                        {#if hasMultipleFactions}
                            <button
                                type="button"
                                onclick={() => toggleFaction(faction)}
                                class="faction-chip inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider border {fActive
                                    ? 'ring-1 ring-inset ring-white/20'
                                    : ''}"
                                style="--chip-color: {fColor}; color: {fColor}; border-color: {fColor}66; background-color: {fColor}15;"
                                aria-pressed={fActive}
                                title={getFactionLabel(faction)}
                            >
                                <FactionIcon {faction} size="sm" />
                                {getFactionLabel(faction)}
                            </button>
                        {:else}
                            <!-- Single-faction ship: static badge, NOT clickable,
                                 does not alter anything. -->
                            <span
                                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider border cursor-default"
                                style="--chip-color: {fColor}; color: {fColor}; border-color: {fColor}66; background-color: {fColor}15;"
                                title={getFactionLabel(faction)}
                            >
                                <FactionIcon {faction} size="sm" />
                                {getFactionLabel(faction)}
                            </span>
                        {/if}
                    {/each}
                </div>

                <!-- Ship name -->
                <h1
                    class="text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-sans font-bold text-primary leading-none tracking-tight mb-4 break-words"
                >
                    {shipName}
                </h1>

                <!-- Ship base stats (attack/agility/hull/shields) + size -->
                {#if shipBaseStats.length > 0 || info.size}
                    <div class="flex flex-wrap items-center gap-2 mt-4">
                        {#if info.size}
                            <!-- Size as a square-ish pill, grouped with the
                                 stat glyphs (below the ship), not inline with
                                 the faction chips. -->
                            <div
                                class="inline-flex items-center justify-center px-2.5 py-1.5 rounded-md border border-border-dark bg-black/40 min-w-[3.5rem]"
                                title="Ship size"
                            >
                                <span
                                    class="text-[11px] font-mono font-bold uppercase tracking-wider text-secondary"
                                >
                                    {info.size}
                                </span>
                            </div>
                        {/if}
                        {#each shipBaseStats as stat}
                            {@const isAttack = stat.type === "attack"}
                            {@const statFontClass = stat.type === "shields" ? "shield" : stat.type}
                            {@const arcClass = isAttack ? (ARCS_TO_FONT_CLASS[stat.arc ?? ""] ?? "attack") : statFontClass}
                            {@const showStat = isAttack ? true : ["agility","hull","shields"].includes(stat.type)}
                            {#if showStat}
                                {@const statColor = isAttack ? "#f87171"
                                    : stat.type === "agility" ? "#4ade80"
                                    : stat.type === "hull" ? "#facc15"
                                    : stat.type === "shields" ? "#60a5fa"
                                    : factionColor}
                                <div
                                    class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md border border-border-dark bg-black/40"
                                    title={isAttack && stat.arc ? `${stat.arc} ${stat.value}` : stat.type}
                                >
                                    {#if isAttack}
                                        <i class="xwing-miniatures-font xwing-miniatures-font-{arcClass} text-base leading-none" style="color: {statColor};" aria-hidden="true"></i>
                                    {:else}
                                        <i class="xwing-miniatures-font xwing-miniatures-font-{statFontClass} text-base leading-none" style="color: {statColor};" aria-hidden="true"></i>
                                    {/if}
                                    <span class="text-sm font-mono font-bold text-primary">{stat.value}</span>
                                </div>
                            {/if}
                        {/each}
                    </div>
                {/if}
            </div>
        </div>
    </section>

    <!-- ====================================================================
         KEY METRICS — compact stat cards
    ===================================================================== -->
    <section class="grid grid-cols-5 gap-2 mb-10">
        <!-- Squadrons — compact, single line -->
        <div class="bg-terminal-panel border border-border-dark rounded-lg px-3 py-3 flex flex-col gap-1 min-w-0">
            <span class="text-[10px] font-mono text-secondary uppercase tracking-widest whitespace-nowrap">Squadrons</span>
            <span class="text-xl md:text-2xl font-mono font-bold text-primary truncate">{(stats.squadron_count ?? squadrons.length).toLocaleString()}</span>
        </div>

        <!-- Lists — no subtitle -->
        <div class="bg-terminal-panel border rounded-lg px-3 py-3 flex flex-col gap-1 min-w-0" style="border-color: {accentBorder}; box-shadow: {accentGlow};">
            <span class="text-[10px] font-mono text-secondary uppercase tracking-widest whitespace-nowrap">Lists</span>
            <span class="text-xl md:text-2xl font-mono font-bold text-primary truncate">{listCount.toLocaleString()}</span>
        </div>

        <!-- Tournament Entries — renamed from Entries -->
        <div class="bg-terminal-panel border rounded-lg px-3 py-3 flex flex-col gap-1 min-w-0" style="border-color: {accentBorder}; box-shadow: {accentGlow};">
            <span class="text-[10px] font-mono text-secondary uppercase tracking-widest whitespace-nowrap">Tournament Entries</span>
            <span class="text-xl md:text-2xl font-mono font-bold text-primary truncate">{(stats.entries_count ?? listCount).toLocaleString()}</span>
        </div>

        <!-- Total Games — compact, single line -->
        <div
            class="bg-terminal-panel border rounded-lg px-3 py-3 flex flex-col gap-1 min-w-0"
            style="border-color: {accentBorder}; box-shadow: {accentGlow};"
        >
            <span class="text-[10px] font-mono text-secondary uppercase tracking-widest whitespace-nowrap">Total Games</span>
            <span class="text-xl md:text-2xl font-mono font-bold text-primary truncate">{totalGames.toLocaleString()}</span>
        </div>

        <!-- Win Rate -->
        <div
            class="bg-terminal-panel border rounded-lg px-3 py-3 flex flex-col gap-1 min-w-0"
            style="border-color: {accentBorder}; box-shadow: {accentGlow};"
        >
            <span class="text-[10px] font-mono text-secondary uppercase tracking-widest whitespace-nowrap">Win Rate</span>
            <span class="text-xl md:text-2xl font-mono font-bold truncate" style="color: {getWinRateColor(winRateNum)};">{winRateStr}</span>
            <span class="text-[10px] font-mono text-secondary truncate">{wins.toLocaleString()} wins</span>
        </div>
    </section>

    <!-- ====================================================================
         PILOT BREAKDOWN
         Sortable rows, large pilot images, clickable to /pilot/{xws}
    ===================================================================== -->
    <section class="mb-12">
        <div class="flex items-center justify-between gap-3 mb-4">
            <h2
                class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 flex items-baseline gap-2"
            >
                Pilot Breakdown <span
                    class="text-secondary text-base font-normal"
                    >({pilots.length})</span
                >
            </h2>
            <SortBy
                value={pilotSortKey}
                direction={pilotSortDir}
                options={[
                    { value: "name", label: "Name" },
                    { value: "initiative", label: "Init" },
                    { value: "cost", label: "Cost" },
                    ...(isXwa ? [{ value: "loadout", label: "Loadout" }] : []),
                    { value: "games", label: "Games" },
                    { value: "pct", label: "% of Games" },
                    { value: "winrate", label: "Win Rate" }
                ]}
                onChange={(v, d) => {
                    pilotSortKey = v as
                        | "name"
                        | "initiative"
                        | "cost"
                        | "loadout"
                        | "games"
                        | "pct"
                        | "winrate";
                    pilotSortDir = d;
                }}
            />
        </div>

        <div
            class="bg-terminal-panel border rounded-lg overflow-hidden shadow-[0_4px_12px_rgba(0,0,0,0.4)]"
            style="border-color: {accentBorder}; box-shadow: 0 4px 12px rgba(0,0,0,0.4), 0 0 22px color-mix(in srgb, {accentColor} 12%, transparent);"
        >
            <!-- Column headers (clickable to sort). Grid gains a Loadout
                 column in XWA mode. -->
            <div
                class="hidden lg:grid {isXwa
                    ? 'grid-cols-[minmax(0,2.2fr)_64px_64px_64px_72px_minmax(0,1.4fr)_84px]'
                    : 'grid-cols-[minmax(0,2.2fr)_64px_64px_72px_minmax(0,1.4fr)_84px]'} gap-3 px-4 py-2.5 border-b border-border-dark bg-[#0c0c0c]"
            >
                <button
                    type="button"
                    class={sortHeaderClass("name") +
                        " text-left rounded-md"}
                    onclick={() => togglePilotSort("name")}
                >
                    Pilot {sortIndicator("name")}
                </button>
                <button
                    type="button"
                    class={sortHeaderClass("initiative") + " text-right rounded-md"}
                    onclick={() => togglePilotSort("initiative")}
                >
                    Init {sortIndicator("initiative")}
                </button>
                <button
                    type="button"
                    class={sortHeaderClass("cost") + " text-right rounded-md"}
                    onclick={() => togglePilotSort("cost")}
                >
                    Cost {sortIndicator("cost")}
                </button>
                {#if isXwa}
                    <button
                        type="button"
                        class={sortHeaderClass("loadout") + " text-right rounded-md"}
                        onclick={() => togglePilotSort("loadout")}
                    >
                        Loadout {sortIndicator("loadout")}
                    </button>
                {/if}
                <button
                    type="button"
                    class={sortHeaderClass("games") + " text-right rounded-md"}
                    onclick={() => togglePilotSort("games")}
                >
                    Games {sortIndicator("games")}
                </button>
                <button
                    type="button"
                    class={sortHeaderClass("pct") + " text-right rounded-md"}
                    onclick={() => togglePilotSort("pct")}
                >
                    % of Games {sortIndicator("pct")}
                </button>
                <button
                    type="button"
                    class={sortHeaderClass("winrate") + " text-right rounded-md"}
                    onclick={() => togglePilotSort("winrate")}
                >
                    Win Rate {sortIndicator("winrate")}
                </button>
            </div>

            <!-- Rows -->
            {#if sortedPilots.length > 0}
                <div class="divide-y divide-border-dark/50">
                    {#each sortedPilots as pilot (pilot.xws)}
                        {@const pData = xwingData.getPilot(pilot.xws)}
                        {@const gamesVal = Math.max(0, pilot.games_count || 0)}
                        {@const winsVal = Math.max(0, pilot.wins || 0)}
                        {@const wrNum = gamesVal > 0 ? (winsVal / gamesVal) * 100 : 0}
                        {@const wrStr =
                            gamesVal > 0 ? wrNum.toFixed(1) + "%" : "NA"}
                        {@const pctOfChassis =
                            totalGames > 0
                                ? (gamesVal / totalGames) * 100
                                : 0}
                        {@const pilotName = resolvePilotName(pilot)}
                        {@const initiative = pData?.initiative ?? pilot.initiative}
                        {@const cost = pData?.cost ?? pilot.cost}
                        {@const loadout = pData?.loadout ?? pilot.loadout}
                        {@const pilotImg = pData?.image}
                        {@const wrBadgeColor = getWinRateColor(wrNum)}
                        <a
                            href="/pilot/{pilot.xws}"
                            class="grid grid-cols-[88px_minmax(0,1fr)] {isXwa
                                ? 'lg:grid-cols-[minmax(0,2.2fr)_64px_64px_64px_72px_minmax(0,1.4fr)_84px]'
                                : 'lg:grid-cols-[minmax(0,2.2fr)_64px_64px_72px_minmax(0,1.4fr)_84px]'} gap-4 px-4 py-3 hover:bg-[#ffffff05] hover:border-l-2 hover:border-l-primary transition-colors group items-center"
                        >
                            <!-- Pilot cell: image + name (one grid column) -->
                            <div
                                class="col-span-2 lg:col-span-1 flex items-center gap-4 min-w-0"
                            >
                                <div
                                    class="w-24 h-24 lg:w-24 lg:h-24 flex-shrink-0 flex items-center justify-center overflow-visible"
                                >
                                    {#if pilotImg}
                                        <img
                                            src={pilotImg}
                                            alt={pilotName}
                                            class="w-full h-full object-contain"
                                            loading="lazy"
                                        />
                                    {:else}
                                        <i
                                            class="xwing-miniatures-ship xwing-miniatures-ship-{data.shipXws} text-4xl"
                                            style="color: {factionColor}; opacity: 0.6;"
                                        ></i>
                                    {/if}
                                </div>
                                <div class="min-w-0 flex-1">
                                    <div
                                        class="text-base font-sans font-bold text-primary group-hover:text-accent transition-colors truncate"
                                    >
                                        {pilotName}
                                    </div>
                                    <!-- Mobile + tablet inline stats -->
                                    <div
                                        class="flex items-center gap-1.5 mt-1 lg:hidden flex-wrap"
                                    >
                                        {#if initiative !== undefined && initiative !== null}
                                            <span
                                                class="px-1.5 py-0.5 text-[10px] font-mono rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30"
                                                >I{initiative}</span
                                            >
                                        {/if}
                                        {#if cost !== undefined && cost !== null}
                                            <span
                                                class="px-1.5 py-0.5 text-[10px] font-mono rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                                >{cost} PT</span
                                            >
                                        {/if}
                                        {#if isXwa && loadout !== undefined && loadout !== null}
                                            <span
                                                class="px-1.5 py-0.5 text-[10px] font-mono rounded-md bg-sky-500/20 text-sky-400 border border-sky-500/30"
                                                >{loadout} LV</span
                                            >
                                        {/if}
                                        <span
                                            class="text-[10px] font-mono text-secondary"
                                        >
                                            · {gamesVal} g
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <!-- Initiative (desktop) -->
                            <div
                                class="hidden lg:flex justify-end items-center"
                            >
                                {#if initiative !== undefined && initiative !== null}
                                    <span
                                        class="px-2 py-0.5 text-xs font-mono rounded-md bg-amber-500/15 text-amber-400 border border-amber-500/20"
                                        >I{initiative}</span
                                    >
                                {:else}
                                    <span class="text-xs font-mono text-secondary"
                                        >—</span
                                    >
                                {/if}
                            </div>

                            <!-- Cost (desktop) -->
                            <div
                                class="hidden lg:flex justify-end items-center"
                            >
                                {#if cost !== undefined && cost !== null}
                                    <span
                                        class="px-2 py-0.5 text-xs font-mono rounded-md bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
                                        >{cost}</span
                                    >
                                {:else}
                                    <span class="text-xs font-mono text-secondary"
                                        >—</span
                                    >
                                {/if}
                            </div>

                            <!-- Loadout (desktop, XWA only) -->
                            {#if isXwa}
                                <div
                                    class="hidden lg:flex justify-end items-center"
                                >
                                    {#if loadout !== undefined && loadout !== null}
                                        <span
                                            class="px-2 py-0.5 text-xs font-mono rounded-md bg-sky-500/15 text-sky-400 border border-sky-500/20"
                                            >{loadout}</span
                                        >
                                    {:else}
                                        <span
                                            class="text-xs font-mono text-secondary"
                                            >—</span
                                        >
                                    {/if}
                                </div>
                            {/if}

                            <!-- Games (desktop) -->
                            <div
                                class="hidden lg:flex justify-end items-center font-mono text-sm text-primary tabular-nums"
                            >
                                {gamesVal.toLocaleString()}
                            </div>

                            <!-- % of Games (desktop) -->
                            <div
                                class="hidden lg:flex justify-end items-center gap-2"
                            >
                                <div
                                    class="w-20 h-1.5 bg-black rounded-full overflow-hidden border border-white/5"
                                >
                                    <div
                                        class="h-full bg-blue-500/60"
                                        style="width: {Math.min(
                                            100,
                                            pctOfChassis,
                                        ).toFixed(1)}%"
                                    ></div>
                                </div>
                                <span
                                    class="text-xs font-mono text-secondary tabular-nums w-12 text-right"
                                >
                                    {pctOfChassis.toFixed(1)}%
                                </span>
                            </div>

                            <!-- Win Rate (desktop) -->
                            <div class="hidden lg:flex justify-end items-center">
                                {#if wrStr !== "NA"}
                                    <span
                                        class="px-2 py-0.5 text-xs font-mono rounded-md font-bold tabular-nums"
                                        style="color: {wrBadgeColor}; background: {wrBadgeColor}18;"
                                    >
                                        {wrStr}
                                    </span>
                                {:else}
                                    <span class="text-xs font-mono text-secondary"
                                        >—</span
                                    >
                                {/if}
                            </div>
                        </a>
                    {/each}
                </div>
            {:else}
                <div class="py-10 text-center text-sm font-mono text-secondary">
                    No pilot data available.
                </div>
            {/if}
        </div>
    </section>

    <!-- ====================================================================
         TOP PERFORMING LISTS
         Uses the existing ListRowCard component for visual consistency.
    ===================================================================== -->
    <section class="mb-12">
        <div class="flex items-center justify-between gap-3 mb-4">
            <h2
                class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 flex items-baseline gap-2"
            >
                <span>Top Performing Lists</span>
                <span class="text-secondary text-base font-normal"
                    >({lists.length})</span
                >
            </h2>
            {#if lists.length > 0}
                <SortBy
                    value={listSortKey}
                    direction={listSortDir}
                    options={[
                        { value: "winrate", label: "Win Rate" },
                        { value: "games", label: "Games" },
                        { value: "lists", label: "Lists" }
                    ]}
                    onChange={(v, d) => {
                        listSortKey = v as ListSortKey;
                        listSortDir = d;
                    }}
                />
            {/if}
        </div>

        {#if lists.length > 0}
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {#each sortedLists as list (list.signature || list.name)}
                    <ListRowCard {list} />
                {/each}
            </div>
        {:else}
            <div class="bg-terminal-panel border border-border-dark rounded-lg py-10 px-6 text-center">
                <p class="text-sm font-mono text-secondary mb-2">No list data available for this ship yet.</p>
                <p class="text-xs font-mono text-secondary/70 mb-4">Lists containing this ship haven't been indexed for the current data source.</p>
                <a href="/lists?min_games=3" class="inline-flex items-center gap-1 text-xs font-mono text-primary hover:text-accent transition-colors border-b border-transparent hover:border-accent">
                    Browse all lists →
                </a>
            </div>
        {/if}
    </section>

    <!-- ====================================================================
         TOP SQUADRONS
         Custom cards: ship composition icons + stats.
    ===================================================================== -->
    <section class="mb-12">
        <div class="flex items-center justify-between gap-3 mb-4">
            <h2
                class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 flex items-baseline gap-2"
            >
                <span>Top Squadrons</span>
                <span class="text-secondary text-base font-normal"
                    >({squadrons.length})</span
                >
            </h2>
            {#if squadrons.length > 0}
                <SortBy
                    value={squadSortKey}
                    direction={squadSortDir}
                    options={[
                        { value: "winrate", label: "Win Rate" },
                        { value: "games", label: "Games" },
                        { value: "lists", label: "Lists" },
                        { value: "entries", label: "Entries" }
                    ]}
                    onChange={(v, d) => {
                        squadSortKey = v as SquadSortKey;
                        squadSortDir = d;
                    }}
                />
            {/if}
        </div>

        {#if squadrons.length > 0}
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {#each sortedSquadrons as squad (squad.signature)}
                    {@const sFaction = squad.faction || "unknown"}
                    {@const sFactionColor = getFactionColor(sFaction)}
                    {@const sGames = Math.max(0, squad.games || 0)}
                    {@const sWins = Math.max(0, squad.wins || 0)}
                    {@const sWrNum =
                        typeof squad.win_rate === "number"
                            ? squad.win_rate
                            : sGames > 0
                              ? (sWins / sGames) * 100
                              : 0}
                    {@const sListCount = Math.max(
                        0,
                        squad.different_lists_count ?? squad.count ?? squad.popularity ?? 0,
                    )}
                    {@const sEntries = Math.max(
                        0,
                        squad.count ?? squad.popularity ?? 0,
                    )}
                    {@const sWrColor = getWinRateColor(sWrNum)}
                    <!-- Aggregate ship counts (e.g. 3x X-wing + 2x Y-wing) -->
                    {@const shipCounts = (() => {
                        const counts = new Map<string, number>();
                        for (const sId of squad.ships || []) {
                            counts.set(sId, (counts.get(sId) ?? 0) + 1);
                        }
                        return Array.from(counts.entries())
                            .map(([id, count]) => ({
                                id,
                                count,
                                name: xwingData.getShip(id)?.name ?? id,
                            }))
                            .sort(
                                (a, b) =>
                                    b.count - a.count ||
                                    a.name.localeCompare(b.name),
                            );
                    })()}
                    <a
                        href="/squadron/{encodeURIComponent(
                            squad.signature || '',
                        )}"
                        class="block group h-full"
                    >
                        <div
                            class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)] hover:border-primary/40 transition-all h-full flex flex-col gap-3 group-hover:bg-[#ffffff03]"
                            style="border-left: 3px solid {sFactionColor};"
                        >
                            <!-- Header: faction + name + games -->
                            <div
                                class="flex items-start justify-between gap-3"
                            >
                                <div class="flex items-center gap-2 min-w-0">
                                    <FactionIcon
                                        faction={sFaction}
                                        size="lg"
                                        className="shrink-0"
                                    />
                                    <span
                                        class="text-[11px] font-mono uppercase tracking-wider text-secondary truncate"
                                        title={getFactionLabel(sFaction)}
                                    >
                                        {getFactionLabel(sFaction)}
                                    </span>
                                </div>
                                <span
                                    class="shrink-0 px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                                >
                                    GAMES {sGames}
                                </span>
                            </div>

                            <!-- Ship composition -->
                            <div
                                class="flex flex-wrap gap-1.5 min-h-[2.5rem] items-center"
                            >
                                {#each shipCounts as sc (sc.id)}
                                    <div
                                        class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-[#ffffff04] border border-white/5"
                                        title="{sc.count}x {sc.name}"
                                    >
                                        {#if sc.count > 1}
                                            <span
                                                class="text-[10px] font-mono font-bold text-secondary"
                                                >{sc.count}x</span
                                            >
                                        {/if}
                                        <i
                                            class="xwing-miniatures-ship xwing-miniatures-ship-{sc.id} text-base"
                                            style="color: {sFactionColor};"
                                        ></i>
                                        <span
                                            class="text-[10px] font-mono text-primary truncate max-w-[7rem]"
                                        >
                                            {sc.name}
                                        </span>
                                    </div>
                                {/each}
                            </div>

                            <!-- Stats footer -->
                            <div
                                class="flex items-center gap-2 pt-3 border-t border-border-dark/60 mt-auto flex-wrap"
                            >
                                <span
                                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                                >
                                    LISTS {sListCount}
                                </span>
                                <span
                                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                                >
                                    ENTRIES {sEntries}
                                </span>
                                <span
                                    class="px-1.5 py-0.5 rounded-md text-[10px] font-mono font-bold"
                                    style="color: {sWrColor}; background: {sWrColor}18;"
                                >
                                    WR {sWrNum.toFixed(1)}%
                                </span>
                                <span
                                    class="ml-auto text-[10px] font-mono text-secondary opacity-60 group-hover:opacity-100 group-hover:text-primary transition-all"
                                    >View Squad →</span
                                >
                            </div>
                        </div>
                    </a>
                {/each}
            </div>
        {:else}
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg py-10 px-6 text-center text-sm font-mono text-secondary"
            >
                No squadron data available for this ship.
            </div>
        {/if}
    </section>
</div>

<style>
    /* Faction chips: on hover, slightly enlarge + emit a glowing halo in
       the chip's own faction color so they read as clickable toggles. */
    .faction-chip {
        --chip-color: #888;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .faction-chip:hover {
        transform: scale(1.06) translateY(-1px);
        box-shadow: 0 0 16px color-mix(in srgb, var(--chip-color) 55%, transparent);
    }
    .faction-chip[aria-pressed="true"] {
        transform: scale(1.03);
        box-shadow: 0 0 14px color-mix(in srgb, var(--chip-color) 45%, transparent);
    }

    /* "All" chip: gray halo (white) on hover/selected */
    .faction-chip-all {
        --chip-color: #cfcfcf;
    }
    .faction-chip-all:hover {
        box-shadow: 0 0 16px rgba(255, 255, 255, 0.45);
    }
    .faction-chip-all[aria-pressed="true"] {
        box-shadow: 0 0 14px rgba(255, 255, 255, 0.35);
    }
</style>
