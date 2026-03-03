<script lang="ts">
    import {
        getFactionColor,
        getFactionChar,
        getWinRateColor,
    } from "$lib/data/factions";
    import { filters } from "$lib/stores/filters.svelte";

    let { list }: { list: any } = $props();

    let factionColor = $derived(getFactionColor(list.faction_key || "unknown"));
    let wrColor = $derived(getWinRateColor(list.win_rate || 0));
    let isXwa = $derived(filters.dataSource === "xwa");
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
                    {getFactionChar(list.faction_key || "unknown")}
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
                    {list.points ?? 0} pts
                    {#if list.original_points && list.original_points !== list.points}
                        <span class="text-secondary/60 text-[10px] ml-1">(orig. {list.original_points})</span>
                    {/if}
                </span>
                <span
                    class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold"
                    style="background-color: {wrColor}22; color: {wrColor};"
                >
                    {(list.win_rate ?? 0).toFixed(1)}% WR
                </span>
                {#if isXwa}
                    <span
                        class="px-1.5 py-0.5 bg-violet-900/20 border border-violet-800/30 rounded text-[11px] font-mono text-violet-300"
                    >
                        LV: {list.total_loadout ?? 0}
                    </span>
                {/if}
                <span class="text-[11px] font-mono text-secondary">
                    {list.games ?? 0} games
                </span>
            </div>
        </div>

        <!-- Pilots Row -->
        <div class="flex flex-wrap gap-2">
            {#each list.pilots || [] as pilot}
                <div
                    class="bg-[#ffffff05] rounded-md px-2 py-2 min-w-[200px] flex-1 space-y-1.5"
                >
                    <!-- Pilot Header: Ship Icon + Name -->
                    <div class="flex items-center gap-2">
                        {#if pilot.ship_icon}
                            <i
                                class="xwing-miniatures-ship xwing-miniatures-ship-{pilot.ship_icon} text-2xl text-secondary"
                            ></i>
                        {/if}
                        <div>
                            <a
                                href="/cards?pilot={pilot.xws}"
                                class="text-sm font-sans font-bold text-primary hover:underline cursor-pointer"
                            >
                                {pilot.name || pilot.xws}
                            </a>
                            <div class="flex items-center gap-1.5">
                                <span
                                    class="text-[11px] font-mono text-secondary"
                                    >{pilot.points ?? 0} pts</span
                                >
                                {#if isXwa && pilot.loadout > 0}
                                    <span
                                        class="text-[11px] font-mono text-secondary"
                                        >LV: {pilot.loadout}</span
                                    >
                                {/if}
                            </div>
                        </div>
                    </div>

                    <!-- Upgrade Badges -->
                    {#if pilot.upgrades?.length > 0}
                        <div class="flex flex-wrap gap-1">
                            {#each pilot.upgrades as upg}
                                <span
                                    class="inline-flex items-center gap-0.5 px-1 py-0.5 border border-border-dark rounded bg-[#00000030] text-[10px] font-mono text-secondary"
                                    title={upg.name}
                                >
                                    {#if upg.slot}
                                        <span class="font-xwing text-[11px]"
                                            >{upg.slot_icon || ""}</span
                                        >
                                    {/if}
                                    {upg.name}
                                    {#if upg.points}
                                        <span class="text-secondary/60"
                                            >({upg.points})</span
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
