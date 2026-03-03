<script lang="ts">
    import { browser } from "$app/environment";

    let { data } = $props();
    let info = $derived(data.info);
    let upgrades = $derived(data.upgrades);
    let chart = $derived(data.chart);
    let configurations = $derived(data.configurations);

    function getFactionColor(xws: string): string {
        const colors: Record<string, string> = {
            rebelalliance: "#FF3333", galacticempire: "#2979FF",
            scumandvillainy: "#006400", resistance: "#FF8C00",
            firstorder: "#800020", galacticrepublic: "#E6D690",
            separatistalliance: "#607D8B", unknown: "#666666",
        };
        const normalized = (xws || "").toLowerCase().replace(/[\s-]/g, "");
        return colors[normalized] || colors.unknown;
    }

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
    <a href="/cards" class="inline-flex items-center gap-2 text-secondary hover:text-primary transition-colors text-sm font-mono mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        BACK TO CARDS
    </a>

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
                <div class="flex items-center gap-3 flex-wrap">
                    <h1 class="text-3xl font-sans font-bold text-primary">{info?.name || data.pilotXws}</h1>
                    <span class="px-2 py-0.5 text-xs font-mono font-bold rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">PILOT</span>
                    {#if info?.faction}
                        <i
                            class="xwing-miniatures-font xwing-miniatures-font-{info.faction === 'Rebel Alliance' ? 'rebel' : info.faction === 'Galactic Empire' ? 'empire' : info.faction === 'Scum and Villainy' ? 'scum' : info.faction === 'Resistance' ? 'rebel' : info.faction === 'First Order' ? 'firstorder' : info.faction === 'Galactic Republic' ? 'republic' : 'separatists'}"
                            style="color: {getFactionColor(info.faction_xws || '')}; font-size: 1.4rem;"
                        ></i>
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
                <div class="flex items-center gap-2 mt-3 flex-wrap">
                    {#if info?.cost != null}
                        <span class="px-2 py-0.5 text-xs font-mono rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">{info.cost} PTS</span>
                    {/if}
                    {#if info?.loadout != null && info.loadout > 0}
                        <span class="px-2 py-0.5 text-xs font-mono rounded bg-purple-500/20 text-purple-400 border border-purple-500/30">{info.loadout} LV</span>
                    {/if}
                    {#if info?.initiative != null}
                        <span class="px-2 py-0.5 text-xs font-mono rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">I{info.initiative}</span>
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
            <h2 class="text-xl font-sans font-bold text-primary mb-4 uppercase tracking-wider">
                Top Configurations
                <span class="text-secondary text-sm font-normal ml-2">({data.configTotal} unique combos)</span>
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {#each configurations as config, i}
                    <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] hover:border-primary/30 transition-all">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-xs font-mono text-secondary">#{i + 1}</span>
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-0.5 text-xs font-mono rounded bg-white/5 text-secondary">{config.count} USED</span>
                                <span
                                    class="px-2 py-0.5 text-xs font-mono rounded"
                                    style="background: {wrColor(config.win_rate)}15; color: {wrColor(config.win_rate)};"
                                >{config.win_rate}% WR</span>
                            </div>
                        </div>
                        <div class="flex flex-wrap gap-1.5">
                            {#each config.upgrades as upg}
                                <span class="px-2 py-1 text-xs font-mono rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20" title={upg.type}>
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
        <h2 class="text-xl font-sans font-bold text-primary mb-4 uppercase tracking-wider">
            Top Compatible Upgrades
            <span class="text-secondary text-sm font-normal ml-2">({data.upgrades_total} total)</span>
        </h2>

        {#if upgrades && upgrades.length > 0}
            <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
                {#each upgrades as u}
                    <div class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] hover:scale-[1.02] hover:border-primary/30 transition-all group">
                        {#if u.image}
                            <img src={u.image} alt={u.name} class="w-full h-auto object-contain max-h-[220px] p-2" />
                        {:else}
                            <div class="w-full h-[150px] bg-white/5 flex items-center justify-center">
                                <span class="text-secondary font-mono text-xs">NO IMAGE</span>
                            </div>
                        {/if}
                        <div class="p-3 text-center">
                            <p class="text-sm font-sans font-bold text-primary">{u.name}</p>
                            <p class="text-xs font-mono text-cyan-400 mb-2">{u.type || ''}</p>
                            <div class="flex items-center justify-center gap-1.5 flex-wrap">
                                <span class="px-1.5 py-0.5 text-[10px] font-mono rounded bg-white/5 text-secondary">{u.count || 0} USED</span>
                                {#if u.win_rate != null && u.win_rate !== 'NA'}
                                    <span
                                        class="px-1.5 py-0.5 text-[10px] font-mono rounded"
                                        style="background: {wrColor(parseFloat(u.win_rate))}15; color: {wrColor(parseFloat(u.win_rate))};"
                                    >{parseFloat(u.win_rate).toFixed(0)}% WR</span>
                                {/if}
                                {#if u.cost != null}
                                    <span class="px-1.5 py-0.5 text-[10px] font-mono rounded bg-emerald-500/10 text-emerald-400">{u.cost} PTS</span>
                                {/if}
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        {:else}
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center">
                <p class="text-secondary font-mono text-sm">No upgrade data available for this pilot.</p>
            </div>
        {/if}
    </section>
</div>
