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

    let { data } = $props();

    let info = $derived(data.info ?? { name: data.shipXws, factions: [] });
    let stats = $derived(data.stats ?? {});
    let pilots = $derived(data.pilots ?? []);
    let lists = $derived(data.lists ?? []);
    let squadrons = $derived(data.squadrons ?? []);

    // Trigger xwingData manifest load so pilot/ship lookups work as soon as
    // the page renders. setSource is a no-op once data is loaded.
    $effect(() => {
        xwingData.setSource(filters.dataSource as any);
    });

    // Primary faction for the glow / accent color.
    // Ships can belong to multiple factions; use the first one.
    let primaryFaction = $derived(
        (info.factions && info.factions[0]) || "unknown",
    );
    let factionColor = $derived(getFactionColor(primaryFaction));

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
    let pilotCount = $derived(xwingData.getPilotCountByShip(data.shipXws));

    // Ship base stats from xwingData2 (e.g. attack/agility/hull/shields).
    // We index by stat type and render with the matching xwing font glyph.
    const SHIP_STAT_GLYPHS: Record<string, string> = {
        attack: "%",
        agility: "^",
        hull: "&",
        shields: "*",
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
        | "games"
        | "pct"
        | "winrate";

    let pilotSortKey = $state<PilotSortKey>("games");
    let pilotSortDir = $state<"asc" | "desc">("desc");

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

        switch (pilotSortKey) {
            case "name":
                return resolvePilotName(p).toLowerCase();
            case "initiative":
                return initiative;
            case "cost":
                return cost;
            case "games":
                return games;
            case "pct":
                return pct;
            case "winrate":
                return wr;
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
    type ListSortKey = "winrate" | "games" | "popularity";

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
            case "popularity":
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
    type SquadSortKey = "winrate" | "games" | "popularity";

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
            case "popularity":
                return Math.max(0, s.popularity ?? s.count ?? 0);
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
         HERO HEADER
         - Big ship icon (200px) on the left
         - Ship name, factions, base stats on the right
         - Subtle backdrop ship icon (xwing font) behind everything
    ===================================================================== -->
    <section
        class="relative bg-terminal-panel border border-border-dark rounded-2xl p-6 md:p-8 mb-6 overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.4)]"
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
                <!-- Faction chips + size badge -->
                <div class="flex items-center gap-2 flex-wrap mb-3">
                    {#each info.factions ?? [] as faction}
                        <span
                            class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider border"
                            style="color: {getFactionColor(faction)}; border-color: {getFactionColor(
                                faction,
                            )}66; background-color: {getFactionColor(faction)}15;"
                        >
                            <FactionIcon {faction} size="sm" />
                            {getFactionLabel(faction)}
                        </span>
                    {/each}
                    {#if info.size}
                        <span
                            class="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider border border-border-dark bg-white/5 text-secondary"
                        >
                            {info.size}
                        </span>
                    {/if}
                </div>

                <!-- Ship name -->
                <h1
                    class="text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-sans font-bold text-primary leading-none tracking-tight mb-4 break-words"
                >
                    {shipName}
                </h1>

                <!-- Ship base stats (attack/agility/hull/shields) -->
                {#if shipBaseStats.length > 0}
                    <div class="flex flex-wrap items-center gap-2">
                        {#each shipBaseStats as stat}
                            {#if SHIP_STAT_GLYPHS[stat.type] !== undefined}
                                {@const statColor = stat.type === "attack" ? "#f87171"
                                    : stat.type === "agility" ? "#4ade80"
                                    : stat.type === "hull" ? "#facc15"
                                    : stat.type === "shields" ? "#60a5fa"
                                    : factionColor}
                                <div
                                    class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md border border-border-dark bg-black/40"
                                    title={stat.type}
                                >
                                    <span
                                        class="font-xwing text-base leading-none"
                                        style="color: {statColor};"
                                    >
                                        {SHIP_STAT_GLYPHS[stat.type]}
                                    </span>
                                    <span
                                        class="text-sm font-mono font-bold text-primary"
                                    >
                                        {stat.value}
                                    </span>
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
    <section
        class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-10"
    >
        <!-- Total Games -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col gap-1"
        >
            <span
                class="text-[10px] font-mono text-secondary uppercase tracking-widest"
                >Total Games</span
            >
            <span class="text-2xl md:text-3xl font-mono font-bold text-primary"
                >{totalGames.toLocaleString()}</span
            >
        </div>

        <!-- Win Rate -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col gap-1"
        >
            <span
                class="text-[10px] font-mono text-secondary uppercase tracking-widest"
                >Win Rate</span
            >
            <span
                class="text-2xl md:text-3xl font-mono font-bold"
                style="color: {getWinRateColor(winRateNum)};"
            >
                {winRateStr}
            </span>
            <span class="text-[10px] font-mono text-secondary">
                {wins.toLocaleString()} wins
            </span>
        </div>

        <!-- Lists -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col gap-1"
        >
            <span
                class="text-[10px] font-mono text-secondary uppercase tracking-widest"
                >Lists</span
            >
            <span class="text-2xl md:text-3xl font-mono font-bold text-primary"
                >{listCount.toLocaleString()}</span
            >
            <span class="text-[10px] font-mono text-secondary">
                total appearances
            </span>
        </div>

        <!-- Unique Lists -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col gap-1"
        >
            <span
                class="text-[10px] font-mono text-secondary uppercase tracking-widest"
                >Unique Lists</span
            >
            <span class="text-2xl md:text-3xl font-mono font-bold text-primary"
                >{differentListCount.toLocaleString()}</span
            >
            <span class="text-[10px] font-mono text-secondary">
                distinct squads
            </span>
        </div>

        <!-- Pilots -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col gap-1"
        >
            <span
                class="text-[10px] font-mono text-secondary uppercase tracking-widest"
                >Pilots</span
            >
            <span class="text-2xl md:text-3xl font-mono font-bold text-primary"
                >{pilotCount}</span
            >
            <span class="text-[10px] font-mono text-secondary">
                in the {info.size?.toLowerCase() || "chassis"} chassis
            </span>
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
                    { value: "games", label: "Games" },
                    { value: "pct", label: "% of Chassis" },
                    { value: "winrate", label: "Win Rate" }
                ]}
                onChange={(v, d) => {
                    pilotSortKey = v as
                        | "name"
                        | "initiative"
                        | "cost"
                        | "games"
                        | "pct"
                        | "winrate";
                    pilotSortDir = d;
                }}
            />
        </div>

        <div
            class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden shadow-[0_4px_12px_rgba(0,0,0,0.4)]"
        >
            <!-- Column headers (clickable to sort) -->
            <div
                class="hidden lg:grid grid-cols-[minmax(0,2.2fr)_64px_64px_72px_minmax(0,1.4fr)_84px] gap-3 px-4 py-2.5 border-b border-border-dark bg-[#0c0c0c]"
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
                    % of Chassis {sortIndicator("pct")}
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
                        {@const pilotImg = pData?.image}
                        {@const wrBadgeColor = getWinRateColor(wrNum)}
                        <a
                            href="/pilot/{pilot.xws}"
                            class="grid grid-cols-[88px_minmax(0,1fr)] lg:grid-cols-[minmax(0,2.2fr)_64px_64px_72px_minmax(0,1.4fr)_84px] gap-4 px-4 py-3 hover:bg-[#ffffff05] hover:border-l-2 hover:border-l-primary transition-colors group items-center"
                        >
                            <!-- Pilot cell: image + name (one grid column) -->
                            <div
                                class="col-span-2 lg:col-span-1 flex items-center gap-4 min-w-0"
                            >
                                <div
                                    class="w-24 h-24 lg:w-24 lg:h-24 flex-shrink-0 rounded-lg bg-[#0a0a0a] border border-white/5 flex items-center justify-center overflow-hidden"
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

                            <!-- Games (desktop) -->
                            <div
                                class="hidden lg:flex justify-end items-center font-mono text-sm text-primary tabular-nums"
                            >
                                {gamesVal.toLocaleString()}
                            </div>

                            <!-- % of Chassis (desktop) -->
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
                        { value: "popularity", label: "Lists" }
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
                        { value: "popularity", label: "Lists" }
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
                    {@const sPopularity = Math.max(
                        0,
                        squad.popularity ?? squad.count ?? 0,
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
                                    class="shrink-0 px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-secondary"
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
                                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-secondary"
                                >
                                    LISTS {sPopularity}
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
