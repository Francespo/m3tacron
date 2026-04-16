<script lang="ts">
    import { browser } from "$app/environment";
    import { filters } from "$lib/stores/filters.svelte";
    import ContentSourceToggle from "$lib/components/ContentSourceToggle.svelte";
    import {
        getFactionColor,
        getFactionChar,
        getFactionLabel,
    } from "$lib/data/factions";
    import { xwingData } from "$lib/stores/xwingData.svelte";

    let meta = $state<any>(null);
    let loading = $state(true);
    let error = $state(false);
    let errorMsg = $state("");

    type RankingMode = "popularity" | "winrate";
    const DASHBOARD_RANKING_PREFS_KEY = "m3tacron.dashboard.rankingModes.v1";
    const WR_MIN_GAMES = {
        pilots: 3,
        upgrades: 3,
        ships: 3,
        lists: 3,
    };

    let pilotRankingMode = $state<RankingMode>("popularity");
    let upgradeRankingMode = $state<RankingMode>("popularity");
    let shipRankingMode = $state<RankingMode>("popularity");
    let listRankingMode = $state<RankingMode>("popularity");

    $effect(() => {
        if (!browser) return;

        try {
            const raw = localStorage.getItem(DASHBOARD_RANKING_PREFS_KEY);
            if (!raw) return;

            const saved = JSON.parse(raw) as {
                pilots?: RankingMode;
                upgrades?: RankingMode;
                ships?: RankingMode;
                lists?: RankingMode;
            };

            if (saved.pilots === "popularity" || saved.pilots === "winrate") {
                pilotRankingMode = saved.pilots;
            }
            if (saved.upgrades === "popularity" || saved.upgrades === "winrate") {
                upgradeRankingMode = saved.upgrades;
            }
            if (saved.ships === "popularity" || saved.ships === "winrate") {
                shipRankingMode = saved.ships;
            }
            if (saved.lists === "popularity" || saved.lists === "winrate") {
                listRankingMode = saved.lists;
            }
        } catch (err) {
            console.warn("Failed to read dashboard ranking preferences", err);
        }
    });

    $effect(() => {
        if (!browser) return;

        try {
            localStorage.setItem(
                DASHBOARD_RANKING_PREFS_KEY,
                JSON.stringify({
                    pilots: pilotRankingMode,
                    upgrades: upgradeRankingMode,
                    ships: shipRankingMode,
                    lists: listRankingMode,
                }),
            );
        } catch (err) {
            console.warn("Failed to save dashboard ranking preferences", err);
        }
    });

    $effect(() => {
        if (!browser) return;
        const source = filters.dataSource;
        // Ensure data is loaded
        xwingData.setSource(source as any);

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

    function getShipIconClass(xws: string) {
        if (!xws) return "";
        // If we want accurate icons from manifest, we might need a mapping or just rely on font classes
        return "xwing-miniatures-ship-" + xws.replace(/[^a-z0-9]/g, "");
    }

    function getUpgradeIconClass(type: string) {
        if (!type) return "";
        return (
            "xwing-miniatures-font-" +
            type.toLowerCase().replace(/[^a-z0-9]/g, "")
        );
    }

    function getWinRate(wins: number, games: number): number {
        if (!games) return 0;
        return (wins / games) * 100;
    }

    function sortByRankingMode(
        items: any[],
        rankingMode: RankingMode,
    ): any[] {
        return [...items].sort((a, b) => {
            const gamesA = Number(a.games_count ?? a.games ?? 0);
            const gamesB = Number(b.games_count ?? b.games ?? 0);

            if (rankingMode === "winrate") {
                const wrA = getWinRate(Number(a.wins ?? 0), gamesA);
                const wrB = getWinRate(Number(b.wins ?? 0), gamesB);
                if (wrB !== wrA) return wrB - wrA;
                return gamesB - gamesA;
            }

            if (gamesB !== gamesA) return gamesB - gamesA;
            const wrA = getWinRate(Number(a.wins ?? 0), gamesA);
            const wrB = getWinRate(Number(b.wins ?? 0), gamesB);
            return wrB - wrA;
        });
    }

    function applyWrMinGames(
        items: any[],
        rankingMode: RankingMode,
        minGames: number,
    ): any[] {
        if (rankingMode !== "winrate") return items;
        return items.filter((item) =>
            Number(item?.games_count ?? item?.games ?? 0) >= minGames,
        );
    }

    function getPilotDisplay(pilotXws: string) {
        const pilot = xwingData.getPilot(pilotXws);
        const ship = pilot?.ship ? xwingData.getShip(pilot.ship) : null;
        return {
            pilot,
            ship,
            name: pilot?.name || pilotXws,
            shipName: ship?.name || pilot?.ship || "Unknown Ship",
            faction: pilot?.faction || "unknown",
            shipXws: pilot?.ship || "",
        };
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
                  labels: meta.factions.map((d: any) => getFactionChar(d.xws) || "?"),
                  datasets: [
                      {
                          label: "Win Rate (%)",
                          data: meta.factions.map((d: any) =>
                              d.games_count > 0 ? Number(((d.wins / d.games_count) * 100).toFixed(1)) : 0,
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
                callbacks: {
                    title(tooltipItems: { dataIndex: number; label?: string }[]) {
                        const item = tooltipItems[0];
                        const faction = item ? meta?.factions?.[item.dataIndex] : null;
                        return faction
                            ? getFactionLabel(faction.xws)
                            : item?.label ?? "";
                    },
                },
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
        meta?.factions
            ? {
                  labels: meta.factions.map(
                      (d: any) => getFactionLabel(d.xws),
                  ),
                  datasets: [
                      {
                          data: meta.factions.map(
                              (d: any) => d.games_count,
                          ),
                          backgroundColor: meta.factions.map(
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

    let totalFactionGames = $derived(
        (meta?.factions || []).reduce(
            (acc: number, f: any) => acc + (f?.games_count || 0),
            0,
        ),
    );

    let sortedPilots = $derived(
        sortByRankingMode(
            applyWrMinGames(meta?.pilots || [], pilotRankingMode, WR_MIN_GAMES.pilots),
            pilotRankingMode,
        ),
    );

    let sortedUpgrades = $derived(
        sortByRankingMode(
            applyWrMinGames(meta?.upgrades || [], upgradeRankingMode, WR_MIN_GAMES.upgrades),
            upgradeRankingMode,
        ),
    );

    let sortedShips = $derived(
        sortByRankingMode(
            applyWrMinGames(meta?.ships || [], shipRankingMode, WR_MIN_GAMES.ships),
            shipRankingMode,
        ),
    );

    let sortedLists = $derived(
        sortByRankingMode(
            applyWrMinGames(meta?.lists || [], listRankingMode, WR_MIN_GAMES.lists),
            listRankingMode,
        ),
    );
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
                    {#each meta.factions || [] as dist}
                        {@const pct = totalFactionGames > 0
                            ? (((dist.games_count || 0) / totalFactionGames) * 100).toFixed(1)
                            : "0.0"}
                        <div
                            class="flex items-center gap-[6px] text-xs font-mono text-secondary mr-3 mb-[6px]"
                        >
                            <span
                                class="font-xwing xwing-icon text-sm"
                                style="color: {getFactionColor(dist.xws)}"
                                aria-hidden="true"
                            >
                                {getFactionChar(dist.xws)}
                            </span>
                            <span>{getFactionLabel(dist.xws)} {pct}%</span>
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
                <div class="mb-4 flex items-center justify-between gap-2">
                    <h2
                        class="text-sm font-mono font-bold uppercase text-primary"
                    >
                        Top Pilots
                    </h2>
                    <div class="inline-flex rounded border border-border-dark overflow-hidden">
                        <button
                            type="button"
                            class="px-2 py-1 text-[10px] font-mono uppercase tracking-wider transition-colors {pilotRankingMode === 'popularity' ? 'bg-secondary text-black' : 'bg-transparent text-secondary hover:bg-white/5'}"
                            onclick={() => (pilotRankingMode = "popularity")}
                        >
                            Games
                        </button>
                        <button
                            type="button"
                            class="px-2 py-1 text-[10px] font-mono uppercase tracking-wider border-l border-border-dark transition-colors {pilotRankingMode === 'winrate' ? 'bg-secondary text-black' : 'bg-transparent text-secondary hover:bg-white/5'}"
                            onclick={() => (pilotRankingMode = "winrate")}
                        >
                            WR
                        </button>
                    </div>
                </div>
                <div class="w-full flex flex-col">
                    {#each sortedPilots.slice(0, 6) as pilot}
                        {@const p = getPilotDisplay(pilot.xws)}
                        {@const wr = getWinRate(pilot.wins || 0, pilot.games_count || 0)}
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
                                            p.shipXws,
                                        )} text-2xl text-white"
                                    ></i>
                                </div>
                                <div
                                    class="flex flex-col overflow-hidden min-w-0 relative"
                                >
                                    <span
                                        class="text-base font-bold text-primary truncate min-w-0"
                                        title={p.name}>{p.name}</span
                                    >
                                    <div
                                        class="flex items-center gap-1 min-w-0 mt-0.5"
                                    >
                                        <span
                                            class="font-xwing xwing-icon text-[11px]"
                                            style="color: {getFactionColor(p.faction)}"
                                            aria-hidden="true"
                                        >
                                            {getFactionChar(p.faction)}
                                        </span>
                                        <span
                                            class="text-[12px] text-secondary truncate min-w-0 pointer-events-none"
                                        >
                                            {getFactionLabel(p.faction)} - {p.shipName}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div
                                class="flex flex-col items-end flex-shrink-0 text-right ml-2 pr-1"
                            >
                                <span
                                    class="text-base font-mono font-bold text-primary shrink-0"
                                    >{wr.toFixed(1)}% WR</span
                                >
                                <span
                                    class="text-[11px] text-secondary shrink-0"
                                    >{pilot.games_count || 0} games</span
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
                <div class="mb-4 flex items-center justify-between gap-2">
                    <h2
                        class="text-sm font-mono font-bold uppercase text-primary"
                    >
                        Top Upgrades
                    </h2>
                    <div class="inline-flex rounded border border-border-dark overflow-hidden">
                        <button
                            type="button"
                            class="px-2 py-1 text-[10px] font-mono uppercase tracking-wider transition-colors {upgradeRankingMode === 'popularity' ? 'bg-secondary text-black' : 'bg-transparent text-secondary hover:bg-white/5'}"
                            onclick={() => (upgradeRankingMode = "popularity")}
                        >
                            Games
                        </button>
                        <button
                            type="button"
                            class="px-2 py-1 text-[10px] font-mono uppercase tracking-wider border-l border-border-dark transition-colors {upgradeRankingMode === 'winrate' ? 'bg-secondary text-black' : 'bg-transparent text-secondary hover:bg-white/5'}"
                            onclick={() => (upgradeRankingMode = "winrate")}
                        >
                            WR
                        </button>
                    </div>
                </div>
                <div class="w-full flex flex-col">
                    {#each sortedUpgrades.slice(0, 6) as upgrade}
                        {@const uData = xwingData.getUpgrade(upgrade.xws)}
                        {@const upType = uData?.sides?.[0]?.type || "upgrade"}
                        {@const upName = uData?.name || upgrade.xws}
                        {@const wr = getWinRate(upgrade.wins || 0, upgrade.games_count || 0)}
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
                                            upType,
                                        )} text-secondary text-2xl"
                                    ></i>
                                </div>
                                <div
                                    class="flex flex-col overflow-hidden min-w-0 relative"
                                >
                                    <span
                                        class="text-base font-bold text-primary truncate min-w-0"
                                        title={upName}
                                        >{upName}</span
                                    >
                                    <div
                                        class="flex items-center gap-1 min-w-0 mt-0.5"
                                    >
                                        <span
                                            class="text-[12px] text-secondary truncate min-w-0 pointer-events-none"
                                            >{upType}</span
                                        >
                                    </div>
                                </div>
                            </div>
                            <div
                                class="flex flex-col items-end flex-shrink-0 text-right ml-2 pr-1"
                            >
                                <span
                                    class="text-base font-mono font-bold text-primary shrink-0"
                                    >{wr.toFixed(1)}% WR</span
                                >
                                <span
                                    class="text-[11px] text-secondary shrink-0"
                                    >{upgrade.games_count || 0} games</span
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
                <div class="mb-4 flex items-center justify-between gap-2">
                    <h2
                        class="text-sm font-mono font-bold uppercase text-primary"
                    >
                        Top Ships
                    </h2>
                    <div class="inline-flex rounded border border-border-dark overflow-hidden">
                        <button
                            type="button"
                            class="px-2 py-1 text-[10px] font-mono uppercase tracking-wider transition-colors {shipRankingMode === 'popularity' ? 'bg-secondary text-black' : 'bg-transparent text-secondary hover:bg-white/5'}"
                            onclick={() => (shipRankingMode = "popularity")}
                        >
                            Games
                        </button>
                        <button
                            type="button"
                            class="px-2 py-1 text-[10px] font-mono uppercase tracking-wider border-l border-border-dark transition-colors {shipRankingMode === 'winrate' ? 'bg-secondary text-black' : 'bg-transparent text-secondary hover:bg-white/5'}"
                            onclick={() => (shipRankingMode = "winrate")}
                        >
                            WR
                        </button>
                    </div>
                </div>
                <div class="w-full flex flex-col">
                    {#each sortedShips.slice(0, 6) as ship}
                        {@const shipData = xwingData.getShip(ship.xws)}
                        {@const shipName = shipData?.name || ship.xws}
                        {@const factionXws = ship.faction_xws}
                        {@const wr = getWinRate(ship.wins || 0, ship.games_count || 0)}
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
                                            ship.xws,
                                        )} text-2xl text-white"
                                    ></i>
                                </div>
                                <div
                                    class="flex flex-col overflow-hidden min-w-0 relative"
                                >
                                    <span
                                        class="text-base font-bold text-primary truncate min-w-0"
                                        title={shipName}
                                        >{shipName}</span
                                    >
                                    <div
                                        class="flex items-center gap-1 min-w-0 mt-0.5"
                                    >
                                        <span
                                            class="font-xwing xwing-icon text-[11px]"
                                            style="color: {getFactionColor(factionXws)}"
                                            aria-hidden="true"
                                        >
                                            {getFactionChar(factionXws)}
                                        </span>
                                        <span
                                            class="text-[12px] text-secondary truncate min-w-0 pointer-events-none"
                                            >{getFactionLabel(factionXws)}</span
                                        >
                                    </div>
                                </div>
                            </div>
                            <div
                                class="flex flex-col items-end flex-shrink-0 text-right ml-2 pr-1"
                            >
                                <span
                                    class="text-base font-mono font-bold text-primary shrink-0"
                                    >{wr.toFixed(1)}% WR</span
                                >
                                <span
                                    class="text-[11px] text-secondary shrink-0"
                                    >{ship.games_count || 0} games</span
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
                <div class="mb-4 flex items-center justify-between gap-2">
                    <h2
                        class="text-sm font-mono font-bold uppercase text-primary"
                    >
                        Top Meta Lists
                    </h2>
                    <div class="inline-flex rounded border border-border-dark overflow-hidden">
                        <button
                            type="button"
                            class="px-2 py-1 text-[10px] font-mono uppercase tracking-wider transition-colors {listRankingMode === 'popularity' ? 'bg-secondary text-black' : 'bg-transparent text-secondary hover:bg-white/5'}"
                            onclick={() => (listRankingMode = "popularity")}
                        >
                            Games
                        </button>
                        <button
                            type="button"
                            class="px-2 py-1 text-[10px] font-mono uppercase tracking-wider border-l border-border-dark transition-colors {listRankingMode === 'winrate' ? 'bg-secondary text-black' : 'bg-transparent text-secondary hover:bg-white/5'}"
                            onclick={() => (listRankingMode = "winrate")}
                        >
                            WR
                        </button>
                    </div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 w-full">
                    {#each sortedLists.slice(0, 4) as list}
                        {@const factionXws = list.faction_xws}
                        {@const wr = getWinRate(list.wins || 0, list.games || 0)}
                        <div
                            class="p-4 bg-[rgba(255,255,255,0.01)] border border-border-dark hover:bg-[rgba(255,255,255,0.03)] transition-colors cursor-pointer w-full flex flex-col gap-3 rounded-md"
                        >
                            <div
                                class="flex w-full items-start justify-between border-b border-border-dark pb-3"
                            >
                                <div
                                    class="flex items-center gap-2 overflow-hidden mr-2 h-12"
                                >
                                    <span
                                        class="font-xwing xwing-icon text-2xl flex-shrink-0"
                                        style="color: {getFactionColor(factionXws)}"
                                        aria-hidden="true"
                                    >
                                        {getFactionChar(factionXws)}
                                    </span>
                                    <div class="flex flex-col min-w-0">
                                        <span
                                            class="text-base font-bold text-primary line-clamp-2 leading-tight"
                                            title={list.name || "Unnamed List"}
                                            >{list.name || "Unnamed List"}</span
                                        >
                                        <span
                                            class="text-[10px] text-secondary uppercase tracking-tighter opacity-70"
                                        >
                                            {getFactionLabel(factionXws)}
                                        </span>
                                    </div>
                                </div>
                                <div
                                    class="flex flex-col items-end flex-shrink-0"
                                >
                                    <span
                                        class="text-base font-mono font-bold text-primary"
                                        >{wr.toFixed(1)}% WR</span
                                    >
                                    <span class="text-[11px] text-secondary"
                                        >{list.games} games</span
                                    >
                                </div>
                            </div>

                            <div class="flex flex-col gap-1 w-full flex-grow">
                                {#each list.pilots || [] as pilot}
                                    {@const p = getPilotDisplay(pilot.xws)}
                                    <div class="flex items-start gap-2">
                                        <i
                                            class="xwing-miniatures-ship {getShipIconClass(
                                                p.shipXws,
                                            )} text-secondary text-base w-6 text-center"
                                        ></i>
                                        <div class="min-w-0 flex-1">
                                            <div class="text-sm text-secondary truncate">
                                                {p.name}
                                            </div>
                                            {#if pilot.upgrades?.length}
                                                <div class="text-[11px] text-secondary/80 truncate">
                                                    {pilot.upgrades
                                                        .slice(0, 3)
                                                        .map((u: any) => xwingData.getUpgrade(u.xws)?.name || u.xws)
                                                        .join(", ")}
                                                </div>
                                            {/if}
                                        </div>
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

<style>
</style>
