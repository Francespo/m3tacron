<script lang="ts">
    import { browser } from "$app/environment";
    import { goto } from "$app/navigation";
    import BackLink from "$lib/components/BackLink.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { getFactionColor } from "$lib/data/factions";
    import SortBy from "$lib/components/SortBy.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";

    let { data } = $props();
    import UpgradeCard from "$lib/components/UpgradeCard.svelte";

    let info = $derived(data.info);
    let upgrades = $derived(data.upgrades);
    let chart = $derived(data.chart);
    let configurations = $derived(data.configurations);
    let initialized = $state(false);

    // Client-side sort state for "Top Configurations". The backend
    // returns configs pre-sorted by `count` desc; we re-sort in the
    // browser so the SortBy control can flip between "most-played"
    // (popularity / lists / games, all proxied by `count`), and
    // computed win rate (provided by the backend).
    type ConfigSortKey = "popularity" | "lists" | "games" | "winrate";
    let configSortKey = $state<ConfigSortKey>("popularity");
    let configSortDir = $state<"asc" | "desc">("desc");

    function configSortValue(c: any): number {
        switch (configSortKey) {
            case "winrate":
                return Math.max(0, c.win_rate ?? 0);
            case "games":
            case "lists":
            case "popularity":
            default:
                return Math.max(0, c.count ?? 0);
        }
    }

    let sortedConfigurations = $derived.by(() => {
        const dir = configSortDir === "asc" ? 1 : -1;
        return [...configurations].sort((a, b) => {
            const diff = configSortValue(a) - configSortValue(b);
            if (diff !== 0) return diff * dir;
            // Stable tiebreaker: most-used first, then by name.
            return (b.count ?? 0) - (a.count ?? 0);
        });
    });

    // Client-side sort state for "Top Compatible Upgrades". The
    // backend already returns upgrades sorted by list_count desc; the
    // SortBy control re-sorts by absolute games or by computed win
    // rate without a server round-trip.
    type UpgSortKey = "games" | "winrate";
    let upgSortKey = $state<UpgSortKey>("games");
    let upgSortDir = $state<"asc" | "desc">("desc");

    function upgGames(u: any): number {
        return Math.max(0, u.count ?? 0);
    }
    function upgWinRate(u: any): number {
        const g = upgGames(u);
        const w = Math.max(0, u.wins ?? 0);
        return g > 0 ? (w / g) * 100 : -1;
    }

    let sortedUpgrades = $derived.by(() => {
        const dir = upgSortDir === "asc" ? 1 : -1;
        return [...upgrades].sort((a, b) => {
            let diff: number;
            if (upgSortKey === "winrate") {
                diff = upgWinRate(a) - upgWinRate(b);
            } else {
                diff = upgGames(a) - upgGames(b);
            }
            if (diff !== 0) return diff * dir;
            // Tiebreaker: more games first, then alphabetical by xws.
            const gDiff = upgGames(b) - upgGames(a);
            if (gDiff !== 0) return gDiff;
            return (a.xws || "").localeCompare(b.xws || "");
        });
    });

    function getDefaultFormats(ds: "xwa" | "legacy", includeEpic: boolean): string[] {
        if (ds === "xwa") {
            return includeEpic ? ["xwa", "xwa_epic"] : ["xwa"];
        }
        return includeEpic
            ? ["legacy_x2po", "legacy_xlc", "ffg", "legacy_epic"]
            : ["legacy_x2po", "legacy_xlc", "ffg"];
    }

    $effect(() => {
        if (initialized) return;
        if (data.ds === "legacy" || data.ds === "xwa") {
            filters.dataSource = data.ds;
        }
        filters.includeEpic = !!data.includeEpic;
        initialized = true;
    });

    $effect(() => {
        if (!initialized) return;

        const params = new URLSearchParams();
        params.set("data_source", filters.dataSource);
        if (filters.includeEpic) params.set("include_epic", "true");
        for (const f of getDefaultFormats(filters.dataSource, filters.includeEpic)) {
            params.append("formats", f);
        }

        goto(`?${params.toString()}`, {
            keepFocus: true,
            noScroll: true,
            replaceState: true,
        });
    });

    function wrColor(wr: number): string {
        if (wr >= 55) return "#22c55e";
        if (wr >= 50) return "#84cc16";
        if (wr >= 45) return "#eab308";
        return "#ef4444";
    }

    // Chart.js action for the temporal usage chart
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
                              label: info?.name || data.pilotXws,
                              data: chart.map((d: any) => d[data.pilotXws] || 0),
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
                          x: { grid: { color: "#222" }, ticks: { font: { size: 10 }, maxRotation: 45 } },
                          y: { grid: { color: "#222" }, beginAtZero: true },
                      },
                  },
              }
            : null,
    );
</script>

<svelte:head>
    <title>{info?.name || data.pilotXws} — Pilot Detail | M3taCron</title>
    <meta name="description" content="Detailed statistics for {info?.name || data.pilotXws} pilot in X-Wing Miniatures." />
</svelte:head>

