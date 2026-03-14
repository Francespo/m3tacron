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

    // Stats calculation
    const wr = $derived(Number(pilot.win_rate ?? 0));
    const wrColor = $derived(getWinRateColor(wr));
    const fColor = $derived(
        pilot.faction ? getFactionColor(pilot.faction) : undefined,
    );
    const fChar = $derived(
        pilot.faction ? getFactionChar(pilot.faction) : undefined,
    );
</script>

{#if viewMode === "grid"}
    <div
        class="bg-terminal-panel border border-border-dark rounded-xl overflow-hidden hover:border-primary/40 transition-all duration-300 hover:scale-[1.02] hover:z-10 flex flex-col relative h-full group"
    >
        <!-- Card Image -->
        {#if showImage}
            <div
                class="relative w-full h-[200px] overflow-hidden bg-[#050505] flex-shrink-0 flex items-center justify-center p-2"
            >
                {#if pilot.image}
                    <img
                        src={pilot.image}
                        alt={pilot.name}
                        class="max-w-full max-h-full object-contain drop-shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-transform duration-500 group-hover:scale-110"
                        loading="lazy"
                    />
                {:else}
                    <!-- Placeholder fallback using X-Wing Font Ship Icon -->
                    <StatIcon
                        type={pilot.ship_xws || ""}
                        size="5rem"
                        color="rgba(255,255,255,0.05)"
                        isShip={true}
                    />
                {/if}
            </div>
        {/if}

        <!-- Info Section -->
        <div class="p-4 flex-1 flex flex-col justify-between">
            <!-- Name + Ship Badge -->
            <div class="mb-4">
                {#if showName}
                    <h3
                        class="text-base font-sans font-bold text-primary leading-tight flex items-center justify-between gap-2 w-full"
                        title={pilot.name}
                    >
                        <div class="flex items-center gap-2 overflow-hidden">
                            <div
                                class="flex-shrink-0 w-6 h-6 rounded-full bg-white/5 flex items-center justify-center border border-white/10"
                            >
                                <StatIcon
                                    type={pilot.ship_xws || ""}
                                    size="1rem"
                                    color="white"
                                    isShip={true}
                                />
                            </div>
                            <span class="truncate">{pilot.name}</span>
                        </div>
                        {#if fChar}
                            <span
                                class="font-xwing text-lg drop-shadow-md opacity-90 flex-shrink-0"
                                style="color: {fColor}; filter: brightness(1.2);"
                            >
                                {fChar}
                            </span>
                        {/if}
                    </h3>
                {/if}
                {#if showShip && pilot.ship_name}
                    <p
                        class="text-[11px] mt-1 font-mono text-secondary/80 uppercase tracking-wider line-clamp-1"
                        title={pilot.ship_name}
                    >
                        {pilot.ship_name}
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
                            >{pilot.games ?? 0}</span
                        >
                        <span class="text-[9px] font-mono text-secondary"
                            >G</span
                        >
                    </div>
                    <!-- Lists -->
                    <div
                        class="px-1.5 py-0.5 rounded bg-[#ffffff0a] border border-[#ffffff10] flex items-center gap-1"
                    >
                        <span class="text-[10px] font-bold text-primary"
                            >{pilot.lists ?? 0}</span
                        >
                        <span class="text-[9px] font-mono text-secondary"
                            >L</span
                        >
                    </div>
                    <!-- Points -->
                    <div
                        class="px-1.5 py-0.5 rounded bg-emerald-900/30 border border-emerald-500/30 flex items-center gap-1"
                    >
                        <span class="text-[10px] font-bold text-emerald-400"
                            >{pilot.points ?? 0}</span
                        >
                        <span class="text-[9px] font-mono text-emerald-500/80"
                            >PTS</span
                        >
                    </div>
                    <!-- Loadout (XWA Only logic) -->
                    {#if pilot.loadout !== undefined && pilot.loadout !== null}
                        <div
                            class="px-1.5 py-0.5 rounded bg-violet-900/20 border border-violet-500/20 flex items-center gap-1"
                        >
                            <span class="text-[10px] font-bold text-violet-300"
                                >{pilot.loadout}</span
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
        <p>Detailed view for {pilot.name} coming soon...</p>
    </div>
{/if}

<style>
    /* Custom component styles if needed */
</style>
