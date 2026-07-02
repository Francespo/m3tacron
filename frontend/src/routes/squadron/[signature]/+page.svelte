<script lang="ts">
    import {
        getWinRateColor,
        getFactionColor,
        getFactionLabel,
    } from "$lib/data/factions";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import BackLink from "$lib/components/BackLink.svelte";
    import CardHoverLink from "$lib/components/CardHoverLink.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    let stats = $derived(data.stats);
    let pilots = $derived(data.pilots);
    let lists = $derived(data.lists);

    // ------------------------------------------------------------------------
    // Top Performing Lists — client-side sort
    // ------------------------------------------------------------------------
    // SortBy in the section header drives this state. `popularity` maps to
    // `list.popularity` (or `list.count` as a fallback, since the enriched
    // payload from the backend can use either field name). `winrate` is
    // computed on demand from `wins / games`.
    type ListSortKey = "winrate" | "games" | "popularity";

    let listSortKey = $state<ListSortKey>("winrate");
    let listSortDir = $state<"asc" | "desc">("desc");

    function listSortValue(l: any): number {
        switch (listSortKey) {
            case "winrate": {
                const games = Math.max(0, l.games ?? 0);
                const wins = Math.max(0, l.wins ?? 0);
                // Pre-computed `win_rate` is preferred (already a percent);
                // fall back to computing from raw counts.
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
            // Primary key: selected sort metric.
            const diff = listSortValue(a) - listSortValue(b);
            if (diff !== 0) return diff * dir;
            // Stable tiebreaker: alphabetical by name so equal-metric
            // entries don't shuffle around on re-render.
            const na = (a.name || "").toLowerCase();
            const nb = (b.name || "").toLowerCase();
            return na.localeCompare(nb);
        });
    });

    // ------------------------------------------------------------------------
    // Pilot Composition — client-side sort
    // ------------------------------------------------------------------------
    // SortBy in the section header drives this state. Options cover the
    // five visible columns: pilot name, cost, initiative, games, and
    // computed win rate. The percent-of-squadron column is derived
    // from games and would be redundant as its own sort key.
    type PilotSortKey = "name" | "cost" | "initiative" | "games" | "winrate";

    let pilotSortKey = $state<PilotSortKey>("games");
    let pilotSortDir = $state<"asc" | "desc">("desc");

    function pilotSortValue(p: any): number | string {
        switch (pilotSortKey) {
            case "name": {
                const pData = xwingData.getPilot(p.pilot_xws);
                return (
                    pData?.name || p.name || p.pilot_xws || ""
                ).toLowerCase();
            }
            case "cost":
                return typeof p.cost === "number" ? p.cost : 0;
            case "initiative":
                return typeof p.initiative === "number" ? p.initiative : -1;
            case "games":
                return Math.max(0, p.games ?? 0);
            case "winrate": {
                if (typeof p.win_rate === "number") return p.win_rate;
                const games = Math.max(0, p.games ?? 0);
                const wins = Math.max(0, p.wins ?? 0);
                return games > 0 ? (wins / games) * 100 : -1;
            }
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

    // Derived from signature (e.g., "bwing,rz1awing,t65xwing")
    // Note: signature is the raw sorted string of ship chassis keys
    let shipsInSquadron = $derived(
        data.signature.split(",").map((s: string) => s.trim()),
    );

    // Human-readable squadron name, deduped with counts when a ship repeats.
    // e.g. "4x TIE/ln Fighter + 2x TIE/sa Bomber". Falls back to the XWS id
    // if the manifest doesn't have a label.
    let squadronName = $derived.by(() => {
        const counts = new Map<string, number>();
        for (const s of shipsInSquadron) {
            counts.set(s, (counts.get(s) ?? 0) + 1);
        }
        return Array.from(counts.entries())
            .map(([xws, count]) => {
                const name = xwingData.getShip(xws)?.name ?? xws;
                return count > 1 ? `${count}x ${name}` : name;
            })
            .join(" + ");
    });

    // Deduped ship counts for the top-component label list. e.g.
    // 3x T-65 X-wing + 2x RZ-1 A-wing. Sorted by count desc, then name asc.
    let shipCounts = $derived.by(() => {
        const counts = new Map<string, number>();
        for (const s of shipsInSquadron) {
            counts.set(s, (counts.get(s) ?? 0) + 1);
        }
        return Array.from(counts.entries())
            .map(([xws, count]) => ({
                xws,
                count,
                name: xwingData.getShip(xws)?.name ?? xws,
            }))
            .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
    });

    // Ensure xwingData manifest is loaded so getShip/getPilot return real
    // human-readable names. Safe to call repeatedly; setSource is a no-op
    // when the requested source is already active and initialized.
    $effect(() => {
        xwingData.setSource(filters.dataSource as any);
    });
</script>

<div class="max-w-7xl mx-auto space-y-8">
    <!-- Back link.
         Content source controls now live in the desktop Sidebar /
         mobile nav drawer; removed from this page header. -->
    <div class="mb-4">
        <BackLink href="/squadrons" ariaLabel="Back to Squadrons" />
    </div>

    {#if !stats}
        <div class="text-center py-12">
            <h2 class="text-xl font-sans font-bold text-primary mb-2">
                Squadron Not Found
            </h2>
            <p class="text-secondary font-mono text-sm">
                We couldn't find data for this squadron combination (or it has
                no recorded games in the current filters).
            </p>
        </div>
    {:else}
        <!-- Page Title -->
        <h1 class="text-3xl font-sans font-bold text-primary mt-4 mb-6">
            {squadronName}
        </h1>

        <!-- Header Section -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-6 md:p-8 flex flex-col md:flex-row gap-8 relative overflow-hidden"
        >
            <!-- Background Glow -->
            <div
                class="absolute -top-32 -right-32 w-96 h-96 rounded-full blur-[100px] pointer-events-none"
                style="background-color: {getFactionColor(stats.faction)}20;"
            ></div>

            <!-- Large Faction Icon -->
            <div
                class="flex-shrink-0 flex items-center justify-center z-10"
            >
                <FactionIcon
                    faction={stats.faction}
                    size="xxl"
                    className="opacity-90"
                />
            </div>

            <!-- Ship Icons + Labels -->
            <div
                class="flex-shrink-0 flex flex-col gap-4 max-w-sm bg-terminal-panel rounded-lg p-6 border border-border-dark z-10"
            >
                <div
                    class="flex items-center justify-center gap-3 flex-wrap"
                >
                    {#each shipsInSquadron as shipId}
                        <i
                            class="xwing-miniatures-ship xwing-miniatures-ship-{shipId}"
                            style="color: {getFactionColor(
                                stats.faction,
                            )}; font-size: 3.5rem;"
                        ></i>
                    {/each}
                </div>
                <div
                    class="flex flex-wrap gap-x-3 gap-y-1 border-t border-border-dark/50 pt-3 justify-center"
                >
                    {#each shipCounts as ship}
                        <span class="text-xs font-mono text-secondary">
                            {ship.count > 1 ? `${ship.count}x ${ship.name}` : ship.name}
                        </span>
                    {/each}
                </div>
            </div>

            <!-- Info / Stats -->
            <div class="flex flex-col justify-center gap-4 z-10 flex-1">
                <!-- Faction Label -->
                <p
                    class="text-secondary font-mono text-xs flex items-center gap-2"
                >
                    <span
                        class="inline-block w-2.5 h-2.5 rounded-full"
                        style="background: {getFactionColor(
                            stats.faction,
                        )}"
                    ></span>
                    {getFactionLabel(stats.faction)}
                </p>

                <!-- Key Metrics -->
                <div class="flex flex-wrap gap-2 mt-2">
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                    >
                        GAMES {Math.max(0, stats.games ?? 0)}
                    </span>
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                    >
                        LISTS {stats.popularity ?? 0}
                    </span>
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold"
                        style="color: {getWinRateColor(Math.min(100, Math.max(0, stats.win_rate ?? 0)))};"
                    >
                        WR {Math.min(100, Math.max(0, Number(stats.win_rate ?? 0))).toFixed(1)}%
                    </span>
                </div>
            </div>
        </div>

        <!-- Pilot Breakdown -->
        <div class="flex items-center justify-between gap-3 mt-12 mb-4">
            <h2
                class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 flex items-baseline gap-2"
            >
                Pilot Composition
                <span class="text-secondary text-base font-normal">({pilots.length})</span>
            </h2>
            {#if pilots.length > 0}
                <SortBy
                    value={pilotSortKey}
                    direction={pilotSortDir}
                    options={[
                        { value: "name", label: "Name" },
                        { value: "cost", label: "Cost" },
                        { value: "initiative", label: "Initiative" },
                        { value: "games", label: "Games" },
                        { value: "winrate", label: "Win Rate" }
                    ]}
                    onChange={(v, d) => {
                        pilotSortKey = v as PilotSortKey;
                        pilotSortDir = d;
                    }}
                />
            {/if}
        </div>

        {#if pilots.length > 0}
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden"
            >
                <div
                    class="grid grid-cols-1 sm:grid-cols-[3fr_1fr_1fr_1fr_1.5fr_1fr] md:grid-cols-[4fr_1fr_1fr_1fr_2fr_1fr] gap-4 p-4 border-b border-border-dark bg-terminal-panel text-xs font-mono text-secondary uppercase tracking-wider"
                >
                    <div>Pilot</div>
                    <div class="text-center hidden sm:block">Ship</div>
                    <div class="text-right hidden sm:block">Cost</div>
                    <div class="text-right hidden sm:block">Games</div>
                    <div class="text-center hidden sm:block">% of Squadron</div>
                    <div class="text-right">Win Rate</div>
                </div>

                <div class="divide-y divide-border-dark/50">
                    {#each sortedPilots as p (p.pilot_xws)}
                        {@const pilotData = xwingData.getPilot(p.pilot_xws)}
                        <div
                            class="relative grid grid-cols-1 sm:grid-cols-[3fr_1fr_1fr_1fr_1.5fr_1fr] md:grid-cols-[4fr_1fr_1fr_1fr_2fr_1fr] gap-4 p-4 border-b border-border-dark pb-2 sm:border-none sm:pb-0 hover:bg-terminal-panel transition-colors items-center group"
                        >
                            <!-- Stretched link covers the whole row so clicking
                                 anywhere navigates to the pilot page. -->
                            <a
                                href="/pilot/{p.pilot_xws}"
                                class="absolute inset-0 z-0"
                                aria-label="View pilot details"
                            ></a>
                            <!-- Name + Image -->
                            <div class="flex items-center gap-3 min-w-0 relative z-10 pointer-events-auto">
                                {#if pilotData?.image}
                                    <img
                                        src={pilotData.image}
                                        alt={pilotData.name ?? p.pilot_xws}
                                        class="w-14 h-14 object-contain rounded-md flex-shrink-0 bg-terminal-panel"
                                        loading="lazy"
                                    />
                                {/if}
                                <CardHoverLink
                                    xws={p.pilot_xws}
                                    type="pilot"
                                    name={pilotData?.name || p.name || p.pilot_xws}
                                    className="font-sans font-bold truncate"
                                />
                            </div>
                            <!-- Ship Icon + Human Name -->
                            <div
                                class="text-center opacity-60 hidden sm:flex items-center justify-center gap-2 truncate"
                            >
                                <i
                                    class="xwing-miniatures-ship xwing-miniatures-ship-{p.ship_xws} text-base opacity-70 flex-shrink-0"
                                ></i>
                                <span
                                    class="text-xs font-mono text-primary truncate"
                                    title={xwingData.getShip(p.ship_xws)?.name || p.name || p.ship_xws}
                                    >{xwingData.getShip(p.ship_xws)?.name || p.name || p.ship_xws}</span
                                >
                            </div>
                            <!-- Cost -->
                            <div
                                class="text-right font-mono text-xs text-green-400 hidden sm:block"
                            >
                                {p.cost} PT
                            </div>
                            <!-- Games -->
                            <div
                                class="text-right font-mono text-xs text-secondary hidden sm:block"
                            >
                                {Math.max(0, p.games ?? 0)}
                            </div>
                            <!-- Percent Bar -->
                            <div class="flex items-center gap-2 justify-end hidden sm:flex">
                                <span class="font-mono text-xs text-secondary"
                                    >{p.percent_of_squadron.toFixed(1)}%</span
                                >
                                <div
                                    class="w-16 h-1 bg-terminal-panel rounded-full overflow-hidden hidden md:block"
                                >
                                    <div
                                        class="h-full bg-blue-500/50"
                                        style="width: {p.percent_of_squadron}%"
                                    ></div>
                                </div>
                            </div>
                            <!-- Win Rate -->
                            <div
                                class="text-right font-mono text-xs font-bold"
                                style="color: {getWinRateColor(Math.min(100, Math.max(0, p.win_rate ?? 0)))}"
                            >
                                {Math.min(100, Math.max(0, Number(p.win_rate ?? 0))).toFixed(1)}%
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        {:else}
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center"
            >
                <p class="text-secondary font-mono text-sm">
                    No pilot breakdown data available.
                </p>
            </div>
        {/if}

        <!-- Top Performing Lists -->
        <div class="flex items-center justify-between gap-3 mb-4 mt-12">
            <h2
                class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 flex items-baseline gap-2"
            >
                Top Performing Lists
                <span class="text-secondary text-base font-normal">({lists.length})</span>
            </h2>
            <SortBy
                value={listSortKey}
                direction={listSortDir}
                options={[
                    { value: "winrate", label: "Win Rate" },
                    { value: "games", label: "Games" },
                    { value: "popularity", label: "Lists" }
                ]}
                onChange={(v, d) => {
                    listSortKey = v as "winrate" | "games" | "popularity";
                    listSortDir = d;
                }}
            />
        </div>

        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-6"
        >
            {#if lists.length > 0}
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {#each sortedLists.slice(0, 12) as list}
                        {@const safeGames = Math.max(0, list.games ?? 0)}
                        {@const safeWins = Math.max(0, list.wins ?? 0)}
                        {@const wr = safeGames > 0
                            ? (safeWins / safeGames) * 100
                            : 0}
                        <div
                            class="relative bg-terminal-panel border border-border-dark rounded-lg p-4 hover:border-secondary/40 transition-colors flex flex-col gap-4"
                            style="border-left: 3px solid {getFactionColor(list.faction)};"
                        >
                            <!-- Stretched link: clicking anywhere on the card
                                 (outside a pilot-name link) goes to the list page. -->
                            <a
                                href="/list/{encodeURIComponent(list.signature || list.name || '')}"
                                class="absolute inset-0 z-0"
                                aria-label="View list details"
                            ></a>
                            <!-- Header: name + faction -->
                            <div class="flex justify-between items-start gap-4">
                                <h3
                                    class="font-sans font-bold text-primary text-sm line-clamp-2 leading-tight"
                                >
                                    {list.name || "Untitled List"}
                                </h3>
                                <div class="flex items-center gap-2 flex-shrink-0">
                                    <span
                                        class="inline-block w-2.5 h-2.5 rounded-full"
                                        style="background: {getFactionColor(
                                            list.faction,
                                        )}"
                                    ></span>
                                    <span
                                        class="text-xs font-mono text-secondary whitespace-nowrap"
                                        >{getFactionLabel(list.faction)}</span
                                    >
                                </div>
                            </div>

                            <!-- Quick Stats -->
                            <div
                                class="flex flex-wrap gap-2 border-b border-border-dark/50 pb-3"
                            >
                                <span
                                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold"
                                    style="color: {getWinRateColor(wr)};"
                                >
                                    WR {wr.toFixed(1)}%
                                </span>
                                <span
                                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                                >
                                    GAMES {safeGames}
                                </span>
                                <span
                                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                                >
                                    WINS {safeWins}
                                </span>
                                <span
                                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-emerald-400"
                                >
                                    PTS {list.points ?? 0}
                                </span>
                            </div>

                            <!-- Pilot summary -->
                            <div class="flex-1 flex flex-col justify-end">
                                <div
                                    class="text-xs font-mono text-secondary space-y-1.5"
                                >
                                    {#each list.pilots || [] as pilot}
                                        {@const pilotName = xwingData.getPilot(
                                            pilot.id,
                                        )?.name || pilot.name || pilot.id}
                                        <div
                                            class="flex items-center gap-2 truncate relative z-10 pointer-events-auto"
                                        >
                                            <i
                                                class="xwing-miniatures-ship xwing-miniatures-ship-{pilot.ship ||
                                                    ''} text-[10px] opacity-70 flex-shrink-0"
                                            ></i>
                                            <CardHoverLink
                                                xws={pilot.id}
                                                type="pilot"
                                                name={pilotName}
                                                className="text-xs font-mono truncate"
                                            />
                                        </div>
                                    {/each}
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>
            {:else}
                <div
                    class="text-center text-sm font-mono text-secondary py-6"
                >
                    No list data available for this squadron.
                </div>
            {/if}
        </div>
    {/if}
</div>
