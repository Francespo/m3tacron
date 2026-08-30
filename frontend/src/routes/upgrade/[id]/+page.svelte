<script lang="ts">
    import { browser } from "$app/environment";
    import { goto } from "$app/navigation";
    import BackLink from "$lib/components/BackLink.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { getWinRateColor, getFactionColor } from "$lib/data/factions";
    import { getSlotIcon } from "$lib/data/slots";
    import SortBy from "$lib/components/SortBy.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";
    import StatIcon from "$lib/components/StatIcon.svelte";
    import LocalFilterBar from "$lib/components/LocalFilterBar.svelte";
    import DebouncedTextInput from "$lib/components/DebouncedTextInput.svelte";
    import { page as pageState } from "$app/state";

    let { data }: { data: any } = $props();

    function getDefaultFormats(ds: "xwa" | "legacy", includeEpic: boolean): string[] {
        if (ds === "xwa") return includeEpic ? ["xwa", "xwa_epic"] : ["xwa"];
        return includeEpic
            ? ["legacy_x2po", "legacy_xlc", "ffg", "legacy_pandorum", "legacy_epic"]
            : ["legacy_x2po", "legacy_xlc", "ffg", "legacy_pandorum"];
    }

    let initialized = $state(false);
    $effect(() => {
        if (initialized) return;
        if (data.ds === "legacy" || data.ds === "xwa") filters.dataSource = data.ds;
        if (data.hasEpicParam) filters.includeEpic = !!data.includeEpic;
        initialized = true;
    });
    $effect(() => {
        if (!initialized) return;
        const keep = browser ? new URLSearchParams(window.location.search) : new URLSearchParams();
        const params = new URLSearchParams();
        params.set("data_source", filters.dataSource);
        if (filters.includeEpic) params.set("epic", "true");
        for (const f of getDefaultFormats(filters.dataSource, filters.includeEpic)) params.append("formats", f);
        for (const k of ["style", "upilot_search", "uship_search"]) {
            const v = keep.get(k);
            if (v !== null && v !== "") params.set(k, v);
        }
        goto(`?${params.toString()}`, { keepFocus: true, noScroll: true, replaceState: true });
    });

    const uData = $derived(xwingData.getUpgrade(data.upgradeXws));
    const info = $derived(data.info);
    const chart = $derived(data.chart ?? []);
    const pilots = $derived(data.pilots ?? []);
    const ships = $derived(data.ships ?? []);
    const stats = $derived(data.stats);

    // Resolve display fields: prefer xwingData manifest, fall back to backend info/stats
    const name = $derived(uData?.name || info?.name || stats?.name || data.upgradeXws);
    const image = $derived(uData?.sides?.[0]?.image || info?.image || info?.sides?.[0]?.image || "");
    const slotXws = $derived((uData?.sides?.[0]?.slots?.[0] || info?.sides?.[0]?.slots?.[0] || "").toLowerCase());
    const slotIconChar = $derived(getSlotIcon(slotXws));
    const slotLabel = $derived(slotXws ? slotXws.toUpperCase() : (uData ? "UPGRADE" : "UPGRADE"));
    const title = $derived(uData?.sides?.[0]?.title || info?.sides?.[0]?.title || name);
    const cost = $derived(uData?.cost?.value ?? info?.cost?.value ?? stats?.cost ?? 0);
    const limited = $derived(uData?.limited ?? info?.limited ?? stats?.limited ?? 0);

    const games = $derived(Math.max(0, Number(stats?.games_count ?? stats?.games ?? 0)));
    const wins = $derived(Math.max(0, Number(stats?.wins ?? 0)));
    const listsCount = $derived(Math.max(0, Number(stats?.list_count ?? stats?.lists ?? 0)));
    const differentListsCount = $derived(Math.max(0, Number(stats?.different_lists_count ?? stats?.different_list_count ?? 0)));
    const wrPct = $derived(games > 0 ? (wins / games) * 100 : 0);
    const wrColor = $derived(getWinRateColor(wrPct));
    const wrDisplay = $derived(games > 0 ? `${wrPct.toFixed(1)}%` : "NA");

    function wrColorFn(wr: number): string {
        if (wr >= 55) return "#22c55e";
        if (wr >= 50) return "#84cc16";
        if (wr >= 45) return "#eab308";
        return "#ef4444";
    }

    // Client-side sort for pilots/ships sections
    type SortKey = "lists" | "games" | "winrate";
    let pilotSortKey = $state<SortKey>("lists");
    let pilotSortDir = $state<"asc" | "desc">("desc");
    let shipSortKey = $state<SortKey>("lists");
    let shipSortDir = $state<"asc" | "desc">("desc");

    const PAGE_SIZE = 12;
    let pilotPage = $state(0);
    let shipPage = $state(0);

    function sortValue(row: any, key: SortKey): number {
        if (key === "winrate") return Math.max(0, Number(row.win_rate ?? row.winRate ?? 0));
        if (key === "games") return Math.max(0, Number(row.games ?? row.games_count ?? 0));
        return Math.max(0, Number(row.list_count ?? row.lists ?? 0));
    }
    let filteredPilotsSource = $derived(pilots as any[]);
    let filteredShipsSource = $derived(ships as any[]);

    let sortedPilots = $derived.by(() => {
        const dir = pilotSortDir === "asc" ? 1 : -1;
        return [...filteredPilotsSource].sort((a: any, b: any) => {
            const d = sortValue(a, pilotSortKey) - sortValue(b, pilotSortKey);
            if (d !== 0) return d * dir;
            return (b.list_count ?? 0) - (a.list_count ?? 0);
        });
    });

    let sortedShips = $derived.by(() => {
        const dir = shipSortDir === "asc" ? 1 : -1;
        return [...filteredShipsSource].sort((a: any, b: any) => {
            const d = sortValue(a, shipSortKey) - sortValue(b, shipSortKey);
            if (d !== 0) return d * dir;
            return (b.list_count ?? 0) - (a.list_count ?? 0);
        });
    });

    let pilotTotalPages = $derived(Math.max(1, Math.ceil(sortedPilots.length / PAGE_SIZE)));
    let pilotItems = $derived(sortedPilots.slice(pilotPage * PAGE_SIZE, (pilotPage + 1) * PAGE_SIZE));
    let shipTotalPages = $derived(Math.max(1, Math.ceil(sortedShips.length / PAGE_SIZE)));
    let shipItems = $derived(sortedShips.slice(shipPage * PAGE_SIZE, (shipPage + 1) * PAGE_SIZE));
    $effect(() => { void sortedPilots; pilotPage = 0; });
    $effect(() => { void sortedShips; shipPage = 0; });

    function chartAction(node: HTMLCanvasElement, config: any) {
        let chartInstance: any;
        if (browser) {
            import("chart.js/auto").then((m) => {
                const ChartJS = m.default;
                ChartJS.defaults.color = "#AAAAAA";
                chartInstance = new ChartJS(node, config);
            });
        }
        return {
            update(newConfig: any) {
                if (chartInstance) {
                    chartInstance.destroy();
                    import("chart.js/auto").then((m) => {
                        const ChartJS = m.default;
                        chartInstance = new ChartJS(node, newConfig);
                    });
                }
            },
            destroy() { if (chartInstance) chartInstance.destroy(); },
        };
    }

    let chartConfig = $derived(
        chart && chart.length > 0
            ? {
                  type: "line" as const,
                  data: {
                      labels: chart.map((d: any) => d.date),
                      datasets: [
                          {
                              label: name || data.upgradeXws,
                              data: chart.map((d: any) => d[data.upgradeXws] ?? d[data.chartSeries?.[0]] ?? 0),
                              borderColor: "#00E0FF",
                              backgroundColor: "rgba(0,224,255,0.1)",
                              fill: true,
                              tension: 0.3,
                              pointRadius: 3,
                          },
                      ],
                  },
                  options: {
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                          legend: { display: false },
                          tooltip: {
                              backgroundColor: "#0A0A0A",
                              borderColor: "#333",
                              borderWidth: 1,
                          },
                      },
                      scales: {
                          x: {
                              grid: { color: "#222" },
                              ticks: { font: { size: 10 }, maxRotation: 45 },
                          },
                          y: {
                              grid: { color: "#222" },
                              beginAtZero: true,
                          },
                      },
                  },
              }
            : null,
    );
