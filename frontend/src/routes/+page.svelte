<script lang="ts">
    import { browser } from "$app/environment";
    import { filters } from "$lib/stores/filters.svelte";
    import ContentSourceToggle from "$lib/components/ContentSourceToggle.svelte";

    let meta = $state<any>(null);
    let loading = $state(true);
    let error = $state(false);
    let errorMsg = $state("");

    $effect(() => {
        if (!browser) return;
        const source = filters.dataSource;
        let isCancelled = false;

        loading = true;
        error = false;
        errorMsg = "";

        const targetUrl = `/api/meta-snapshot?data_source=${source}`;
        fetch(targetUrl)
            .then(async (res) => {
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(
                        `HTTP error! status: ${res.status}, Details: ${errData.error || "unknown"}`,
                    );
                }
                return res.json();
            })
            .then((data) => {
                if (!isCancelled) {
                    meta = data;
                    loading = false;
                }
            })
            .catch((err) => {
                console.error("Dashboard Fetch Error:", err);
                if (!isCancelled) {
                    error = true;
                    errorMsg = `URL: ${targetUrl} | Error: ${err.message || String(err)}`;
                    loading = false;
                }
            });

        return () => {
            isCancelled = true;
        };
    });

    function getFactionColor(xws: string) {
        const colors: Record<string, string> = {
            rebelalliance: "#FF3333",
            galacticempire: "#2979FF",
            scumandvillainy: "#006400",
            resistance: "#FF8C00",
            firstorder: "#800020",
            galacticrepublic: "#E6D690",
            separatistalliance: "#607D8B",
            unknown: "#666666",
        };
        return colors[xws] || colors.unknown;
    }

    function getFactionIconClass(xws: string) {
        const icons: Record<string, string> = {
            rebelalliance: "xwing-miniatures-font-rebel",
            galacticempire: "xwing-miniatures-font-empire",
            scumandvillainy: "xwing-miniatures-font-scum",
            resistance: "xwing-miniatures-font-rebel",
            firstorder: "xwing-miniatures-font-firstorder",
            galacticrepublic: "xwing-miniatures-font-republic",
            separatistalliance: "xwing-miniatures-font-separatists",
            unknown: "",
        };
        return icons[xws] || "";
    }

    function getShipIconClass(xws: string) {
        if (!xws) return "";
        return "xwing-miniatures-ship-" + xws.replace(/[^a-z0-9]/g, "");
    }

    function getUpgradeIconClass(type: string) {
        if (!type) return "";
        return (
            "xwing-miniatures-font-" +
            type.toLowerCase().replace(/[^a-z0-9]/g, "")
        );
    }

    function chartAction(node: HTMLCanvasElement, config: any) {
        let chart: any;

        if (browser) {
            import("chart.js/auto").then((m) => {
                const ChartJS = m.default;
                ChartJS.defaults.color = "#AAAAAA";
                chart = new ChartJS(node, config);
            });
        }

        return {
            update(newConfig: any) {
                if (chart) {
                    chart.destroy();
                    import("chart.js/auto").then((m) => {
                        const ChartJS = m.default;
                        chart = new ChartJS(node, newConfig);
                    });
                }
            },
            destroy() {
                if (chart) chart.destroy();
            },
        };
    }

    let barData = $derived(
        meta?.factions
            ? {
                  labels: meta.factions.map((d: any) => d.icon_char || ""),
                  datasets: [
                      {
                          label: "Win Rate (%)",
                          data: meta.factions.map((d: any) =>
                              parseFloat(d.win_rate),
                          ),
                          backgroundColor: meta.factions.map((d: any) =>
                              getFactionColor(d.xws),
                          ),
                          borderRadius: {
                              topLeft: 4,
                              topRight: 4,
                              bottomLeft: 0,
                              bottomRight: 0,
                          },
                      },
                  ],
              }
            : null,
    );

    const barOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: "#0A0A0A",
                borderColor: "#333333",
                borderWidth: 1,
                titleFont: { family: '"Inter", sans-serif' },
                bodyFont: { family: '"Inter", sans-serif' },
            },
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: {
                    font: { family: "XWing", size: 20 },
                    color: "#AAAAAA",
                },
            },
            y: {
                grid: { color: "#222", strokeDash: [3, 3] },
                ticks: {
                    font: { family: '"JetBrains Mono", monospace', size: 10 },
                },
            },
        },
    };

    let pieData = $derived(
        meta?.faction_distribution
            ? {
                  labels: meta.faction_distribution.map(
                      (d: any) => d.real_name,
                  ),
                  datasets: [
                      {
                          data: meta.faction_distribution.map(
                              (d: any) => d.games,
                          ),
                          backgroundColor: meta.faction_distribution.map(
                              (d: any) => getFactionColor(d.xws),
                          ),
                          borderWidth: 0,
                      },
                  ],
              }
            : null,
    );

    const pieOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: "#0A0A0A",
                borderColor: "#333333",
                borderWidth: 1,
                titleFont: { family: '"Inter", sans-serif' },
                bodyFont: { family: '"Inter", sans-serif' },
            },
        },
    };
