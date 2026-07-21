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
    import Chart from "chart.js/auto";
    import FactionIcon from "$lib/components/FactionIcon.svelte";

    let meta = $state<any>(null);
    let loading = $state(true);
    let error = $state(false);
    let errorMsg = $state("");

    /**
     * Latest tournament date in the current data source (and epic toggle).
     * Populated by a separate fetch to `/api/tournaments` so the "Last Sync"
     * stat can show the most recent tournament that actually exists in the
     * active source, rather than the generic `meta.last_sync` timestamp
     * (which is just `datetime.now()` formatted as a date on the backend).
     * Falls back to `meta.last_sync` while the fetch is in flight or if the
     * source has no tournaments yet.
     */
    let latestTournamentDate = $state<string | null>(null);

    /**
     * Source-aware Total Tournaments and Total Players counts.
     *
     * The `/api/meta-snapshot` endpoint computes `total_tournaments` and
     * `total_players` by counting rows in the tournaments/player_standings
     * tables with only a `date >= now-90d` filter — it does NOT filter by
     * `data_source`. As a result the meta-snapshot returns the same number
     * for XWA and Legacy (e.g. 73 for both), so the Total Tournaments /
     * Total Players stat cards never change when the user switches source.
     *
     * This effect computes the correct source-aware counts by hitting
     * `/api/tournaments` with the source's `formats` filter and the same
     * 90-day window, paginating if necessary to sum every tournament's
     * `players` field. The values are exposed as separate reactive state
     * (not by mutating `meta`) so there is no race with the meta-snapshot
     * $effect overwriting the object.
     *
     * The template prefers these values and falls back to the meta-snapshot
     * fields while this fetch is in flight.
     */
    let sourceAwareTournaments = $state<number | null>(null);
    let sourceAwarePlayers = $state<number | null>(null);

    /**
     * Map a `(dataSource, includeEpic)` pair to the list of `formats` the
     * tournaments endpoint should filter on. The XWA macro is `{xwa, amg}`
     * and the Legacy macro is `{legacy_x2po, legacy_xlc}`; the Epic toggle
     * controls whether the larger squad-size variant (amg / legacy_xlc) is
     * included.
     */
    function formatsForSource(
        source: "xwa" | "legacy",
        epic: boolean,
    ): string[] {
        if (source === "xwa") {
            return epic ? ["xwa", "amg"] : ["xwa"];
        }
        return epic ? ["legacy_x2po", "legacy_xlc"] : ["legacy_x2po"];
    }

    type SortKey = "popularity" | "winrate" | "games";
    type SortDir = "asc" | "desc";
    const DASHBOARD_RANKING_PREFS_KEY = "m3tacron.dashboard.rankingModes.v1";
    const WR_MIN_GAMES = {
        pilots: 3,
        upgrades: 3,
        ships: 3,
        lists: 3,
    };

    function isSortKey(v: unknown): v is SortKey {
        return v === "popularity" || v === "winrate" || v === "games";
    }

    function isSortDir(v: unknown): v is SortDir {
        return v === "asc" || v === "desc";
    }

    let pilotSortKey = $state<SortKey>("popularity");
    let pilotSortDir = $state<SortDir>("desc");
    let upgradeSortKey = $state<SortKey>("popularity");
    let upgradeSortDir = $state<SortDir>("desc");
    let shipSortKey = $state<SortKey>("popularity");
    let shipSortDir = $state<SortDir>("desc");
    let listSortKey = $state<SortKey>("popularity");
    let listSortDir = $state<SortDir>("desc");

    $effect(() => {
        if (!browser) return;

        try {
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
            console.warn("Failed to read dashboard ranking preferences", err);
        }
    });

    $effect(() => {
        if (!browser) return;

        try {
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
            console.warn("Failed to save dashboard ranking preferences", err);
        }
    });

    $effect(() => {
        if (!browser) return;
        // Track BOTH the data source AND the epic toggle so the dashboard
        // re-fetches whenever the user changes either one via the
        // ContentSourceToggle. Reading both inside the effect makes them
        // reactive dependencies under Svelte 5 runes.
        const source = filters.dataSource;
        const epic = filters.includeEpic;
        // Ensure data is loaded
        xwingData.setSource(source as any);

        let isCancelled = false;

        loading = true;
        error = false;
        errorMsg = "";

        // Pass `epic` to the meta-snapshot even though the backend currently
        // ignores it; the dashboard will already be wired correctly if the
        // endpoint starts honoring it. The `data_source` query param is the
        // one that actually filters the snapshot today.
        const params = new URLSearchParams();
        params.set("data_source", source);
        if (epic) params.set("epic", "true");
        const targetUrl = `/api/meta-snapshot?${params.toString()}`;
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

    /**
     * Fetch the latest tournament date in the current source. This is used
     * by the "Last Sync" stat so it shows a real tournament date instead of
     * the generic `last_sync` timestamp. The meta-snapshot endpoint doesn't
     * expose a "max(date)" field, so we hit `/api/tournaments` with
     * `size=1&sort=Date desc` and read the first item's `date`.
     *
     * Runs as a separate $effect so it re-issues on every (dataSource,
     * includeEpic) change and is independent of the main meta-snapshot
     * loading state.
     */
    $effect(() => {
        if (!browser) return;
        const source = filters.dataSource;
        const epic = filters.includeEpic;

        let isCancelled = false;

        const params = new URLSearchParams();
        params.set("page", "0");
        params.set("size", "1");
        params.set("sort_metric", "Date");
        params.set("sort_direction", "desc");
        for (const f of formatsForSource(source, epic)) {
            params.append("formats", f);
        }
        const url = `/api/tournaments?${params.toString()}`;

        fetch(url)
            .then(async (res) => {
                if (!res.ok) {
                    // Don't blow up the dashboard if this secondary fetch
                    // fails — the stat will fall back to `meta.last_sync`.
                    return null;
                }
                return res.json();
            })
            .then((data) => {
                if (isCancelled || !data) return;
                const first = data?.items?.[0];
                if (first?.date) {
                    latestTournamentDate = first.date;
                }
            })
            .catch(() => {
                /* swallow — keep previous / fallback value */
            });

        return () => {
            isCancelled = true;
        };
    });

    /**
     * Fetch source-aware Total Tournaments and Total Players counts for the
     * 90-day window that the meta-snapshot uses. See the
     * `sourceAwareTournaments` / `sourceAwarePlayers` declarations above
     * for why this exists.
     *
     * Hits `/api/tournaments?date_start=…&formats=…` (paginated at 100/page
     * which is the backend's hard cap) and:
     *   - reads `data.total` for Total Tournaments
     *   - sums `players` across every page for Total Players
     *
     * Re-issues on every (dataSource, includeEpic) change and is independent
     * of the meta-snapshot and latestTournamentDate $effects.
     */
    $effect(() => {
        if (!browser) return;
        const source = filters.dataSource;
        const epic = filters.includeEpic;

        // Reset to null on every source change so the template falls back
        // to the (stale) meta-snapshot values for the brief moment before
        // the new counts arrive, then snaps to the correct values.
        sourceAwareTournaments = null;
        sourceAwarePlayers = null;

        let isCancelled = false;

        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 90);
        const dateStart = startDate.toISOString().slice(0, 10);

        const formats = formatsForSource(source, epic);
        const pageSize = 100;

        const fetchPage = (page: number): Promise<any> => {
            const params = new URLSearchParams();
            params.set("page", String(page));
            params.set("size", String(pageSize));
            params.set("date_start", dateStart);
            for (const f of formats) {
                params.append("formats", f);
            }
            return fetch(`/api/tournaments?${params.toString()}`)
                .then((r) => (r.ok ? r.json() : null))
                .catch(() => null);
        };

        fetchPage(0).then(async (data) => {
            if (isCancelled || !data) return;
            const items: any[] = data?.items || [];
            const total: number = typeof data?.total === "number" ? data.total : items.length;
            let allPlayers = items.reduce(
                (sum: number, t: any) => sum + (Number(t?.players) || 0),
                0,
            );

            // Paginate to sum players across every page. The backend caps
            // `size` at 100, so anything beyond that needs additional
            // requests. In practice the 90-day window is well under 100
            // tournaments per source, but we paginate defensively so the
            // counts stay correct as the dataset grows.
            const totalPages = Math.ceil(total / pageSize);
            for (let p = 1; p < totalPages; p++) {
                if (isCancelled) return;
                const pageData = await fetchPage(p);
                if (!pageData) break;
                for (const item of pageData?.items || []) {
                    allPlayers += Number(item?.players) || 0;
                }
            }

            if (!isCancelled) {
                sourceAwareTournaments = total;
                sourceAwarePlayers = allPlayers;
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

    function getFactionIconClass(xws: string) {
        const normalized = (xws || "").toLowerCase().replace(/[^a-z0-9]/g, "");
        const icons: Record<string, string> = {
            rebelalliance: "xwing-miniatures-font-rebel",
            galacticempire: "xwing-miniatures-font-empire",
            scumandvillainy: "xwing-miniatures-font-scum",
            resistance: "xwing-miniatures-font-resistance",
            firstorder: "xwing-miniatures-font-firstorder",
            galacticrepublic: "xwing-miniatures-font-republic",
            separatistalliance: "xwing-miniatures-font-separatists",
        };
        return icons[normalized] || "";
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
            } else {
                // popularity: by games count, with WR tiebreaker
                if (gamesB !== gamesA) cmp = gamesB - gamesA;
                else cmp = wrB - wrA;
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
     * Period banner range. We treat the snapshot's `last_sync` as the end of
     * the 90-day window and compute the start by subtracting 90 days. This
     * keeps the banner purely client-side and avoids any backend changes.
     * Returns null when `last_sync` is missing or unparseable so the banner
     * can fall back to a generic "last 90 days" label.
     */
    let periodRange = $derived.by(() => {
        const endStr = meta?.last_sync;
        if (!endStr || typeof endStr !== "string" || endStr === "Never") {
            return null;
        }
        const end = new Date(endStr);
        if (Number.isNaN(end.getTime())) return null;
        const start = new Date(end);
        start.setDate(start.getDate() - 90);
        const fmt = (d: Date) => d.toISOString().slice(0, 10);
        return { start: fmt(start), end: fmt(end) };
    });
</script>

<div class="min-h-screen p-6 font-sans">
    <header
        class="mb-8 flex flex-col md:flex-row md:items-start justify-between gap-4 w-full"
    >
        <div>
            <h1 class="text-3xl font-sans font-bold text-primary mb-1">
                Meta Dashboard
            </h1>
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
        <!-- Period Banner: prominent "Last 90 Days" indicator -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-4 mb-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
        >
            <div class="flex flex-col sm:flex-row sm:items-center gap-3 flex-wrap">
                <div
                    class="px-2 py-1 bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded text-xs font-mono font-bold uppercase tracking-wider self-start"
                >
                    {meta.date_range || "Last 90 Days"}
                </div>
                <div
                    data-testid="period-banner-data-source"
                    class="px-2 py-1 {filters.dataSource === 'legacy'
                        ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                        : 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'} border rounded text-xs font-mono font-bold uppercase tracking-wider self-start"
                >
                    {filters.dataSource === 'legacy' ? 'Legacy' : 'XWA'}
                </div>
                <span class="text-sm text-secondary font-mono">
                    {#if periodRange}
                        Tournament data from {periodRange.start} to {periodRange.end}
                    {:else}
                        Tournament data from the most recent 90 days
                    {/if}
                </span>
            </div>
        </div>

        <!-- Top Stats Row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1"
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
                <div
                    data-testid="dashboard-total-tournaments"
                    class="text-4xl font-bold font-mono text-primary"
                >
                    {sourceAwareTournaments ?? meta.total_tournaments ?? 0}
                </div>
            </div>

            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1"
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
                <div
                    data-testid="dashboard-total-players"
                    class="text-4xl font-bold font-mono text-primary"
                >
                    {sourceAwarePlayers ?? meta.total_players ?? 0}
                </div>
            </div>

            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] flex flex-col items-start gap-1"
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
                    data-testid="dashboard-last-sync"
                    class="text-2xl font-bold font-mono text-primary leading-tight mt-1"
                >
                    {latestTournamentDate || meta.last_sync || "Unknown"}
                </div>
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
                            { value: "popularity", label: "Popularity" },
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
                    {#each sortedPilots.slice(0, 5) as pilot}
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
                                        <i
                                            class="xwing-miniatures-font {getFactionIconClass(
                                                p.faction,
                                            )} text-[11px]"
                                            style="color: {getFactionColor(
                                                p.faction,
                                            )}"
                                        ></i>
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
                            { value: "popularity", label: "Popularity" },
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
                                    >{upgrade.games_count || 0} games</span
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
                            { value: "popularity", label: "Popularity" },
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
                    {#each sortedShips.slice(0, 5) as ship}
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
                                        <i
                                            class="xwing-miniatures-font {getFactionIconClass(
                                                factionXws,
                                            )} text-[11px]"
                                            style="color: {getFactionColor(
                                                factionXws,
                                            )}"
                                        ></i>
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
                            { value: "popularity", label: "Popularity" },
                            { value: "winrate", label: "Win Rate" },
                            { value: "games", label: "Games" }
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
                            class="p-4 bg-[rgba(255,255,255,0.01)] border border-border-dark hover:bg-[rgba(255,255,255,0.03)] transition-colors cursor-pointer w-full flex flex-col gap-3 rounded-lg"
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
