<script lang="ts">
    /**
     * PilotCard.svelte
     * Purpose: High-fidelity Pilot card component with a strict square layout.
     */
    import {
        getWinRateColor,
        getFactionColor,
        getFactionChar,
    } from "$lib/data/factions";
    import StatIcon from "./StatIcon.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";

    let {
        pilot,
        viewMode = "grid",
        showImage = true,
    }: {
        pilot: any;
        viewMode?: "grid" | "detailed";
        showImage?: boolean;
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
    <div class="w-full aspect-square relative group">
        <div
            class="absolute inset-0 bg-terminal-panel border border-border-dark rounded-xl overflow-hidden hover:border-primary/40 transition-all duration-300 hover:scale-[1.02] hover:z-10 flex flex-col pt-2"
        >
            <!-- Card Image Container -->
            <div class="relative flex-1 bg-black/40 overflow-hidden mx-2 rounded-lg">
                {#if showImage && pilot.image}
                    <img
                        src={pilot.image}
                        alt={pilot.name}
                        class="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                    />
                {:else}
                    <div class="w-full h-full flex items-center justify-center opacity-10">
                        <StatIcon type={pilot.ship_xws || ""} size="4rem" isShip={true} />
                    </div>
                {/if}
                <div
                    class="absolute inset-0 bg-gradient-to-t from-terminal-panel/80 via-transparent to-transparent"
                ></div>

                <!-- Faction Icon Overlay -->
                <div class="absolute top-2 right-2">
                    <FactionIcon faction={pilot.faction} size="1.1rem" />
                </div>

                <!-- Pilot Initiative -->
                <div
                    class="absolute bottom-2 left-2 flex items-center justify-center w-7 h-7 rounded-full bg-black/90 border border-white/20 text-orange-500 font-bold text-base shadow-lg"
                >
                    {pilot.initiative || 0}
                </div>
            </div>

            <!-- Card Info -->
            <div class="p-3 flex flex-col gap-1">
                <div class="flex items-center justify-between gap-2 overflow-hidden">
                    <h3
                        class="text-sm font-sans font-bold text-primary leading-tight truncate uppercase tracking-tight"
                    >
                        {pilot.name}
                    </h3>
                    {#if pilot.cost}
                        <span class="text-[11px] font-bold text-primary bg-white/5 px-1.5 py-0.5 rounded border border-white/10"
                            >{pilot.cost}</span
                        >
                    {/if}
                </div>

                <div class="flex items-center justify-between mb-1">
                    <span
                        class="text-[10px] font-sans text-secondary/70 uppercase font-medium tracking-wider truncate"
                    >
                        {pilot.ship_name || "Unknown Ship"}
                    </span>
                </div>

                <!-- Stats Bar -->
                <div class="flex items-center justify-between mt-auto">
                    <div class="flex items-center gap-2">
                        {#if pilot.stats}
                            {#each pilot.stats.filter((s) => ["attack", "agility", "hull", "shield"].includes(s.type)) as stat}
                                <div class="flex items-center gap-0.5" title={stat.type}>
                                    <StatIcon type={stat.type} size="0.75rem" />
                                    <span class="text-[10px] font-bold text-primary"
                                        >{stat.value}</span
                                    >
                                </div>
                            {/each}
                        {/if}
                    </div>

                    <!-- Performance mini-badge -->
                    <div class="flex items-center gap-1.5 opacity-60">
                         <span class="text-[9px] font-bold" style="color: {wrColor}">{isNaN(wr) ? "NA" : wr.toFixed(0) + "%"}</span>
                         <span class="text-[9px] font-sans text-secondary">{pilot.games || 0}G</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
{:else}
    <div class="p-4 bg-terminal-panel border border-border-dark rounded-xl">
        <h3 class="text-xl font-bold text-primary mb-2">{pilot.name}</h3>
        <p class="text-secondary">{pilot.ship_name}</p>
    </div>
{/if}

<style>
    /* Custom component styles */
</style>