<div class="min-h-screen p-6 md:p-8 font-sans">
    <!-- Back link -->
    <BackLink href="/cards" ariaLabel="Back to Cards" />

    <!-- Header Section -->
    <div class="flex flex-col lg:flex-row gap-8 mb-10">
        <!-- Pilot Image -->
        <div class="flex-shrink-0">
            {#if info?.image}
                <img
                    src={info.image}
                    alt={info.name}
                    class="rounded-xl border border-border-dark max-w-[280px] w-full shadow-lg"
                />
            {:else}
                <div class="w-[280px] h-[380px] bg-terminal-panel border border-border-dark rounded-xl flex items-center justify-center">
                    <span class="text-secondary font-mono text-sm">NO IMAGE</span>
                </div>
            {/if}
        </div>

        <!-- Pilot Info + Chart -->
        <div class="flex-grow flex flex-col gap-6">
            <!-- Name & Badges -->
            <div>
                <div>
                    <div class="flex items-center gap-3 flex-wrap min-w-0">
                        <h1 class="text-3xl font-sans font-bold text-primary">{info?.name || data.pilotXws}</h1>
                        <span class="px-2 py-0.5 text-xs font-mono font-bold rounded-md bg-blue-500/20 text-blue-400 border border-blue-500/30">PILOT</span>
                        {#if info?.faction_xws}
                            <FactionIcon
                                faction={info.faction_xws}
                                size="lg"
                            />
                        {/if}
                    </div>
                    {#if info?.ship}
                        <p class="text-secondary font-mono text-sm mt-1">
                            {#if info.ship_xws}
                                <i class="xwing-miniatures-ship xwing-miniatures-ship-{info.ship_xws}" style="color: {getFactionColor(info.faction_xws || '')}; font-size: 1.2rem;"></i>
                            {/if}
                            {info.ship}
                        </p>
                    {/if}
                    <!-- The right-column ContentSourceToggle card was removed
                         here; the XWA / LEGACY / Epic controls now live in
                         the desktop Sidebar / mobile nav drawer. -->
                </div>
                <div class="flex items-center gap-2 mt-3 flex-wrap">
                    {#if info?.cost != null}
                        <span class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-md text-[10px] font-mono font-bold">PTS {info.cost}</span>
                    {/if}
                    {#if info?.loadout != null && info.loadout > 0}
                        <span class="px-1.5 py-0.5 bg-violet-500/20 text-violet-400 border border-violet-500/30 rounded-md text-[10px] font-mono font-bold">LV {info.loadout}</span>
                    {/if}
                </div>
            </div>

            <!-- Usage Over Time Chart -->
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <h2 class="text-sm font-sans font-bold text-primary mb-3 uppercase tracking-wider">Usage Over Time</h2>
                {#if chartConfig}
                    <div class="h-[220px]">
                        <canvas use:chartAction={chartConfig}></canvas>
                    </div>
                {:else}
                    <p class="text-secondary font-mono text-xs py-8 text-center">No usage data available for chart.</p>
                {/if}
            </div>
        </div>
    </div>

    <!-- Top Configurations Section (NEW) -->
    {#if configurations && configurations.length > 0}
        <section class="mb-10">
            <div class="flex items-center justify-between gap-3 mb-4">
                <h2 class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 flex items-baseline gap-2">
                    <span>Top Configurations</span>
                    <span class="text-secondary text-base font-normal">({data.configTotal} unique combos)</span>
                </h2>
                <SortBy
                    value={configSortKey}
                    direction={configSortDir}
                    options={[
                        { value: "popularity", label: "Popularity" },
                        { value: "lists", label: "Lists" },
                        { value: "games", label: "Games" },
                        { value: "winrate", label: "Win Rate" }
                    ]}
                    onChange={(v, d) => {
                        configSortKey = v as ConfigSortKey;
                        configSortDir = d;
                    }}
                />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {#each sortedConfigurations as config, i (config.upgrades.map((u: any) => u.xws).join("|"))}
                    <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] hover:border-primary/30 transition-all">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-xs font-mono text-secondary">#{i + 1}</span>
                            <div class="flex items-center gap-2">
                                <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-secondary">GAMES {config.count}</span>
                                <span
                                    class="px-1.5 py-0.5 rounded-md text-[10px] font-mono font-bold"
                                    style="background: {wrColor(config.win_rate)}15; color: {wrColor(config.win_rate)};"
                                >WR {config.win_rate}%</span>
                            </div>
                        </div>
                        <div class="flex flex-wrap gap-1.5">
                            {#each config.upgrades as upg}
                                <span class="px-2 py-1 text-xs font-mono rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20" title={upg.type}>
                                    {upg.name}
                                </span>
                            {/each}
                            {#if config.upgrades.length === 0}
                                <span class="text-xs font-mono text-secondary italic">No upgrades</span>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        </section>
    {/if}

    <!-- Top Compatible Upgrades Section -->
    <section>
        <div class="flex items-center justify-between gap-3 mb-4">
            <h2 class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 flex items-baseline gap-2">
                <span>Top Compatible Upgrades</span>
                <span class="text-secondary text-base font-normal">({data.upgrades_total} total)</span>
            </h2>
            <SortBy
                value={upgSortKey}
                direction={upgSortDir}
                options={[
                    { value: "games", label: "Games" },
                    { value: "winrate", label: "Win Rate" }
                ]}
                onChange={(v, d) => {
                    upgSortKey = v as UpgSortKey;
                    upgSortDir = d;
                }}
            />
        </div>

        {#if sortedUpgrades && sortedUpgrades.length > 0}
            <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">                {#each sortedUpgrades as u (u.xws)}
                    <UpgradeCard upgrade={{
                        ...u,
                        slot_xws: u.type_xws || u.type,
                        games: u.count,
                    }} />
                {/each}

            </div>
        {:else}
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center">
                <p class="text-secondary font-mono text-sm">No upgrade data available for this pilot.</p>
            </div>
        {/if}
    </section>
</div>
