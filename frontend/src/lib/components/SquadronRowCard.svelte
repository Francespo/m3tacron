<script module lang="ts">
    import { xwingData } from "$lib/stores/xwingData.svelte";

    // Module-level cache so all SquadronRowCard instances share a single
    // in-flight load of the xwingData manifest.
    let dataLoadPromise: Promise<void> | null = null;
    function ensureXwingDataLoaded() {
        if (!dataLoadPromise) {
            dataLoadPromise = xwingData.setSource(xwingData.currentSource);
        }
        return dataLoadPromise;
    }
</script>

<script lang="ts">
    import {
        getFactionColor,
        getFactionLabel,
        getWinRateColor,
    } from "$lib/data/factions";
    import FactionIcon from "./FactionIcon.svelte";

    let { list } = $props<{ list: any }>();

    let fColor = $derived(getFactionColor(list.faction_key));
    // Prefer backend-computed win_rate (always present, already clamped to
    // 0-100 with one decimal) and fall back to recomputing from wins/games
    // for any future callers that don't pre-aggregate.
    let wr = $derived.by(() => {
        const backend = Number(list.win_rate ?? list.wr ?? 0);
        if (Number.isFinite(backend) && backend > 0) return backend;
        const games = Number(list.games ?? 0);
        const wins = Number(list.wins ?? 0);
        if (!Number.isFinite(games) || games <= 0) return 0;
        return Math.max(0, Math.min(100, (wins / games) * 100));
    });
    let wrColor = $derived(getWinRateColor(wr));

    // Ensure xwingData manifest is loaded so getShip() can resolve human names.
    // The /squadrons route does not call setSource itself, so we trigger loading
    // here. Guarded by data presence so the effect is a no-op when already loaded.
    $effect(() => {
        if (!xwingData.data[xwingData.currentSource]) {
            ensureXwingDataLoaded();
        }
    });

    // Aggregate ships from pilots to display counts.
    // Use the XWS code (p.ship_xws) as the dedup key so the link href
    // (/ship/{xws}) matches the backend route. The xwing-miniatures-ship
    // icon class uses the same XWS code (e.g. "fangfighter").
    let ships = $derived(() => {
        const counts: Record<string, { icon: string; count: number }> = {};
        for (const p of list.pilots) {
            const xws = p.ship_xws || p.ship_name;
            if (!counts[xws]) {
                counts[xws] = { icon: p.ship_icon || xws, count: 0 };
            }
            counts[xws].count++;
        }
        return Object.entries(counts)
            .map(([xws, data]) => ({
                xws,
                displayName: xwingData.getShip(xws)?.name ?? xws,
                icon: data.icon,
                count: data.count,
            }))
            .sort((a, b) => a.displayName.localeCompare(b.displayName));
    });
</script>

<div
    class="flex relative bg-terminal-panel border border-border-dark border-l-[3px] rounded-lg overflow-hidden group hover:bg-[#ffffff05] hover:border-primary/40 transition-colors"
    style="border-left: 3px solid {fColor};"
>
    <!-- Stretched link covers the whole card so the rest of the area
         (faction label, stats) still navigates to the squadron page.
         Ship label links are siblings with z-index 1 so they win on click. -->
    <a
        href="/squadron/{encodeURIComponent(list.signature || '')}"
        class="absolute inset-0 z-0"
        aria-label="View squadron details"
    ></a>
    <!-- Card Content -->
    <div class="flex-1 p-4 flex flex-col gap-3 relative pointer-events-none">
        <!-- Header -->
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
                <FactionIcon faction={list.faction_key} size="lg" />
                <span
                    class="text-sm font-bold font-mono tracking-wide"
                    style="color: {fColor};"
                >
                    {getFactionLabel(list.faction_key)}
                </span>
            </div>

            <!-- Stats Badges (standardized pill pattern) -->
            <div class="flex items-center gap-1.5 flex-wrap font-mono text-xs font-bold">
                <span
                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                >
                    LISTS {list.count} (UNIQUE {list.count})
                </span>
                <span
                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold"
                    style="color: {wrColor};"
                >
                    WR {list.games === 0 ? "NA" : wr.toFixed(1) + "%"}
                </span>
                <span
                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold"
                >
                    GAMES {list.games ?? 0}
                </span>
            </div>
        </div>

        <!-- Ships Container -->
        <div class="flex flex-wrap gap-2 items-center">
            {#each ships() as ship}
                <div
                    class="flex items-center bg-[rgba(255,255,255,0.03)] border border-border-dark rounded px-2 py-1 gap-2 relative z-10 pointer-events-auto"
                >
                    <span class="text-xs font-mono font-bold text-secondary"
                        >{ship.count}x</span
                    >
                    <i
                        class="xwing-miniatures-ship xwing-miniatures-ship-{ship.icon} text-lg text-primary"
                    ></i>
                    <a
                        href="/ship/{ship.icon}"
                        class="text-xs font-mono text-primary hover:text-accent transition-colors border-b border-transparent hover:border-accent/50 truncate max-w-[120px]"
                        title={ship.displayName}>{ship.displayName}</a
                    >
                </div>
            {/each}
        </div>
    </div>
</div>