</script>

<div class="min-h-screen p-6 font-sans">
    <header
        class="mb-8 flex flex-col md:flex-row md:items-start justify-between gap-4 w-full"
    >
        <div>
            <h1
                class="text-3xl font-mono uppercase tracking-widest font-bold text-primary"
            >
                M3taCron <span class="text-secondary text-2xl font-light"
                    >Dashboard</span
                >
            </h1>
        </div>
        <div
            class="w-full md:w-64 bg-terminal-panel border border-border-dark p-3 rounded-lg shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
        >
            <ContentSourceToggle />
        </div>
    </header>

    {#if loading || !meta}
        <div
            class="p-6 bg-terminal-panel border border-border-dark shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] rounded-md text-center"
        >
            <p class="text-secondary font-mono animate-pulse">
                {#if error}
                    Failed to fetch data: {errorMsg}
                {:else}
                    Loading or fetching data...
                {/if}
            </p>
        </div>
    {:else}
        <!-- Top Stats Row -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1"
            >
                <div class="flex items-center gap-2">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        class="text-secondary"
                        ><path
                            d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22M18 2H6v7a6 6 0 0 0 12 0V2Z"
                        /></svg
                    >
                    <span
                        class="text-secondary font-mono text-[10px] font-bold uppercase tracking-widest"
                        >Tournaments</span
                    >
                </div>
                <div class="text-4xl font-bold font-sans text-primary">
                    {meta.total_tournaments || 0}
                </div>
            </div>

            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1"
            >
                <div class="flex items-center gap-2">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        class="text-secondary"
                        ><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" /><path
                            d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"
                        /><path d="M4 22h16" /><path
                            d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"
                        /><path
                            d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"
                        /><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" /></svg
                    >
                    <span
                        class="text-secondary font-mono text-[10px] font-bold uppercase tracking-widest"
                        >Players</span
                    >
                </div>
                <div class="text-4xl font-bold font-sans text-primary">
                    {meta.total_players || 0}
                </div>
            </div>

            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1"
            >
                <div class="flex items-center gap-2">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        class="text-secondary"
                        ><path d="M8 2v4" /><path d="M16 2v4" /><rect
                            width="18"
                            height="18"
                            x="3"
                            y="4"
                            rx="2"
                        /><path d="M3 10h18" /></svg
                    >
                    <span
                        class="text-secondary font-mono text-[10px] font-bold uppercase tracking-widest"
                        >Date Range</span
                    >
                </div>
                <div
                    class="text-2xl font-bold font-sans text-primary leading-tight mt-1"
                >
                    {meta.date_range || "Unknown"}
                </div>
            </div>

            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1"
            >
                <div class="flex items-center gap-2">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        class="text-secondary"
                        ><path
                            d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"
                        /><path d="M3 3v5h5" /><path
                            d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"
                        /><path d="M16 21v-5h5" /></svg
                    >
                    <span
                        class="text-secondary font-mono text-[10px] font-bold uppercase tracking-widest"
                        >Last Sync</span
                    >
                </div>
                <div
                    class="text-2xl font-bold font-sans text-primary leading-tight mt-1"
                >
                    {meta.last_sync || "Unknown"}
                </div>
            </div>
        </div>

        <!-- Section 1: Factions -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <h2
                    class="text-sm font-mono font-bold uppercase mb-4 text-primary"
                >
                    Faction Performance
                </h2>
                <div class="h-[250px] w-full relative">
                    {#if barData}
                        <canvas
                            use:chartAction={{
                                type: "bar",
                                data: barData,
                                options: barOptions,
                            }}
                        ></canvas>
                    {/if}
                </div>
            </div>

            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <h2
                    class="text-sm font-mono font-bold uppercase mb-4 text-primary"
                >
                    Game Distribution
                </h2>
                <div class="h-[180px] w-full relative mb-4">
                    {#if pieData}
                        <canvas
                            use:chartAction={{
                                type: "pie",
                                data: pieData,
                                options: pieOptions,
                            }}
                        ></canvas>
                    {/if}
                </div>
                <div class="flex flex-wrap justify-center w-full mt-2">
                    {#each meta.faction_distribution || [] as dist}
                        <div
                            class="flex items-center gap-[6px] text-xs font-mono text-secondary mr-3 mb-[6px]"
                        >
                            <i
                                class="xwing-miniatures-font {getFactionIconClass(
                                    dist.xws,
                                )} text-sm"
                            ></i>
                            <span>{dist.percentage}%</span>
                        </div>
                    {/each}
                </div>
            </div>
        </div>

        <!-- Section 2: Leaderboards -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <!-- Top Pilots -->
            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <h2
                    class="text-sm font-mono font-bold uppercase mb-4 text-primary"
                >
                    Top Pilots
                </h2>
                <div class="w-full flex flex-col">
                    {#each (meta.pilots || []).slice(0, 5) as pilot}
                        <div
                            class="py-[12px] border-b border-border-dark flex items-center justify-between w-full last:border-0 relative"
                        >
                            <div
                                class="flex items-center gap-3 overflow-hidden mr-2"
                            >
                                <div
                                    class="w-8 flex justify-center flex-shrink-0"
                                >
                                    <i
                                        class="xwing-miniatures-ship {getShipIconClass(
                                            pilot.ship_xws || pilot.ship_icon,
                                        )} text-secondary text-2xl"
                                    ></i>
                                </div>
                                <div
                                    class="flex flex-col overflow-hidden min-w-0 relative"
                                >
                                    <span
                                        class="text-base font-bold text-primary truncate min-w-0"
                                        title={pilot.name}>{pilot.name}</span
                                    >
                                    <div
                                        class="flex items-center gap-1 min-w-0 mt-0.5"
                                    >
                                        <i
                                            class="xwing-miniatures-font {getFactionIconClass(
                                                (pilot.faction || '')
                                                    .toLowerCase()
                                                    .replace(/[^a-z0-9]/g, ''),
                                            )} text-[11px] text-secondary"
                                        ></i>
                                        <span
                                            class="text-[12px] text-secondary truncate min-w-0 pointer-events-none"
                                            >{pilot.faction || "Unknown"} - {pilot.ship ||
                                                "Unknown Ship"}</span
                                        >
                                    </div>
                                </div>
                            </div>
                            <div
                                class="flex flex-col items-end flex-shrink-0 text-right ml-2 pr-1"
                            >
                                <span
                                    class="text-base font-mono font-bold text-primary shrink-0"
                                    >{pilot.win_rate}% WR</span
                                >
                                <span
                                    class="text-[11px] text-secondary shrink-0"
                                    >{pilot.games} games</span
                                >
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Top Upgrades -->
            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <h2
                    class="text-sm font-mono font-bold uppercase mb-4 text-primary"
                >
                    Top Upgrades
                </h2>
                <div class="w-full flex flex-col">
                    {#each (meta.upgrades || []).slice(0, 6) as upgrade}
                        <div
                            class="py-[12px] border-b border-border-dark flex items-center justify-between w-full last:border-0 relative"
                        >
                            <div
                                class="flex items-center gap-3 overflow-hidden mr-2"
                            >
                                <div
                                    class="w-8 flex justify-center flex-shrink-0"
                                >
                                    <i
                                        class="xwing-miniatures-font {getUpgradeIconClass(
                                            upgrade.type,
                                        )} text-secondary text-2xl"
                                    ></i>
                                </div>
                                <div
                                    class="flex flex-col overflow-hidden min-w-0 relative"
                                >
                                    <span
                                        class="text-base font-bold text-primary truncate min-w-0"
                                        title={upgrade.name}
                                        >{upgrade.name}</span
                                    >
                                    <div
                                        class="flex items-center gap-1 min-w-0 mt-0.5"
                                    >
                                        <span
                                            class="text-[12px] text-secondary truncate min-w-0 pointer-events-none"
                                            >{upgrade.type}</span
                                        >
                                    </div>
                                </div>
                            </div>
                            <div
                                class="flex flex-col items-end flex-shrink-0 text-right ml-2 pr-1"
                            >
                                <span
                                    class="text-base font-mono font-bold text-primary shrink-0"
                                    >{upgrade.win_rate}% WR</span
                                >
                                <span
                                    class="text-[11px] text-secondary shrink-0"
                                    >{upgrade.games} games</span
                                >
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Top Ships -->
            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <h2
                    class="text-sm font-mono font-bold uppercase mb-4 text-primary"
                >
                    Top Ships
                </h2>
                <div class="w-full flex flex-col">
                    {#each (meta.ships || []).slice(0, 5) as ship}
                        <div
                            class="py-[12px] border-b border-border-dark flex items-center justify-between w-full last:border-0 relative"
                        >
                            <div
                                class="flex items-center gap-3 overflow-hidden mr-2"
                            >
                                <div
                                    class="w-8 flex justify-center flex-shrink-0"
                                >
                                    <i
                                        class="xwing-miniatures-ship {getShipIconClass(
                                            ship.ship_xws,
                                        )} text-secondary text-2xl"
                                    ></i>
                                </div>
                                <div
                                    class="flex flex-col overflow-hidden min-w-0 relative"
                                >
                                    <span
                                        class="text-base font-bold text-primary truncate min-w-0"
                                        title={ship.ship_name}
                                        >{ship.ship_name}</span
                                    >
                                    <div
                                        class="flex items-center gap-1 min-w-0 mt-0.5"
                                    >
                                        <i
                                            class="xwing-miniatures-font {getFactionIconClass(
                                                ship.faction_xws,
                                            )} text-[11px] text-secondary"
                                        ></i>
                                        <span
                                            class="text-[12px] text-secondary truncate min-w-0 pointer-events-none"
                                            >{ship.faction}</span
                                        >
                                    </div>
                                </div>
                            </div>
                            <div
                                class="flex flex-col items-end flex-shrink-0 text-right ml-2 pr-1"
                            >
                                <span
                                    class="text-base font-mono font-bold text-primary shrink-0"
                                    >{ship.win_rate}% WR</span
                                >
                                <span
                                    class="text-[11px] text-secondary shrink-0"
                                    >{ship.games} games</span
                                >
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        </div>

        <!-- Section 3: Meta Lists -->
        <div class="w-full">
            <div
                class="bg-terminal-panel border border-border-dark rounded-[6px] p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <h2
                    class="text-sm font-mono font-bold uppercase mb-4 text-primary"
                >
                    Top Meta Lists
                </h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
                    {#each (meta.lists || []).slice(0, 3) as list}
                        <div
                            class="p-4 bg-[rgba(255,255,255,0.01)] border border-border-dark hover:bg-[rgba(255,255,255,0.03)] transition-colors cursor-pointer w-full flex flex-col gap-3 rounded-md"
                        >
                            <div
                                class="flex w-full items-start justify-between border-b border-border-dark pb-3"
                            >
                                <div
                                    class="flex items-center gap-2 overflow-hidden mr-2"
                                >
                                    <i
                                        class="xwing-miniatures-font {getFactionIconClass(
                                            list.faction_key,
                                        )} text-secondary text-2xl font-bold"
                                    ></i>
                                    <span
                                        class="text-base font-bold text-primary truncate"
                                        title={list.name || "Unnamed List"}
                                        >{list.name || "Unnamed List"}</span
                                    >
                                </div>
                                <div
                                    class="flex flex-col items-end flex-shrink-0"
                                >
                                    <span
                                        class="text-base font-mono font-bold text-primary"
                                        >{list.win_rate}% WR</span
                                    >
                                    <span class="text-[11px] text-secondary"
                                        >{list.games} games</span
                                    >
                                </div>
                            </div>

                            <div class="flex flex-col gap-1 w-full flex-grow">
                                {#each list.pilots || [] as pilot}
                                    <div class="flex items-center gap-2">
                                        <i
                                            class="xwing-miniatures-ship {getShipIconClass(
                                                pilot.ship_icon,
                                            )} text-secondary text-base w-6 text-center"
                                        ></i>
                                        <span
                                            class="text-sm text-secondary truncate"
                                            >{pilot.name}</span
                                        >
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    {/if}
</div>
