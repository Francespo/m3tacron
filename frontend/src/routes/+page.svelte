<svelte:head>
    <title>M3tacron — X-Wing Tournament Analytics &amp; Meta Engine</title>
</svelte:head>

<script lang="ts">
    import { browser } from "$app/environment";
    import { filters } from "$lib/stores/filters.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import {
        getFactionColor,
        getFactionChar,
        getFactionLabel,
    } from "$lib/data/factions";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { cachedFetchJson } from "$lib/api/cache";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import Chart from "chart.js/auto";
    import FactionIcon from "$lib/components/FactionIcon.svelte";

    let meta = $state<any>(null);
    let loading = $state(true);
    let error = $state(false);
    let errorMsg = $state("");
    // Bumped by the "Try again" button so the main fetch $effect re-runs.
    let retryToken = $state(0);

    function retry() {
        retryToken++;
    }

    // `meta` now carries authoritative source-filtered totals and the
    // real scraper timestamp (`last_sync` = last scrape run, even when
    // zero tournaments were saved). No extra /tournaments fetches needed.

    type SortKey = "lists" | "entries" | "winrate" | "games";
    type SortDir = "asc" | "desc";
    const DASHBOARD_RANKING_PREFS_KEY = "m3tacron.dashboard.rankingModes.v1";
    const DASHBOARD_TIME_RANGE_PREFS_KEY = "m3tacron.dashboard.timeRange.v1";

    const TIME_RANGE_OPTIONS = [
        { value: "7", label: "Last 7 days" },
        { value: "30", label: "Last 30 days" },
        { value: "90", label: "Last 90 days" },
        { value: "180", label: "Last 6 months" },
        { value: "365", label: "Last year" },
        { value: "all", label: "All time" },
    ];

    let selectedTimeRange = $state<string>("90");

    const WR_MIN_GAMES = {
        pilots: 3,
        upgrades: 3,
        ships: 3,
        lists: 3,
    };

    function isSortKey(v: unknown): v is SortKey {
        return v === "lists" || v === "entries" || v === "winrate" || v === "games";
    }

    function isSortDir(v: unknown): v is SortDir {
        return v === "asc" || v === "desc";
    }

    let pilotSortKey = $state<SortKey>("lists");
    let pilotSortDir = $state<SortDir>("desc");
    let upgradeSortKey = $state<SortKey>("lists");
    let upgradeSortDir = $state<SortDir>("desc");
    let shipSortKey = $state<SortKey>("lists");
    let shipSortDir = $state<SortDir>("desc");
    let listSortKey = $state<SortKey>("lists");
    let listSortDir = $state<SortDir>("desc");

    $effect(() => {
        if (!browser) return;

        try {
            const savedRange = localStorage.getItem(DASHBOARD_TIME_RANGE_PREFS_KEY);
            if (savedRange && ["7", "30", "90", "180", "365", "all"].includes(savedRange)) {
                selectedTimeRange = savedRange;
            }

            const raw = localStorage.getItem(DASHBOARD_RANKING_PREFS_KEY);
            if (!raw) return;

            const saved = JSON.parse(raw) as any;

            // Backward-compat: previous format stored a plain string per
            // section (e.g. { pilots: "popularity" }). New format stores
            // { pilots: { key, dir } }.
            const readSection = (
                raw: any,
            ): { key: SortKey; dir: SortDir } | null => {
                if (typeof raw === "string" && isSortKey(raw)) {
                    return { key: raw, dir: "desc" };
                }
                if (
                    raw &&
                    typeof raw === "object" &&
                    isSortKey(raw.key) &&
                    isSortDir(raw.dir)
                ) {
                    return { key: raw.key, dir: raw.dir };
                }
                return null;
            };

            const pilots = readSection(saved.pilots);
            if (pilots) {
                pilotSortKey = pilots.key;
                pilotSortDir = pilots.dir;
            }
            const upgrades = readSection(saved.upgrades);
            if (upgrades) {
                upgradeSortKey = upgrades.key;
                upgradeSortDir = upgrades.dir;
            }
            const ships = readSection(saved.ships);
            if (ships) {
                shipSortKey = ships.key;
                shipSortDir = ships.dir;
            }
            const lists = readSection(saved.lists);
            if (lists) {
                listSortKey = lists.key;
                listSortDir = lists.dir;
            }
        } catch (err) {
            console.warn("Failed to read dashboard preferences", err);
        }
    });

    $effect(() => {
        if (!browser) return;

        try {
            localStorage.setItem(DASHBOARD_TIME_RANGE_PREFS_KEY, selectedTimeRange);
            localStorage.setItem(
                DASHBOARD_RANKING_PREFS_KEY,
                JSON.stringify({
                    pilots: { key: pilotSortKey, dir: pilotSortDir },
                    upgrades: { key: upgradeSortKey, dir: upgradeSortDir },
                    ships: { key: shipSortKey, dir: shipSortDir },
                    lists: { key: listSortKey, dir: listSortDir },
                }),
            );
        } catch (err) {
            console.warn("Failed to save dashboard preferences", err);
        }
    });

    $effect(() => {
        if (!browser) return;
        // Track data source, epic toggle, and selected time range so the dashboard
        // re-fetches whenever the user changes any of them.
        const source = filters.dataSource;
        const epic = filters.includeEpic;
        const timeRange = selectedTimeRange;
        const _rt = retryToken;
        // Ensure data is loaded
        xwingData.setSource(source as any);

        let isCancelled = false;

        loading = true;
        error = false;
        errorMsg = "";

        // AbortController so rapid source/filter changes cancel the
        // in-flight request instead of racing it. `isCancelled` guards the
        // state updates; the abort actually stops the network request.
        const controller = new AbortController();

        const params = new URLSearchParams();
        params.set("data_source", source);
        if (epic) params.set("epic", "true");
        if (timeRange && timeRange !== "all") {
            params.set("days", timeRange);
        } else if (timeRange === "all") {
            params.set("days", "0");
        }
        const targetUrl = `/api/meta-snapshot?${params.toString()}`;
        cachedFetchJson(targetUrl, undefined, controller.signal)
            .then((data) => {
                if (!isCancelled) {
                    meta = data;
                    loading = false;
                }
            })
            .catch((err) => {
                if (err?.name === "AbortError") return;
                console.error("Dashboard Fetch Error:", err);
                if (!isCancelled) {
                    // Drop any stale cached snapshot so a transient failure
                    // (e.g. backend restart, empty cache race) can never
                    // leave `meta` stuck on an old/zeroed payload — the next
                    // retry always hits the network fresh.
                    import("$lib/api/cache").then((m) => m.clearApiCache());
                    error = true;
                    errorMsg = `URL: ${targetUrl} | Error: ${err.message || String(err)}`;
                    loading = false;
                }
            });

        return () => {
            isCancelled = true;
            controller.abort();
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

    function sortByKey(
        items: any[],
        key: SortKey,
        dir: SortDir,
    ): any[] {
        return [...items].sort((a, b) => {
            const gamesA = Number(a.games_count ?? a.games ?? 0);
            const gamesB = Number(b.games_count ?? b.games ?? 0);
            const wrA = getWinRate(Number(a.wins ?? 0), gamesA);
            const wrB = getWinRate(Number(b.wins ?? 0), gamesB);

            let cmp = 0;
            if (key === "winrate") {
                if (wrB !== wrA) cmp = wrB - wrA;
                else cmp = gamesB - gamesA;
            } else if (key === "games") {
                cmp = gamesB - gamesA;
            } else if (key === "entries") {
                const eA = Number(a.entries_count ?? a.list_count ?? 0);
                const eB = Number(b.entries_count ?? b.list_count ?? 0);
                if (eB !== eA) cmp = eB - eA;
                else cmp = gamesB - gamesA;
            } else {
                const listA = Number(a.list_count ?? 0);
                const listB = Number(b.list_count ?? 0);
                if (listB !== listA) cmp = listB - listA;
                else cmp = gamesB - gamesA;
            }

            return dir === "desc" ? cmp : -cmp;
        });
    }

    function applyWrMinGames(
        items: any[],
        key: SortKey,
        minGames: number,
    ): any[] {
        if (key !== "winrate") return items;
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
            pack: (pilot as any)?.pack,
        };
    }

    Chart.defaults.color = "#AAAAAA";

    function chartAction(node: HTMLCanvasElement, config: any) {
        const chart = new Chart(node, config);

        return {
            update(newConfig: any) {
                chart.update(newConfig);
            },
            destroy() {
                chart.destroy();
            },
        };
    }

    let barData = $derived(
        meta?.factions
            ? {
                  // Chart.js labels are plain strings — keep the raw "?" fallback
                  // for unknown so Chart.js doesn't try to render an HTML
                  // element. (The X-Wing font would render "?" as a
                  // geometric/rocket glyph otherwise.)
                  labels: meta.factions.map((d: any) =>
                      d.xws === "unknown" ? "?" : getFactionChar(d.xws),
                  ),
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
        sortByKey(
            applyWrMinGames(meta?.pilots || [], pilotSortKey, WR_MIN_GAMES.pilots),
            pilotSortKey,
            pilotSortDir,
        ),
    );

    let sortedUpgrades = $derived(
        sortByKey(
            applyWrMinGames(meta?.upgrades || [], upgradeSortKey, WR_MIN_GAMES.upgrades),
            upgradeSortKey,
            upgradeSortDir,
        ),
    );

    let sortedShips = $derived(
        sortByKey(
            applyWrMinGames(meta?.ships || [], shipSortKey, WR_MIN_GAMES.ships),
            shipSortKey,
            shipSortDir,
        ),
    );

    let sortedLists = $derived(
        sortByKey(
            applyWrMinGames(meta?.lists || [], listSortKey, WR_MIN_GAMES.lists),
            listSortKey,
            listSortDir,
        ),
    );

    /**
     * Period banner range. Computes start and end dates based on
     * backend metadata or client-side date window calculation.
     */
    let periodRange = $derived.by(() => {
        if (selectedTimeRange === "all") {
            if (meta?.date_start && meta?.date_end) {
                return { start: meta.date_start, end: meta.date_end, isAll: true };
            }
            const endStr = meta?.date_end || meta?.last_sync;
            const endVal = endStr && endStr !== "Never" ? endStr : "present";
            return { start: meta?.date_start || "All recorded", end: endVal, isAll: true };
        }

        const daysNum = parseInt(selectedTimeRange, 10) || 90;
        const endStr = meta?.date_end || meta?.last_sync;
        if (!endStr || typeof endStr !== "string" || endStr === "Never") {
            return null;
        }
        const end = new Date(endStr);
        if (Number.isNaN(end.getTime())) return null;

        const fmt = (d: Date) => d.toISOString().slice(0, 10);
        let startStr = meta?.date_start;
        if (!startStr) {
            const start = new Date(end);
            start.setDate(start.getDate() - daysNum);
            startStr = fmt(start);
        }
        return { start: startStr, end: fmt(end), isAll: false };
    });
</script>

<div class="min-h-screen p-6 font-sans">
    <header class="mb-5 flex flex-col gap-3">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h1 class="text-3xl font-sans font-bold text-primary leading-none shrink-0">Meta Dashboard</h1>

            <div class="flex flex-wrap items-center gap-3">
                <!-- Time Range Dropdown Selector -->
                <div class="flex items-center gap-2">
                    <label for="time-range-select" class="text-xs text-secondary font-mono uppercase tracking-wider whitespace-nowrap">
                        Time range
                    </label>
                    <select
                        id="time-range-select"
                        bind:value={selectedTimeRange}
                        class="bg-terminal-panel border border-border-dark rounded-md text-xs font-mono text-primary px-2.5 py-1.5 focus:outline-none focus:border-white/40 cursor-pointer shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
                    >
                        {#each TIME_RANGE_OPTIONS as opt}
                            <option value={opt.value}>{opt.label}</option>
                        {/each}
                    </select>
                </div>

                {#if !loading && !error && meta}
                    <div class="hidden md:flex items-center gap-2 text-xs font-mono text-secondary shrink-0">
                        <span class="w-px h-4 bg-white/10"></span>
                        <span class="tracking-widest {filters.dataSource === 'legacy' ? 'text-violet-400' : 'text-amber-400'}">
                            {filters.dataSource === 'legacy' ? 'Legacy' : 'XWA'}
                        </span>
                        <span class="w-px h-4 bg-white/10"></span>
                        <span class="hidden lg:inline text-secondary">
                            {#if periodRange}
                                {#if periodRange.isAll}
                                    Tournament data · All time
                                {:else}
                                    Tournament data {periodRange.start} → {periodRange.end}
                                {/if}
                            {:else}
                                Tournament data · {meta.date_range || "Last 90 days"}
                            {/if}
                        </span>
                        <span class="hidden lg:inline w-px h-4 bg-white/10"></span>
                        <span class="hidden xl:inline text-secondary">Last sync {meta.last_sync || "Unknown"}</span>
                    </div>
                {/if}
            </div>
        </div>

        <!-- Mobile Info Banner / Subtitle (shown on mobile < md viewports) -->
        {#if !loading && !error && meta}
            <div class="flex md:hidden flex-wrap items-center gap-x-2 gap-y-1 text-xs font-mono text-secondary">
                <span class="tracking-widest font-semibold text-primary">
                    {meta.date_range || (selectedTimeRange === 'all' ? 'All time' : `Last ${selectedTimeRange} days`)}
                </span>
                <span class="w-px h-3.5 bg-white/15"></span>
                <span class="tracking-widest font-semibold {filters.dataSource === 'legacy' ? 'text-violet-400' : 'text-amber-400'}">
                    {filters.dataSource === 'legacy' ? 'Legacy' : 'XWA'}
                </span>
                {#if periodRange}
                    <span class="w-px h-3.5 bg-white/15"></span>
                    <span class="text-secondary/80">
                        {#if periodRange.isAll}
                            All data
                        {:else}
                            {periodRange.start} → {periodRange.end}
                        {/if}
                    </span>
                {/if}
                {#if meta.last_sync && meta.last_sync !== "Never" && meta.last_sync !== "Unknown"}
                    <span class="w-px h-3.5 bg-white/15"></span>
                    <span class="text-secondary/60 text-[11px]">Sync: {meta.last_sync}</span>
                {/if}
            </div>
        {/if}
    </header>

    {#if error}
        <ErrorPanel
            title="Failed to load dashboard data"
            message={errorMsg}
            onRetry={retry}
        />
    {:else if loading || !meta}
        <!-- Loading Skeleton (matches dashboard shape: stat cards, chart
             panels, leaderboard columns) -->
        <div class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                {#each Array(3) as _}
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg p-4 h-24 space-y-2"
                    >
                        <div
                            class="animate-pulse bg-[#ffffff06] rounded h-3 w-24"
                        ></div>
                        <div
                            class="animate-pulse bg-[#ffffff06] rounded h-8 w-16"
                        ></div>
                    </div>
                {/each}
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div
                    class="bg-terminal-panel border border-border-dark rounded-lg p-5 h-[280px]"
                >
                    <div
                        class="animate-pulse bg-[#ffffff06] rounded h-4 w-40 mb-4"
                    ></div>
                    <div
                        class="animate-pulse bg-[#ffffff06] rounded h-[220px] w-full"
                    ></div>
                </div>
                <div
                    class="bg-terminal-panel border border-border-dark rounded-lg p-5 h-[280px]"
                >
                    <div
                        class="animate-pulse bg-[#ffffff06] rounded h-4 w-40 mb-4"
                    ></div>
                    <div
                        class="animate-pulse bg-[#ffffff06] rounded h-[220px] w-full"
                    ></div>
                </div>
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {#each Array(3) as _}
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg p-5 space-y-3"
                    >
                        <div
                            class="animate-pulse bg-[#ffffff06] rounded h-4 w-32"
                        ></div>
                        {#each Array(4) as _}
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-6 w-full"
                            ></div>
                        {/each}
                    </div>
                {/each}
            </div>
        </div>
    {:else}
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <!-- Tournaments -->
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1">
                <div class="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-secondary"><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/></svg>
                    <span class="text-secondary font-mono text-[10px] font-bold uppercase tracking-widest">Tournaments</span>
                </div>
                <div data-testid="dashboard-total-tournaments" class="text-4xl font-bold font-mono text-primary">{meta.total_tournaments ?? 0}</div>
            </div>
            <!-- Lists (sidebar icon) -->
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1">
                <div class="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-secondary"><path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/></svg>
                    <span class="text-secondary font-mono text-[10px] font-bold uppercase tracking-widest">Lists</span>
                </div>
                <div data-testid="dashboard-total-lists" class="text-4xl font-bold font-mono text-primary">{meta.total_lists ?? 0}</div>
            </div>
            <!-- Players (person) -->
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1">
                <div class="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-secondary"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                    <span class="text-secondary font-mono text-[10px] font-bold uppercase tracking-widest">Players</span>
                </div>
                <div data-testid="dashboard-total-players" class="text-4xl font-bold font-mono text-primary">{meta.total_players ?? 0}</div>
            </div>
            <!-- Games (crossed swords) -->
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1">
                <div class="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-secondary"><path d="M14.5 17.5 3 6V3h3l11.5 11.5-3 3z"/><path d="M13 19 3 9"/><path d="M9.5 17.5 20 6V3h-3L6.5 13.5l3 3z"/><path d="M11 19l-2 2"/></svg>
                    <span class="text-secondary font-mono text-[10px] font-bold uppercase tracking-widest">Games</span>
                </div>
                <div data-testid="dashboard-total-games" class="text-4xl font-bold font-mono text-primary">{meta.total_games ?? 0}</div>
            </div>
        </div>

        <!-- Section 1: Factions -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
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
                class="bg-terminal-panel border border-border-dark rounded-lg p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
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
                            <FactionIcon faction={dist.xws} size="sm" />
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
                class="bg-terminal-panel border border-border-dark rounded-lg p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <div class="mb-4 flex items-baseline justify-between gap-3">
                    <h2
                        class="text-sm font-mono font-bold uppercase text-primary border-b border-border-dark pb-2 flex items-baseline gap-2 flex-1"
                    >
                        Top Pilots
                    </h2>
                    <SortBy
                        value={pilotSortKey}
                        direction={pilotSortDir}
                        options={[
                            { value: "lists", label: "Lists" },
                            { value: "winrate", label: "Win Rate" },
                            { value: "games", label: "Games" }
                        ]}
                        onChange={(newValue, newDirection) => {
                            pilotSortKey = newValue as SortKey;
                            pilotSortDir = newDirection;
                        }}
                    />
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
                                        <FactionIcon
                                            faction={p.faction}
                                            size="xs"
                                            className="text-[11px]"
                                        />
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
                                    >{pilot.games_count || 0} games · {pilot.list_count ?? pilot.lists ?? 0} lists</span
                                >
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Top Upgrades -->
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <div class="mb-4 flex items-baseline justify-between gap-3">
                    <h2
                        class="text-sm font-mono font-bold uppercase text-primary border-b border-border-dark pb-2 flex items-baseline gap-2 flex-1"
                    >
                        Top Upgrades
                    </h2>
                    <SortBy
                        value={upgradeSortKey}
                        direction={upgradeSortDir}
                        options={[
                            { value: "lists", label: "Lists" },
                            { value: "winrate", label: "Win Rate" },
                            { value: "games", label: "Games" }
                        ]}
                        onChange={(newValue, newDirection) => {
                            upgradeSortKey = newValue as SortKey;
                            upgradeSortDir = newDirection;
                        }}
                    />
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
                                    >{upgrade.games_count || 0} games · {upgrade.list_count ?? upgrade.lists ?? 0} lists</span
                                >
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Top Ships -->
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <div class="mb-4 flex items-baseline justify-between gap-3">
                    <h2
                        class="text-sm font-mono font-bold uppercase text-primary border-b border-border-dark pb-2 flex items-baseline gap-2 flex-1"
                    >
                        Top Ships
                    </h2>
                    <SortBy
                        value={shipSortKey}
                        direction={shipSortDir}
                        options={[
                            { value: "lists", label: "Lists" },
                            { value: "winrate", label: "Win Rate" },
                            { value: "games", label: "Games" }
                        ]}
                        onChange={(newValue, newDirection) => {
                            shipSortKey = newValue as SortKey;
                            shipSortDir = newDirection;
                        }}
                    />
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
                                        <FactionIcon
                                            faction={factionXws}
                                            size="xs"
                                            className="text-[11px]"
                                        />
                                        <span
                                            class="text-[12px] text-secondary truncate min-w-0 pointer-events-none"
                                            >{getFactionLabel(factionXws)}</span>
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
                                    >{ship.games_count || 0} games · {ship.list_count ?? ship.lists ?? 0} lists</span
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
                class="bg-terminal-panel border border-border-dark rounded-lg p-[20px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] w-full flex flex-col"
            >
                <div class="mb-4 flex items-baseline justify-between gap-3">
                    <h2
                        class="text-sm font-mono font-bold uppercase text-primary border-b border-border-dark pb-2 flex items-baseline gap-2 flex-1"
                    >
                        Top Meta Lists
                    </h2>
                    <SortBy
                        value={listSortKey}
                        direction={listSortDir}
                        options={[
                            { value: "winrate", label: "Win Rate" },
                            { value: "games", label: "Games" },
                            { value: "entries", label: "Entries" }
                        ]}
                        onChange={(newValue, newDirection) => {
                            listSortKey = newValue as SortKey;
                            listSortDir = newDirection;
                        }}
                    />
                </div>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 w-full">
                    {#each sortedLists.slice(0, 4) as list}
                        {@const factionXws = list.faction_xws}
                        {@const wr = getWinRate(list.wins || 0, list.games || 0)}
                        <div
                            class="p-4 bg-[rgba(255,255,255,0.01)] border border-border-dark border-l-[3px] hover:bg-[rgba(255,255,255,0.03)] transition-colors cursor-pointer w-full flex flex-col gap-3 rounded-lg overflow-hidden"
                            style="border-left: 3px solid {getFactionColor(factionXws)};"
                        >
                            <div
                                class="flex w-full items-start justify-between border-b border-border-dark pb-3"
                            >
                                <div
                                    class="flex items-center gap-2 overflow-hidden mr-2 h-12"
                                >
                                    <FactionIcon
                                        faction={factionXws}
                                        size="lg"
                                        className="flex-shrink-0"
                                    />
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
                                        >{list.games} games · {(list.entries ?? list.entries_count ?? list.count ?? 1)} entries</span
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
                                            {#if p.pack}
                                                <div class="text-[11px] text-secondary/80 italic truncate">
                                                    {p.pack}
                                                </div>
                                            {:else if pilot.upgrades?.length}
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
