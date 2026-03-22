<script lang="ts">
    import {
        getFactionColor,
        getFactionChar,
        getWinRateColor,
    } from "$lib/data/factions";
    import { filters } from "$lib/stores/filters.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { getSlotIcon } from "$lib/data/slots";

    let { list }: { list: any } = $props();

    let factionColor = $derived(getFactionColor(list.faction_xws || "unknown"));
    let wr = $derived(list.games > 0 ? (list.wins / list.games) * 100 : 0);
    let wrColor = $derived(getWinRateColor(wr));
    let isXwa = $derived(filters.dataSource === "xwa");

    function normalizeXws(value: unknown): string {
        return String(value ?? "").trim();
    }

    let computedCurrentPoints = $derived.by(() => {
        let total = 0;
        for (const pilotEntry of list.pilots || []) {
            const pilotXws = normalizeXws(pilotEntry.xws);
            const p = xwingData.getPilot(pilotXws);
            total += p?.cost ?? 0;
        }
        return total;
    });

    let displayedPoints = $derived(
        isXwa && computedCurrentPoints > 0 ? computedCurrentPoints : (list.points ?? 0),
    );
</script>

<div
    class="flex bg-terminal-panel border border-border-dark rounded-md overflow-hidden hover:border-secondary/40 transition-colors"
>
    <!-- Faction Color Strip -->
    <div
        class="w-1.5 shrink-0 self-stretch"
        style="background-color: {factionColor};"
    ></div>

    <!-- Content -->
    <div class="flex-1 p-3 space-y-2">
        <!-- Header: Faction icon + Badges -->
        <div class="flex items-center justify-between flex-wrap gap-2">
            <!-- Faction Icon and List Name -->
            <div class="flex items-center gap-3">
                <span class="font-xwing text-xl" style="color: {factionColor};">
                    {getFactionChar(list.faction_xws || "unknown")}
                </span>
                <a
                    href="/list/{encodeURIComponent(
                        list.signature || list.name || list.id,
                    )}"
                    class="text-sm font-sans font-bold text-primary hover:text-accent transition-colors"
                >
                    {list.name || "Untitled List"}
                </a>
            </div>

            <!-- Stats Badges -->
            <div class="flex items-center gap-1.5 flex-wrap">
                <span
                    class="px-1.5 py-0.5 bg-[#ffffff08] border border-border-dark rounded text-[11px] font-mono text-secondary"
                >
                    {displayedPoints} pts
                    {#if displayedPoints !== (list.points ?? 0)}
                        <span class="text-secondary/60 text-[10px] ml-1"
                            >(orig. {list.points ?? 0})</span
                        >
                    {:else if list.original_points && list.original_points !== list.points}
                        <span class="text-secondary/60 text-[10px] ml-1"
                            >(orig. {list.original_points})</span
                        >
                    {/if}
                </span>
                <span
                    class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold"
                    style="background-color: {wrColor}22; color: {wrColor};"
                >
                    {list.games === 0
                        ? "NA"
                        : wr.toFixed(1) + "%"} WR
                </span>
                <span class="text-[11px] font-mono text-secondary">
                    {list.games ?? 0} games
                </span>
            </div>
        </div>

        <!-- Pilots Row -->
        <div class="flex flex-wrap gap-2">
            {#each list.pilots || [] as pilotEntry}
                {@const pilotXws = normalizeXws(pilotEntry.xws)}
                {@const pilot = xwingData.getPilot(pilotXws)}
                {@const ship = pilot ? xwingData.getShip(pilot.ship) : null}
                <div
                    class="bg-[#ffffff05] rounded-md px-2 py-2 min-w-[200px] flex-1 space-y-1.5"
                >
                    <!-- Pilot Header: Ship Icon + Name -->
                    <div class="flex items-center gap-2">
                        {#if pilot && pilot.ship}
                            <i
                                class="xwing-miniatures-ship xwing-miniatures-ship-{pilot.ship.replace(/[^a-z0-9]/g, '')} text-2xl text-secondary"
                            ></i>
                        {/if}
                        <div>
                            <span class="text-sm font-sans font-bold text-primary">
                                {pilot?.name || pilotXws}
                            </span>
                            <div class="flex items-center gap-1.5">
                                <span
                                    class="text-[11px] font-mono text-secondary"
                                    >{pilot?.cost ?? "?"} pts</span
                                >
                                {#if isXwa && pilot?.loadout}
                                    <span
                                        class="text-[11px] font-mono text-secondary"
                                        >LV: {pilot.loadout}</span
                                    >
                                {/if}
                            </div>
                        </div>
                    </div>

                    <!-- Upgrade Badges -->
                    {#if pilotEntry.upgrades?.length > 0}
                        <div class="flex flex-wrap gap-1">
                            {#each pilotEntry.upgrades as upgEntry}
                                {@const upgradeXws = normalizeXws(upgEntry.xws)}
                                {@const upg = xwingData.getUpgrade(upgradeXws)}
                                {@const slot = upg?.sides?.[0]?.slots?.[0] || 'unknown'}
                                <span
                                    class="inline-flex items-center gap-0.5 px-1 py-0.5 border border-border-dark rounded bg-[#00000030] text-[10px] font-mono text-secondary"
                                    title={upg?.name}
                                >
                                    {#if slot}
                                        <span class="font-xwing text-[11px]"
                                            >{getSlotIcon(slot)}</span
                                        >
                                    {/if}
                                    {upg?.name || upgradeXws}
                                    {#if upg?.cost?.value}
                                        <span class="text-secondary/60"
                                            >({upg.cost.value})</span
                                        >
                                    {/if}
                                </span>
                            {/each}
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    </div>
</div>
