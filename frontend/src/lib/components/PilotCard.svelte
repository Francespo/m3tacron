<script lang="ts">
    /**
     * PilotCard.svelte
     * Purpose: High-fidelity Pilot card component.
     * Replicates the current grid-card aesthetic while allowing for expanded views.
     */
    import {
        getWinRateColor,
        getFactionColor,
        getFactionChar,
    } from "$lib/data/factions";
    import StatIcon from "./StatIcon.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";

    let {
        pilot,
        viewMode = "grid", // 'grid' for browser, 'detailed' for side-panels
        showImage = true,
        showName = true,
        showShip = true,
        showStats = true,
    }: {
        pilot: any;
        viewMode?: "grid" | "detailed";
        showImage?: boolean;
        showName?: boolean;
        showShip?: boolean;
        showStats?: boolean;
    } = $props();

    const pData = $derived(xwingData.getPilot(pilot.xws));

    // Stats calculation
    const games = $derived(pilot.games_count ?? 0);
    const wins = $derived(pilot.wins ?? 0);
    const wr = $derived(games > 0 ? (wins / games) * 100 : 0);
    const wrColor = $derived(getWinRateColor(wr));
    const listsCount = $derived(pilot.list_count ?? pilot.lists ?? 0);
    const differentListsCount = $derived(
        pilot.different_lists_count ?? pilot.different_list_count ?? 0,
    );

    const faction = $derived(pData?.faction || pilot.faction_xws || "unknown");
    const fColor = $derived(getFactionColor(faction));
    const fChar = $derived(getFactionChar(faction));
    const name = $derived(pData?.name || pilot.xws);
    const image = $derived(pData?.image);
    const shipXws = $derived(pData?.ship);
    const shipName = $derived(
        shipXws ? xwingData.getShip(shipXws)?.name || pilot.ship_name : pilot.ship_name,
    );
    const subtitle = $derived(pData?.caption || pData?.shipAbility?.name || "");
    const points = $derived(pData?.cost ?? pilot.points ?? pilot.cost ?? 0);
    const loadout = $derived(pData?.loadout ?? pilot.loadout);
</script>

{#if viewMode === "grid"}
    <div
        class="bg-terminal-panel border border-border-dark rounded-xl overflow-hidden hover:border-primary/40 transition-all duration-300 hover:scale-[1.04] hover:z-20 flex flex-col relative aspect-square group"
    >
        <!-- Card Image -->
        {#if showImage}
            <div
                class="relative w-full flex-[2.2] overflow-hidden bg-[#050505] flex items-center justify-center p-2"
            >
                {#if image}
                    <img
                        src={image}
                        alt={name}
                        class="max-w-full max-h-full object-contain drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]"
                        loading="lazy"
                    />
                {:else}
                    <!-- Placeholder fallback using X-Wing Font Ship Icon -->
                    <StatIcon
                        type={shipXws || pilot.ship_xws || ""}
                        size="5rem"
                        color="rgba(255,255,255,0.05)"
                        isShip={true}
                    />
                {/if}
            </div>
        {/if}

        <!-- Info Section -->
        <div class="p-2 flex-1 flex flex-col justify-between">
            <!-- Name + Ship Badge -->
            <div class="mb-1.5">
                {#if showName}
                    <h3
                        class="text-base font-sans font-bold text-primary leading-tight flex items-center justify-between gap-2 w-full"
                        title={name}
                    >
                        <div class="flex items-center gap-2 overflow-hidden">
                            <div
                                class="flex-shrink-0 w-6 h-6 rounded-full bg-white/5 flex items-center justify-center border border-white/10"
                            >
                                <StatIcon
                                    type={shipXws || pilot.ship_xws || ""}
                                    size="1rem"
                                    color="white"
                                    isShip={true}
                                    className="drop-shadow-md opacity-90"
                                    style="filter: brightness(1.1);"
                                />
                            </div>
                            <span class="truncate">{name}</span>
                        </div>
                        {#if fChar}
                            <StatIcon
                                type={fChar}
                                size="1.125rem"
                                color={fColor}
                                className="drop-shadow-md opacity-90 flex-shrink-0"
                                style="filter: brightness(1.2);"
                            />
                        {/if}
                    </h3>
                {/if}
                {#if showShip && subtitle}
                    <p
                        class="text-[11px] mt-1 font-mono text-secondary/80 uppercase tracking-wider line-clamp-1"
                        title={subtitle}
                    >
                        {subtitle}
                    </p>
                {/if}
            </div>

            <!-- Stats Badges -->
            {#if showStats}
                <div class="flex flex-wrap gap-1.5 mt-auto">
                    <!-- WR -->
                    <div
                        class="px-1.5 py-0.5 rounded bg-[#ffffff0a] border border-[#ffffff10] flex items-center gap-1"
                    >
                        <span
                            class="text-[10px] font-bold"
                            style="color: {wrColor};"
                        >
                            {isNaN(wr) ? "NA" : wr.toFixed(1) + "%"}
                        </span>
                        <span class="text-[9px] font-mono text-secondary"
                            >WR</span
                        >
                    </div>
                    <!-- Games -->
                    <div
                        class="px-1.5 py-0.5 rounded bg-[#ffffff0a] border border-[#ffffff10] flex items-center gap-1"
                    >
                        <span class="text-[10px] font-bold text-primary"
                            >{games}</span
                        >
                        <span class="text-[9px] font-mono text-secondary"
                            >G</span
                        >
                    </div>
                    <!-- Lists + Different Lists -->
                    <div
                        class="px-1.5 py-0.5 rounded bg-[#ffffff0a] border border-[#ffffff10] flex items-center gap-1"
                    >
                        <span class="text-[10px] font-bold text-primary"
                            >{listsCount}</span
                        >
                        <span class="text-[9px] font-mono text-secondary"
                            >L</span
                        >
                        <span class="text-[8px] font-mono text-secondary/80"
                            >(DL {differentListsCount})</span
                        >
                    </div>
                    <!-- Points -->
                    <div
                        class="px-1.5 py-0.5 rounded bg-emerald-900/30 border border-emerald-500/30 flex items-center gap-1"
                    >
                        <span class="text-[10px] font-bold text-emerald-400"
                            >{points}</span
                        >
                        <span class="text-[9px] font-mono text-emerald-500/80"
                            >PTS</span
                        >
                    </div>
                    <!-- Loadout (XWA Only logic) -->
                    {#if loadout !== undefined && loadout !== null}
                        <div
                            class="px-1.5 py-0.5 rounded bg-violet-900/20 border border-violet-500/20 flex items-center gap-1"
                        >
                            <span class="text-[10px] font-bold text-violet-300"
                                >{loadout}</span
                            >
                            <span
                                class="text-[9px] font-mono text-violet-400/80"
                                >LV</span
                            >
                        </div>
                    {/if}
                </div>
            {/if}
        </div>
    </div>
{:else}
    <!-- Detailed mode for side-panels (To be implemented) -->
    <div class="detailed-card">
        <p>Detailed view for {name} coming soon...</p>
    </div>
{/if}

<style>
    /* Custom component styles if needed */
</style>