</script>

<svelte:head>
    <title>{name} — Upgrade Detail | M3taCron</title>
    <meta name="description" content="Detailed statistics for the {name} upgrade in X-Wing Miniatures." />
</svelte:head>

<div class="min-h-screen p-6 md:p-8 font-sans">
    <div class="mb-6">
        <BackLink href="/cards?tab=upgrades" ariaLabel="Back to Cards" />
    </div>

    <!-- Header: upgrade image (horizontal) on the left, chart on the right — bare PNG, no outer container (mirrors pilot header) -->
    <div class="flex flex-col lg:flex-row gap-8 mb-10">
        <!-- Upgrade Image — bare PNG, same scale as pilot card (280×~392 → 392×280 horizontal) -->
        <div class="flex-shrink-0 flex items-center justify-center" style="width: 392px; max-width: 100%;">
            {#if image}
                <img src={image} alt={name} class="max-w-full h-auto object-contain drop-shadow-[0_4px_16px_rgba(0,0,0,0.45)]" style="max-height: 280px;" loading="eager" />
            {:else}
                <div class="w-full h-[240px] flex flex-col items-center justify-center gap-2">
                    <StatIcon type={slotXws || "upgrade"} size="3.5rem" color="rgba(255,255,255,0.15)" />
                    <span class="text-secondary font-mono text-xs">NO IMAGE</span>
                </div>
            {/if}
        </div>

        <!-- Upgrade Info + Chart -->
        <div class="flex-grow flex flex-col gap-6 min-w-0">
            <div>
                <div class="flex items-center gap-3 flex-wrap min-w-0">
                    <h1 class="text-3xl font-sans font-bold text-primary">{name}</h1>
                    <span class="px-2 py-0.5 text-xs font-mono font-bold rounded-md bg-blue-500/20 text-blue-400 border border-blue-500/30">UPGRADE</span>
                    {#if slotXws}
                        <span class="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[11px] font-mono not-italic text-secondary uppercase tracking-wider" title={slotLabel}>
                            {#if slotIconChar}<i class="font-xwing text-base text-primary not-italic" style="line-height:1; font-style: normal;">{slotIconChar}</i>{/if}
                            {slotLabel}
                        </span>
                    {/if}
                    {#if limited > 0}
                        <span class="px-2 py-0.5 text-xs font-mono font-bold rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30">LIMITED × {limited}</span>
                    {/if}
                </div>
                {#if title && title !== name}
                    <p class="text-secondary font-mono text-sm mt-1">{title}</p>
                {/if}
                <div class="flex items-center gap-2 mt-3 flex-wrap">
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">LISTS {listsCount}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">ENTRIES {Math.max(0, Number((stats as any)?.entries_count ?? listsCount))}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">GAMES {games}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold" style="color: {wrColor};">WR {wrDisplay}</span>
                    <span class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-md text-[10px] font-mono font-bold">PTS {cost}</span>
                </div>
            </div>

            <!-- Games Played Over Time Chart -->
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <h2 class="text-sm font-sans font-bold text-primary uppercase tracking-wider mb-3">Games Played Over Time</h2>
                {#if chartConfig}
                    <div class="h-[220px]">
                        <canvas use:chartAction={chartConfig}></canvas>
                    </div>
                {:else}
                    <p class="text-secondary font-mono text-xs py-8 text-center">No game data available for chart.</p>
                {/if}
            </div>
        </div>
    </div>

    <!-- Pilots Using This Upgrade -->
    <section class="mb-10">
        <div class="flex items-center justify-between gap-3 mb-4 flex-wrap">
            <h2 class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2">Pilots Using This Upgrade</h2>
            <SortBy
                value={pilotSortKey}
                direction={pilotSortDir}
                options={[
                    { value: "lists", label: "Lists" },
                    { value: "games", label: "Games" },
                    { value: "winrate", label: "Win Rate" },
                ]}
                onChange={(v, d) => { pilotSortKey = v as SortKey; pilotSortDir = d; }}
            />
        </div>
                {#if pilotItems.length > 0}
            <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
                {#each pilotItems as p (p.xws)}
                    {@const pWr = Math.max(0, Number(p.win_rate ?? 0))}
                    {@const pGames = Math.max(0, Number(p.games ?? 0))}
                    {@const pLists = Math.max(0, Number(p.list_count ?? 0))}
                    {@const isLandscape = !!p.image && p.image.includes('/quickbuilds/')}
                    <a href="/pilot/{p.xws}" class="bg-terminal-panel border border-border-dark rounded-lg p-3 flex gap-3 hover:border-primary/30 transition-colors group {isLandscape ? 'items-center' : ''}">
                        {#if p.image}
                            <img src={p.image} alt={p.name} class="{isLandscape ? 'w-[6.5rem] h-[3.8rem] object-contain' : 'w-14 h-[4.2rem] object-contain'} drop-shadow-[0_2px_8px_rgba(0,0,0,0.45)] flex-shrink-0 rounded-sm" loading="lazy" />
                        {:else}
                            <div class="{isLandscape ? 'w-[6.5rem] h-[3.8rem]' : 'w-14 h-[4.2rem]'} flex-shrink-0 flex items-center justify-center rounded-sm bg-black/20 border border-white/5"><StatIcon type={p.ship_xws || ""} size="1.8rem" color="rgba(255,255,255,0.15)" isShip={true} /></div>
                        {/if}
                        <div class="min-w-0 flex-1">
                            <p class="text-sm font-sans font-bold text-primary truncate group-hover:text-accent transition-colors" title={p.name}>{p.name}</p>
                            <p class="text-[11px] font-mono text-secondary truncate flex items-center gap-1">
                                {#if p.ship_xws}<i class="xwing-miniatures-ship xwing-miniatures-ship-{p.ship_xws}" style="color: {getFactionColor(p.faction_xws || '')}; font-size: 1rem;"></i>{/if}
                                {p.ship}
                            </p>
                            <div class="flex flex-wrap gap-1 mt-2">
                                <span class="px-1 py-0.5 bg-[#ffffff05] border border-border-dark rounded text-[10px] font-mono font-bold text-secondary">LISTS {pLists}</span>
                                <span class="px-1 py-0.5 bg-[#ffffff05] border border-border-dark rounded text-[10px] font-mono font-bold text-secondary">GAMES {pGames}</span>
                                <span class="px-1 py-0.5 rounded text-[10px] font-mono font-bold" style="background: {wrColorFn(pWr)}15; color: {wrColorFn(pWr)};">WR {pWr.toFixed(1)}%</span>
                            </div>
                        </div>
                        {#if p.faction_xws}<FactionIcon faction={p.faction_xws} size="sm" />{/if}
                    </a>
                {/each}
            </div>
            {#if pilotTotalPages > 1}
                {@const pilotRangeStart = pilotPage * PAGE_SIZE + 1}
                {@const pilotRangeEnd = Math.min((pilotPage + 1) * PAGE_SIZE, sortedPilots.length)}
                <div class="flex items-center justify-center gap-2 mt-6">
                    <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {pilotPage === 0 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={pilotPage === 0} onclick={() => pilotPage = Math.max(0, pilotPage - 1)}>← Prev</button>
                    <span class="text-xs font-mono text-secondary">Showing {pilotRangeStart}–{pilotRangeEnd} of {sortedPilots.length} · Page {pilotPage + 1}/{pilotTotalPages}</span>
                    <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {pilotPage >= pilotTotalPages - 1 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={pilotPage >= pilotTotalPages - 1} onclick={() => pilotPage = Math.min(pilotTotalPages - 1, pilotPage + 1)}>Next →</button>
                </div>
            {/if}
        {:else}
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center">
                <p class="text-secondary font-mono text-sm">No pilot data available for this upgrade.</p>
                <p class="text-secondary font-mono text-xs mt-2 opacity-70">Try adjusting the format filters or check back after more tournaments are imported.</p>
            </div>
        {/if}
    </section>

    <!-- Ships Using This Upgrade -->
    <section>
        <div class="flex items-center justify-between gap-3 mb-4 flex-wrap">
            <h2 class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2">Ships Using This Upgrade</h2>
            <SortBy
                value={shipSortKey}
                direction={shipSortDir}
                options={[
                    { value: "lists", label: "Lists" },
                    { value: "games", label: "Games" },
                    { value: "winrate", label: "Win Rate" },
                ]}
                onChange={(v, d) => { shipSortKey = v as SortKey; shipSortDir = d; }}
            />
        </div>
        {#if shipItems.length > 0}
            <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
                {#each shipItems as s (s.xws)}
                    {@const sWr = Math.max(0, Number(s.win_rate ?? 0))}
                    {@const sGames = Math.max(0, Number(s.games ?? 0))}
                    {@const sLists = Math.max(0, Number(s.list_count ?? 0))}
                    <a href="/ship/{s.xws}" class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex items-center gap-3 hover:border-primary/30 transition-colors group">
                        <div class="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0">
                            <StatIcon type={s.xws} size="1.4rem" color="white" isShip={true} />
                        </div>
                        <div class="min-w-0 flex-1">
                            <p class="text-sm font-sans font-bold text-primary truncate group-hover:text-accent transition-colors">{s.name}</p>
                            <div class="flex flex-wrap gap-1 mt-1">
                                <span class="px-1 py-0.5 bg-[#ffffff05] border border-border-dark rounded text-[10px] font-mono font-bold text-secondary">LISTS {sLists}</span>
                                <span class="px-1 py-0.5 bg-[#ffffff05] border border-border-dark rounded text-[10px] font-mono font-bold text-secondary">GAMES {sGames}</span>
                                <span class="px-1 py-0.5 rounded text-[10px] font-mono font-bold" style="background: {wrColorFn(sWr)}15; color: {wrColorFn(sWr)};">WR {sWr.toFixed(1)}%</span>
                            </div>
                        </div>
                        {#if s.faction_xws}<FactionIcon faction={s.faction_xws} size="sm" />{/if}
                    </a>
                {/each}
            </div>
            {#if shipTotalPages > 1}
                {@const shipRangeStart = shipPage * PAGE_SIZE + 1}
                {@const shipRangeEnd = Math.min((shipPage + 1) * PAGE_SIZE, sortedShips.length)}
                <div class="flex items-center justify-center gap-2 mt-6">
                    <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {shipPage === 0 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={shipPage === 0} onclick={() => shipPage = Math.max(0, shipPage - 1)}>← Prev</button>
                    <span class="text-xs font-mono text-secondary">Showing {shipRangeStart}–{shipRangeEnd} of {sortedShips.length} · Page {shipPage + 1}/{shipTotalPages}</span>
                    <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {shipPage >= shipTotalPages - 1 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={shipPage >= shipTotalPages - 1} onclick={() => shipPage = Math.min(shipTotalPages - 1, shipPage + 1)}>Next →</button>
                </div>
            {/if}
        {:else}
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center">
                <p class="text-secondary font-mono text-sm">No ship data available for this upgrade.</p>
                <p class="text-secondary font-mono text-xs mt-2 opacity-70">This upgrade hasn't appeared on any tracked ship yet for the current filters.</p>
            </div>
        {/if}
    </section>
</div>
