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
    import StatIcon from "$lib/components/StatIcon.svelte";
    import ListRowCard from "$lib/components/ListRowCard.svelte";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    let stats = $derived(data.stats);
    let pilots = $derived(data.pilots);
    let lists = $derived(data.lists);

    let isXwa = $derived(filters.dataSource === "xwa");

    // ------------------------------------------------------------------------
    // Top Performing Lists — client-side sort
    // ------------------------------------------------------------------------
    // SortBy in the section header drives this state.
    // `winrate` is computed on demand from `wins / games` (or pre-computed win_rate).
    type ListSortKey = "winrate" | "games";

    let listSortKey = $state<ListSortKey>("winrate");
    let listSortDir = $state<"asc" | "desc">("desc");

    function listSortValue(l: any): number {
        switch (listSortKey) {
            case "winrate": {
                const games = Math.max(0, l.games ?? 0);
                const wins = Math.max(0, l.wins ?? 0);
                // Compute directly so sorting is 100% accurate even if pre-computed win_rate is missing or 0
                if (games > 0) {
                    return (wins / games) * 100;
                }
                if (typeof l.win_rate === "number") return l.win_rate;
                return -1;
            }
            case "games":
                return Math.max(0, l.games ?? 0);
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
    type PilotSortKey = "name" | "cost" | "games" | "winrate" | "percent";

    let pilotSortKey = $state<PilotSortKey>("percent");
    let pilotSortDir = $state<"asc" | "desc">("desc");

    function pilotSortValue(p: any): number | string {
        switch (pilotSortKey) {
            case "name": {
                const pData = xwingData.getPilot(p.pilot_xws);
                return (
                    pData?.name || p.name || p.pilot_xws || ""
                ).toLowerCase();
            }
            case "cost": {
                const md = xwingData.getPilot(p.pilot_xws) as any;
                const c = md?.cost ?? p.cost;
                return typeof c === "number" ? c : 0;
            }
            case "games":
                return Math.max(0, p.games ?? 0);
            case "percent":
                return Math.max(0, Number(p.percent_of_squadron ?? 0));
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

    // ------------------------------------------------------------------------
    // Graceful display names for the top-lists pilot summary.
    // ------------------------------------------------------------------------
    // The enriched list payload references pilots/upgrades by XWS id only
    // (`pilot.xws`, `upgrade.xws`); human-readable names come from the
    // xwing-data manifest. Unmapped ids fall back to the raw XWS id rather
    // than the literal string "unknown" (the squadron page already knows the
    // faction, so "unknown" would be wrong). For the pathological case where
    // the id itself is "unknown" we show a neutral placeholder instead.
    function pilotDisplayName(pilot: any): string {
        const xws = String(pilot?.xws ?? "").trim();
        const name = xwingData.getPilot(xws)?.name || pilot?.name || xws;
        return name.toLowerCase() === "unknown" ? "Unidentified Pilot" : name;
    }

    function upgradeDisplayName(upgrade: any): string {
        const xws = String(upgrade?.xws ?? "").trim();
        const name = xwingData.getUpgrade(xws)?.name || xws;
        return name.toLowerCase() === "unknown" ? "Unidentified Upgrade" : name;
    }

    // The backend names unnamed lists "Unknown List"; render those with the
    // same neutral "Untitled List" fallback used for missing names so the
    // literal word "unknown" never appears on the page.
    function listDisplayName(list: any): string {
        const name = String(list?.name ?? "").trim();
        return !name || name.toLowerCase() === "unknown list"
            ? "Untitled List"
            : name;
    }

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
                    <FactionIcon faction={stats.faction} size="sm" />
                    {getFactionLabel(stats.faction)}
                </p>

                <!-- Key Metrics: squadrons→lists→entries→games→winrate -->
                <div class="flex flex-wrap gap-2 mt-2">
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                    >
                        LISTS {stats.popularity ?? 0}
                    </span>
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                    >
                        ENTRIES {stats.popularity ?? 0}
                    </span>
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                    >
                        GAMES {Math.max(0, stats.games ?? 0)}
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

        <!-- Pilot Composition — B2 final (2 col, large PNG). % is default sort, инициатива removed -->
        <div class="flex flex-wrap items-center gap-2 md:gap-3 mt-12 mb-4">
            <h2
                class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 flex items-baseline gap-2"
            >
                Pilot Composition
                <span class="text-secondary text-base font-normal">({pilots.length})</span>
            </h2>
            {#if pilots.length > 0}
                <div class="ml-auto">
                    <SortBy
                        value={pilotSortKey}
                        direction={pilotSortDir}
                        options={[
                            { value: "percent", label: "% of games" },
                            { value: "games", label: "Games" },
                            { value: "winrate", label: "Win Rate" },
                            { value: "name", label: "Name" },
                            { value: "cost", label: "Points" }
                        ]}
                        onChange={(v, d) => {
                            pilotSortKey = v as PilotSortKey;
                            pilotSortDir = d;
                        }}
                    />
                </div>
            {/if}
        </div>

        {#if pilots.length > 0}
            <!-- B2 final — 2 col, immagini grandi a tutta altezza, % a destra della barra, GAMES/WR in capsula top-right -->
            <div class="grid gap-4 grid-cols-1 md:grid-cols-2">
                {#each sortedPilots as p (p.pilot_xws)}
                    {@const pilotData = xwingData.getPilot(p.pilot_xws) as any}
                    {@const pts = pilotData?.cost ?? p.cost ?? 0}
                    {@const loadout = pilotData?.loadout}
                    {@const hasLoadout = isXwa && loadout !== undefined && loadout !== null}
                    {@const pct = Math.max(0, Math.min(100, Number(p.percent_of_squadron ?? 0)))}
                    {@const wr = Math.min(100, Math.max(0, Number(p.win_rate ?? 0)))}
                    {@const wrC = getWinRateColor(wr)}
                    {@const isLandscape = !!(pilotData?.image && String(pilotData.image).includes('/quickbuilds/'))}
                    {@const _isGeneric = (pilotData?.limited ?? 1) === 0}
                    {@const _gbc = (p as any).games_by_copies as Record<string, number> | undefined}
                    {@const _tg = Math.max(1, Number(stats?.games ?? 0) || 1)}
                    <a href="/pilot/{p.pilot_xws}" class="relative bg-terminal-panel border border-border-dark rounded-lg flex items-stretch overflow-hidden hover:border-primary/30 transition-colors group min-h-[144px] p-2 gap-2">
                        {#if pilotData?.image}
                            <img src={pilotData.image} alt={pilotData.name ?? p.pilot_xws} class="{isLandscape ? 'w-44 sm:w-52 object-contain object-left' : 'w-24 sm:w-28 object-contain object-center'} self-stretch flex-shrink-0 rounded-md drop-shadow-[0_4px_12px_rgba(0,0,0,0.5)]" style="min-height: 100%; background: transparent;" loading="lazy" />
                        {:else}
                            <div class="w-24 sm:w-28 self-stretch flex-shrink-0 flex items-center justify-center rounded-md bg-black/20 border border-white/5"><StatIcon type={p.ship_xws} size="2.4rem" color="rgba(255,255,255,0.15)" isShip={true} /></div>
                        {/if}
                        <div class="min-w-0 flex-1 flex flex-col py-1 gap-2">
                            <!-- Capsule top-right come Cards: spostate più a destra per lasciare spazio alle landscape integrali -->
                            <div class="flex justify-end">
                                <span class="flex items-center gap-1.5">
                                    <span class="px-1.5 py-0.5 bg-[#ffffff08] border border-border-dark rounded text-[10px] font-mono font-bold text-secondary">GAMES {Math.max(0, p.games ?? 0)}</span>
                                    <span class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border" style="background: {wrC}18; color: {wrC}; border-color: {wrC}35;">WR {wr.toFixed(1)}%</span>
                                </span>
                            </div>
                            <div class="min-w-0">
                                <p class="font-sans font-bold text-primary truncate group-hover:text-accent transition-colors text-[15px] leading-tight" title={pilotDisplayName({ xws: p.pilot_xws, name: p.name })}>{pilotDisplayName({ xws: p.pilot_xws, name: p.name })}</p>
                                <p class="font-mono text-secondary truncate flex items-center gap-1 text-xs mt-0.5">{#if p.ship_xws}<i class="xwing-miniatures-ship xwing-miniatures-ship-{p.ship_xws}" style="font-size: 1.05rem; opacity: 0.85;"></i>{/if} {xwingData.getShip(p.ship_xws)?.name ?? p.ship_xws}</p>
                                <div class="flex flex-wrap gap-1.5 mt-2">
                                    <span class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded text-[11px] font-mono font-bold">PTS {pts}</span>
                                    {#if hasLoadout}<span class="px-1.5 py-0.5 bg-violet-500/20 text-violet-400 border border-violet-500/30 rounded text-[11px] font-mono font-bold">LV {loadout}</span>{/if}
                                </div>
                            </div>
                            <div class="mt-auto flex items-center gap-2 pt-2">
                                <div class="flex-1 h-2 bg-black/40 rounded-full overflow-hidden border border-white/5 flex" title={_isGeneric && _gbc ? `present in ${Math.max(0, p.games ?? 0)} games of this squadron — single: ${((_gbc["1"]??0)/_tg*100).toFixed(1)}% · double: ${((_gbc["2"]??0)/_tg*100).toFixed(1)}%` : `present in ${Math.max(0, p.games ?? 0)} games of this squadron`}>
                                    {#if _isGeneric && _gbc && ((_gbc["2"] ?? 0) > 0 || (_gbc["3+"] ?? 0) > 0)}
                                        <span class="h-full bg-sky-400" style="width: {Math.max(0, Math.min(100, (_gbc["1"] ?? 0)/_tg*100))}%"></span>
                                        <span class="h-full bg-amber-400" style="width: {Math.max(0, Math.min(100, (_gbc["2"] ?? 0)/_tg*100))}%"></span>
                                        {#if (_gbc["3+"] ?? 0) > 0}<span class="h-full bg-violet-400" style="width: {Math.max(0, Math.min(100, (_gbc["3+"] ?? 0)/_tg*100))}%"></span>{/if}
                                    {:else}
                                        <span class="h-full bg-sky-400 rounded-full" style="width: {pct >= 0.1 ? Math.max(2, Math.min(100, pct)) : 0}%"></span>
                                    {/if}
                                </div>
                                <span class="font-mono text-sm font-bold text-primary tabular-nums shrink-0" title={`present in ${Math.max(0, p.games ?? 0)} games of this squadron`}>{pct.toFixed(1)}% <span class="font-normal text-secondary/80 text-xs">of games</span>{#if _isGeneric && _gbc && ((_gbc["2"] ?? 0) > 0 || (_gbc["3+"] ?? 0) > 0)}<span class="ml-1 inline-flex items-center gap-1 text-[10px] font-normal"><span class="inline-flex items-center gap-1"><span class="w-2 h-2 rounded-sm bg-sky-400 inline-block"></span>1× {((_gbc["1"]??0)/_tg*100).toFixed(1)}%</span><span class="inline-flex items-center gap-1"><span class="w-2 h-2 rounded-sm bg-amber-400 inline-block ml-1"></span>2× {((_gbc["2"]??0)/_tg*100).toFixed(1)}%</span>{#if (_gbc["3+"] ?? 0) > 0}<span class="inline-flex items-center gap-1"><span class="w-2 h-2 rounded-sm bg-violet-400 inline-block ml-1"></span>3+ {((_gbc["3+"]??0)/_tg*100).toFixed(1)}%</span>{/if}</span>{/if}</span>
                            </div>
                        </div>
                    </a>
                {/each}
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
                    { value: "games", label: "Games" }
                ]}
                onChange={(v, d) => {
                    listSortKey = v as ListSortKey;
                    listSortDir = d;
                }}
            />
        </div>

        {#if lists.length > 0}
            <!-- 2 per row on desktop like ship detail on very large monitors — ListRowCard is the shared component -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {#each sortedLists.slice(0, 12) as list (list.signature || list.name)}
                    <ListRowCard {list} />
                {/each}
            </div>
        {:else}
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg py-10 px-6 text-center"
            >
                <p class="text-sm font-mono text-secondary">No list data available for this squadron.</p>
            </div>
        {/if}
    {/if}
</div>
