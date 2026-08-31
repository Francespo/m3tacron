<script lang="ts">
    import { browser } from "$app/environment";
    import { goto } from "$app/navigation";
    import BackLink from "$lib/components/BackLink.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { getFactionColor } from "$lib/data/factions";
import SortBy from "$lib/components/SortBy.svelte";
import FactionIcon from "$lib/components/FactionIcon.svelte";
import { xwingData } from "$lib/stores/xwingData.svelte";
import ListRowCard from "$lib/components/ListRowCard.svelte";
import LocalFilterBar from "$lib/components/LocalFilterBar.svelte";
import DebouncedTextInput from "$lib/components/DebouncedTextInput.svelte";
import { page as pageState } from "$app/state";
import { untrack } from "svelte";

    let { data }: { data: any } = $props();
    import StatIcon from "$lib/components/StatIcon.svelte";

    let info = $derived(data.info);
    let upgrades = $derived(data.upgrades);
    let chart = $derived(data.chart);
    let configurations = $derived(data.configurations);
    let headerStats = $derived(data.headerStats);
    // Horizontal / standard-loadout pilots (quickbuilds, slots==[], no loadout) — treated like upgrades for sizing
    let isHorizontal = $derived(!!info?.image && String(info.image).includes("/quickbuilds/"));
    let hasNoUpgradesConfig = $derived(isHorizontal || (info?.slots && info.slots.length === 0));
    let headerSq = $derived(Math.max(0, Number((headerStats ?? {}).squadron_count ?? 0)));
    let headerLists = $derived(Math.max(0, Number((headerStats ?? {}).list_count ?? (headerStats ?? {}).different_lists_count ?? 0)));
    let headerEntries = $derived(Math.max(0, Number((headerStats ?? {}).entries_count ?? 0)));
    let headerGames = $derived(Math.max(0, Number((headerStats ?? {}).games_count ?? 0)));
    let headerWins = $derived(Math.max(0, Number((headerStats ?? {}).wins ?? 0)));
    let headerWr = $derived(headerGames > 0 ? (headerWins / headerGames) * 100 : 0);
    let initialized = $state(false);

    $effect(() => { xwingData.setSource(filters.dataSource as any); });

    // Pagination: configs 12/page (4 cols × 3 rows), upgrades 12/page — all backend-sourced (real GAMES/LISTS/WR)
    const CONFIG_PAGE_SIZE = 12;
    const UPG_PAGE_SIZE = 12;
    let configPage = $state(0);
    let upgPage = $state(0);
    let pilotListsSort = $state<"Games" | "Win Rate">("Games");
    let pilotListsDir = $state<"desc" | "asc">("desc");
    let pilotListsPage = $state(0);
    const PILOT_LISTS_PAGE_SIZE = 4;
    // Server-paginated: data.pilotLists is the current page (4 items), data.pilotListsTotal is real total
    // Client-side sort state for "Top Configurations". The backend
    // returns configs pre-sorted by `count` desc; we re-sort in the
    // browser so the SortBy control can flip between "most-played"
    // (popularity / lists / games, all proxied by `count`), and
    // computed win rate (provided by the backend).
    type ConfigSortKey = "lists" | "games" | "winrate";
    let configSortKey = $state<ConfigSortKey>("lists");
    let configSortDir = $state<"asc" | "desc">("desc");

    // --- Local section filters: per-section, URL-prefix ready (upg_*, cfg_*, plist_*) ---

    function configSortValue(c: any): number {
        switch (configSortKey) {
            case "winrate":
                return Math.max(0, c.win_rate ?? 0);
            case "games":
                return Math.max(0, c.games ?? 0);
            case "lists":
            default:
                return Math.max(0, c.lists ?? c.count ?? 0);
        }
    }

    // Server-paginated pilot lists (4/page, SQL): real total (e.g. 266 for Vader), not capped to 12.
    // Use local $state so mutating after fetch is reactive — mutating data.* from $props is not.
    let pilotListsItems = $state(data.pilotLists ?? []);
    let pilotListsTotal = $state(Number(data.pilotListsTotal ?? 0) || 0);
    let filteredListsSource = $derived(pilotListsItems as any[]);
    let filteredConfigurationsSource = $derived(configurations as any[]);

    let sortedConfigurations = $derived.by(() => {
        const dir = configSortDir === "asc" ? 1 : -1;
        return [...filteredConfigurationsSource].sort((a, b) => {
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
        return Math.max(0, Number(u.games_count ?? u.count ?? 0));
    }
    function upgWinRate(u: any): number {
        const g = upgGames(u);
        const w = Math.max(0, Number(u.wins ?? 0));
        return g > 0 ? (w / g) * 100 : -1;
    }
    let filteredUpgrades = $derived(upgrades as any[]);

    let sortedUpgrades = $derived.by(() => {
        const dir = upgSortDir === "asc" ? 1 : -1;
        return [...filteredUpgrades].sort((a, b) => {
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

    function getDefaultFormats(ds: "xwa" | "legacy", includeEpic?: boolean): string[] {
        if (ds === "xwa") {
            return includeEpic ? ["xwa", "xwa_epic"] : ["xwa"];
        }
        return ["legacy_x2po"];
    }

    $effect(() => {
        if (initialized) return;
        if (data.ds === "legacy" || data.ds === "xwa") {
            filters.dataSource = data.ds;
        }
        // Only sync the epic flag from the URL when the URL explicitly
        // carries it. A plain navigation from another page (e.g. a card
        // link) drops the query string, and the store must keep its value
        // so the toggle stays consistent across routes.
        if (data.hasEpicParam) {
            filters.includeEpic = !!data.includeEpic;
        }
        initialized = true;
    });

    $effect(() => {
        if (!initialized) return;

        const keep = browser ? new URLSearchParams(window.location.search) : new URLSearchParams();
        const params = new URLSearchParams();
        params.set("data_source", filters.dataSource);
        if (filters.includeEpic) params.set("epic", "true");
        for (const f of getDefaultFormats(filters.dataSource, filters.includeEpic)) {
            params.append("formats", f);
        }
        // preserve style + local prefixes (URL with prefix)
        for (const k of ["style", "upg_search", "upg_slot", "cfg_search", "plist_search"]) {
            const v = keep.get(k);
            if (v !== null && v !== "") params.set(k, v);
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

    let upgTotalPages = $derived(Math.max(1, Math.ceil(sortedUpgrades.length / UPG_PAGE_SIZE)));
    let upgItems = $derived(sortedUpgrades.slice(upgPage * UPG_PAGE_SIZE, (upgPage + 1) * UPG_PAGE_SIZE));
    $effect(() => { void sortedConfigurations; configPage = 0; });
    $effect(() => { void sortedUpgrades; upgPage = 0; });

    let pilotListsTotalPages = $derived(Math.max(1, Math.ceil(pilotListsTotal / PILOT_LISTS_PAGE_SIZE)));
    $effect(() => {
        pilotListsItems = data.pilotLists ?? [];
        pilotListsTotal = Number(data.pilotListsTotal ?? 0) || 0;
        pilotListsPage = 0;
    });
    async function fetchPilotListsPage(page: number, sort: string, dir: string) {
        const p = new URLSearchParams({
            data_source: data.ds ?? "xwa",
            sort_metric: sort,
            sort_direction: dir,
            size: String(PILOT_LISTS_PAGE_SIZE),
            page: String(page),
        });
        for (const f of (data.formats ?? [])) p.append("formats", f);
        const { API_BASE } = await import("$lib/api");
        const res = await fetch(`${API_BASE}/pilot/${data.pilotXws}/lists?${p.toString()}`);
        if (!res.ok) return;
        const j = await res.json().catch(() => null);
        pilotListsItems = Array.isArray(j?.items) ? j.items : [];
        pilotListsTotal = Number(j?.total ?? 0) || 0;
        pilotListsPage = page;
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
    <title>{info?.name || data.pilotXws} — Pilot Detail | M3taCron</title>
    <meta name="description" content="Detailed statistics for {info?.name || data.pilotXws} pilot in X-Wing Miniatures." />
</svelte:head>

<div class="min-h-screen p-6 md:p-8 font-sans">
    <!-- Back link -->
    <div class="mb-6">
        <BackLink href="/cards" ariaLabel="Back to Cards" />
    </div>

    <!-- Header Section -->
    {#if isHorizontal}
        <!-- Horizontal (standard-loadout) pilot: SAME ZOOM as vertical (280×~392 portrait → ~610×380 landscape, quickbuilds are ~1.6:1).
             Image on the left at vertical height, name/ship/capsules to its right; chart FULL-WIDTH BELOW (like upgrades page). -->
        <div class="flex flex-col lg:flex-row gap-8 mb-6">
            <div class="flex-shrink-0 flex items-center justify-center" style="width: 620px; max-width: 100%;">
                {#if info?.image}
                    <img src={info.image} alt={info.name} class="w-full h-auto object-contain drop-shadow-[0_4px_16px_rgba(0,0,0,0.45)]" style="max-height: 380px;" loading="eager" />
                {:else}
                    <div class="w-full h-[240px] flex items-center justify-center"><span class="text-secondary font-mono text-sm">NO IMAGE</span></div>
                {/if}
            </div>
            <div class="flex-1 min-w-0 flex flex-col justify-center gap-3">
                <div class="flex items-center gap-3 flex-wrap min-w-0">
                    <h1 class="text-3xl font-sans font-bold text-primary">{info?.name || data.pilotXws}</h1>
                    <span class="px-2 py-0.5 text-xs font-mono font-bold rounded-md bg-blue-500/20 text-blue-400 border border-blue-500/30">PILOT</span>
                    {#if info?.faction_xws}<FactionIcon faction={info.faction_xws} size="lg" />{/if}
                </div>
                {#if info?.ship}
                    <p class="text-secondary font-mono text-sm">
                        {#if info.ship_xws}<i class="xwing-miniatures-ship xwing-miniatures-ship-{info.ship_xws}" style="color: {getFactionColor(info.faction_xws || '')}; font-size: 1.2rem;"></i>{/if}
                        {info.ship}
                    </p>
                {/if}
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">SQUADRONS {headerSq}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">LISTS {headerLists}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">ENTRIES {headerEntries}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">GAMES {headerGames}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold" style="color: {wrColor(headerWr)};">WR {headerWr.toFixed(1)}%</span>
                    {#if info?.cost != null}<span class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-md text-[10px] font-mono font-bold">PTS {info.cost}</span>{/if}
                    {#if info?.loadout != null && info.loadout > 0}<span class="px-1.5 py-0.5 bg-violet-500/20 text-violet-400 border border-violet-500/30 rounded-md text-[10px] font-mono font-bold">LV {info.loadout}</span>{/if}
                </div>
            </div>
        </div>
        <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] mb-10">
            <h2 class="text-sm font-sans font-bold text-primary uppercase tracking-wider mb-3">Games Played Over Time</h2>
            {#if chartConfig}<div class="h-[220px]"><canvas use:chartAction={chartConfig}></canvas></div>{:else}<p class="text-secondary font-mono text-xs py-8 text-center">No game data available for chart.</p>{/if}
        </div>
    {:else}
        <div class="flex flex-col lg:flex-row gap-8 mb-10">
            <div class="flex-shrink-0 flex items-center justify-center" style="width: 280px; max-width: 100%;">
                {#if info?.image}
                    <img src={info.image} alt={info.name} class="max-w-full h-auto object-contain drop-shadow-[0_4px_16px_rgba(0,0,0,0.45)]" style="max-height: 380px;" loading="eager" />
                {:else}
                    <div class="w-full h-[300px] flex items-center justify-center"><span class="text-secondary font-mono text-sm">NO IMAGE</span></div>
                {/if}
            </div>
            <div class="flex-grow flex flex-col gap-6">
                <div>
                    <div class="flex items-center gap-3 flex-wrap min-w-0">
                        <h1 class="text-3xl font-sans font-bold text-primary">{info?.name || data.pilotXws}</h1>
                        <span class="px-2 py-0.5 text-xs font-mono font-bold rounded-md bg-blue-500/20 text-blue-400 border border-blue-500/30">PILOT</span>
                        {#if info?.faction_xws}<FactionIcon faction={info.faction_xws} size="lg" />{/if}
                    </div>
                    {#if info?.ship}
                        <p class="text-secondary font-mono text-sm mt-1">
                            {#if info.ship_xws}<i class="xwing-miniatures-ship xwing-miniatures-ship-{info.ship_xws}" style="color: {getFactionColor(info.faction_xws || '')}; font-size: 1.2rem;"></i>{/if}
                            {info.ship}
                        </p>
                    {/if}
                </div>
                <div class="flex items-center gap-2 mt-3 flex-wrap">
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">SQUADRONS {headerSq}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">LISTS {headerLists}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">ENTRIES {headerEntries}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary">GAMES {headerGames}</span>
                    <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold" style="color: {wrColor(headerWr)};">WR {headerWr.toFixed(1)}%</span>
                    {#if info?.cost != null}<span class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-md text-[10px] font-mono font-bold">PTS {info.cost}</span>{/if}
                    {#if info?.loadout != null && info.loadout > 0}<span class="px-1.5 py-0.5 bg-violet-500/20 text-violet-400 border border-violet-500/30 rounded-md text-[10px] font-mono font-bold">LV {info.loadout}</span>{/if}
                </div>
                <div class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                    <h2 class="text-sm font-sans font-bold text-primary uppercase tracking-wider mb-3">Games Played Over Time</h2>
                    {#if chartConfig}<div class="h-[220px]"><canvas use:chartAction={chartConfig}></canvas></div>{:else}<p class="text-secondary font-mono text-xs py-8 text-center">No game data available for chart.</p>{/if}
                </div>
            </div>
        </div>
    {/if}


    <!-- Compatible Upgrades — hidden for standard-loadout (horizontal) pilots that have no upgrade slots -->
    {#if !hasNoUpgradesConfig}
    <section class="mb-10">
        <div class="flex items-center justify-between gap-3 mb-4 flex-wrap">
            <h2 class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2">Compatible Upgrades</h2>
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

        {#if upgItems.length > 0}
            <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
                {#each upgItems as u (u.xws)}
                    {@const _uData = xwingData.getUpgrade(u.xws)}
                    {@const uName = u.name || _uData?.name || u.xws_name || u.xws}
                    {@const uImage = u.image || _uData?.sides?.[0]?.image || ""}
                    {@const uSlotRaw = (u.type || _uData?.sides?.[0]?.slots?.[0] || '').trim()}
                    {@const uSlot = (uSlotRaw || u.type_xws || u.slot_xws || '').toLowerCase()}
                    {@const uGames = Math.max(0, Number(u.games_count ?? u.count ?? u.games ?? 0))}
                    {@const uLists = Math.max(0, Number(u.list_count ?? u.lists ?? 0))}
                    {@const uWr = uGames > 0 ? (Math.max(0, Number(u.wins ?? 0)) / uGames) * 100 : 0}
                    {@const uSlotLabel = uSlot ? uSlot.charAt(0).toUpperCase() + uSlot.slice(1) : 'Upgrade'}
                    <a href="/upgrade/{u.xws}" class="bg-terminal-panel border border-border-dark rounded-lg p-3 flex gap-3 items-center hover:border-primary/30 transition-colors group">
                        {#if uImage}
                            <img src={uImage} alt={uName} class="w-[6.5rem] h-[3.8rem] object-contain drop-shadow-[0_2px_8px_rgba(0,0,0,0.45)] flex-shrink-0 self-center rounded-sm" loading="lazy" />
                        {:else}
                            <div class="w-[6.5rem] h-[3.8rem] flex-shrink-0 self-center flex items-center justify-center rounded-sm bg-black/20 border border-white/5"><StatIcon type={uSlot || "upgrade"} size="1.6rem" color="rgba(255,255,255,0.15)" /></div>
                        {/if}
                        <div class="min-w-0 flex-1 flex flex-col justify-center">
                            <p class="text-sm font-sans font-bold text-primary truncate group-hover:text-accent transition-colors" title={uName}>{uName}</p>
                            <p class="text-[11px] font-mono text-secondary uppercase tracking-wider truncate" title={uSlotLabel}>{uSlotLabel}</p>
                            <div class="flex flex-wrap gap-1 mt-1.5">
                                <span class="px-1 py-0.5 bg-[#ffffff05] border border-border-dark rounded text-[10px] font-mono font-bold text-secondary">LISTS {uLists}</span>
                                <span class="px-1 py-0.5 bg-[#ffffff05] border border-border-dark rounded text-[10px] font-mono font-bold text-secondary">GAMES {uGames}</span>
                                <span class="px-1 py-0.5 rounded text-[10px] font-mono font-bold" style="background: {wrColor(uWr)}15; color: {wrColor(uWr)};">WR {uWr.toFixed(1)}%</span>
                            </div>
                        </div>
                    </a>
                {/each}
            </div>
            <div class="flex items-center justify-center gap-2 mt-6">
                <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {upgPage === 0 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={upgPage === 0} onclick={() => upgPage = Math.max(0, upgPage - 1)}>← Prev</button>
                <span class="text-xs font-mono text-secondary">Showing {upgPage * UPG_PAGE_SIZE + 1}–{Math.min((upgPage + 1) * UPG_PAGE_SIZE, sortedUpgrades.length)} of {sortedUpgrades.length} · Page {upgPage + 1}/{upgTotalPages}</span>
                <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {upgPage >= upgTotalPages - 1 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={upgPage >= upgTotalPages - 1} onclick={() => upgPage = Math.min(upgTotalPages - 1, upgPage + 1)}>Next →</button>
            </div>
        {:else}
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center">
                <p class="text-secondary font-mono text-sm">No upgrade data available for this pilot.</p>
            </div>
        {/if}
    </section>
    {/if}

    <!-- Configurations — hidden for standard-loadout pilots (no configs) -->
    {#if !hasNoUpgradesConfig && configurations && configurations.length > 0}
        {@const configTotalPages = Math.max(1, Math.ceil(sortedConfigurations.length / CONFIG_PAGE_SIZE))}
        {@const configPageItems = sortedConfigurations.slice(configPage * CONFIG_PAGE_SIZE, (configPage + 1) * CONFIG_PAGE_SIZE)}
        <section>
            <div class="flex items-center justify-between gap-3 mb-4 flex-wrap">
                <h2 class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2">Configurations</h2>
                <SortBy
                    value={configSortKey}
                    direction={configSortDir}
                    options={[
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
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {#each configPageItems as config, j (config.upgrades.map((u: any) => u.xws).join("|") + ":" + j)}
                    {@const i = configPage * CONFIG_PAGE_SIZE + j}
                    <div class="bg-terminal-panel border border-border-dark rounded-lg p-3 overflow-hidden flex flex-col">
                        <div class="flex items-center justify-between gap-2 mb-3">
                            <span class="text-xs font-mono text-secondary">#{i + 1}</span>
                            <div class="flex flex-wrap items-center gap-1.5 justify-end">
                                <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-secondary">LISTS {config.lists ?? config.count}</span>
                                <span class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-secondary">GAMES {config.games ?? 0}</span>
                                <span class="px-1.5 py-0.5 rounded-md text-[10px] font-mono font-bold" style="background: {wrColor(config.win_rate)}15; color: {wrColor(config.win_rate)};">WR {Number(config.win_rate ?? 0).toFixed(1)}%</span>
                            </div>
                        </div>
                        {#if config.upgrades.length > 0}
                            <div class="flex flex-wrap gap-1.5">
                                {#each config.upgrades as upg}
                                    {@const upgCost = upg.cost?.value ?? upg.cost ?? null}
                                    {@const resolvedUpg = xwingData.getUpgrade(upg.xws)}
                                    {@const slotForIcon = resolvedUpg?.sides?.[0]?.slots?.[0] || upg.type || "upgrade"}
                                    <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-white/[0.06] border border-white/10 text-[11px]">
                                        <StatIcon type={slotForIcon} size="0.85rem" color="rgba(255,255,255,0.55)" />
                                        <a href="/upgrade/{upg.xws}" title="View {upg.name}" class="font-sans font-semibold text-primary underline decoration-transparent hover:decoration-primary/40 hover:text-accent underline-offset-2 transition-colors">{upg.name}</a>
                                        {#if upgCost !== null && upgCost !== undefined}<span class="ml-1 px-1 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 leading-none">{upgCost} PT</span>{/if}
                                    </span>
                                {/each}
                            </div>
                        {:else}
                            <p class="text-xs font-mono text-secondary italic">No upgrades</p>
                        {/if}
                    </div>
                {/each}
            </div>
            <div class="flex items-center justify-center gap-2 mt-6">
                <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {configPage === 0 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={configPage === 0} onclick={() => configPage = Math.max(0, configPage - 1)}>← Prev</button>
                <span class="text-xs font-mono text-secondary">Showing {configPage * CONFIG_PAGE_SIZE + 1}–{Math.min((configPage + 1) * CONFIG_PAGE_SIZE, sortedConfigurations.length)} of {sortedConfigurations.length} · Page {configPage + 1}/{configTotalPages}</span>
                <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {configPage >= configTotalPages - 1 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={configPage >= configTotalPages - 1} onclick={() => configPage = Math.min(configTotalPages - 1, configPage + 1)}>Next →</button>
            </div>
        </section>
    {/if}

    <!-- Lists Featuring This Pilot — reuses existing ListRowCard (SQL-paginated, 4/page, 2 cols) -->
    <section>
        <div class="flex items-center justify-between gap-3 mb-4 flex-wrap">
            <h2 class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2">Lists Featuring This Pilot</h2>
            <SortBy
                value={pilotListsSort}
                direction={pilotListsDir}
                options={[
                    { value: "Games", label: "Games" },
                    { value: "Win Rate", label: "Win Rate" }
                ]}
                onChange={(v, d) => { pilotListsSort = v as "Games" | "Win Rate"; pilotListsDir = d; fetchPilotListsPage(0, v, d); }}
            />
        </div>

        {#if filteredListsSource.length > 0}
            <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
                {#each filteredListsSource as lst (lst.signature)}
                    <ListRowCard list={lst} />
                {/each}
            </div>
            <div class="flex items-center justify-center gap-2 mt-6">
                <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {pilotListsPage === 0 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={pilotListsPage === 0} onclick={() => fetchPilotListsPage(Math.max(0, pilotListsPage - 1), pilotListsSort, pilotListsDir)}>← Prev</button>
                <span class="text-xs font-mono text-secondary">Showing {pilotListsPage * PILOT_LISTS_PAGE_SIZE + 1}–{Math.min((pilotListsPage + 1) * PILOT_LISTS_PAGE_SIZE, pilotListsTotal)} of {pilotListsTotal} · Page {pilotListsPage + 1}/{pilotListsTotalPages}</span>
                <button type="button" class="px-3 py-1.5 rounded-md border text-xs font-mono transition-colors {pilotListsPage >= pilotListsTotalPages - 1 ? 'border-border-dark text-secondary' : 'border-primary text-primary hover:bg-white/[0.04]'}" disabled={pilotListsPage >= pilotListsTotalPages - 1} onclick={() => fetchPilotListsPage(Math.min(pilotListsTotalPages - 1, pilotListsPage + 1), pilotListsSort, pilotListsDir)}>Next →</button>
            </div>
        {:else}
            <div class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center">
                <p class="text-secondary font-mono text-sm">"No lists found featuring this pilot."</p>
            </div>
        {/if}
    </section>
</div>
