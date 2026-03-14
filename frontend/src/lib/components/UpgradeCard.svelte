<script lang="ts">
    /**
     * UpgradeCard.svelte
     * Purpose: High-fidelity Upgrade card component.
     * Replicates the current grid-card aesthetic while allowing for expanded views.
     */
    import { getWinRateColor } from "$lib/data/factions";
    import StatIcon from "./StatIcon.svelte";

    let {
        upgrade,
        viewMode = "grid",
        showImage = true,
        showName = true,
        showSlot = true,
        showStats = true,
    }: {
        upgrade: any;
        viewMode?: "grid" | "detailed";
        showImage?: boolean;
        showName?: boolean;
        showSlot?: boolean;
        showStats?: boolean;
    } = $props();
    // Stats calculation
    const wr = $derived(Number(upgrade.win_rate ?? 0));
    const wrColor = $derived(getWinRateColor(wr));
</script>

{#if viewMode === "grid"}
    <div
        class="bg-terminal-panel border border-border-dark rounded-xl overflow-hidden hover:border-primary/40 transition-all duration-300 hover:scale-[1.02] hover:z-10 flex flex-col relative aspect-square group"
    >
        <!-- Card Image -->
        {#if showImage}
            <div
                class="relative w-full flex-[2.2] overflow-hidden bg-[#050505] flex items-center justify-center p-2"
            >
                {#if upgrade.image}
                    <img
                        src={upgrade.image}
                        alt={upgrade.name}
                        class="max-w-full max-h-full object-contain drop-shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-transform duration-500 group-hover:scale-110"
                        loading="lazy"
                    />
                {:else}
                    <!-- Placeholder fallback using X-Wing Font Upgrade Icon -->
                    <StatIcon
                        type={upgrade.slot_xws || "upgrade"}
                        size="5rem"
                        color="rgba(255,255,255,0.05)"
                    />
                {/if}
            </div>
        {/if}
        <!-- Info Section -->
        <div class="p-2 flex-1 flex flex-col justify-between">
            <!-- Name + Slot Badge -->
            <div class="mb-1.5">
                {#if showName}
                    <h3
                        class="text-base font-sans font-bold text-primary leading-tight flex items-center gap-2"
                        title={upgrade.name}
                    >
                        <div class="flex items-center gap-1 flex-shrink-0">
                            {#if upgrade.slot_xws}
                                <div
                                    class="w-6 h-6 rounded bg-white/5 flex items-center justify-center border border-white/10"
                                >
                                    <StatIcon
                                        type={upgrade.slot_xws}
                                        size="1rem"
                                        color="white"
                                    />
                                </div>
                            {/if}
                            {#if upgrade.slots && upgrade.slots.length > 1}
                                {#each upgrade.slots.slice(1) as extraSlot}
                                    <div
                                        class="w-6 h-6 rounded bg-white/5 flex items-center justify-center border border-white/10"
                                    >
                                        <StatIcon
                                            type={extraSlot}
                                            size="1rem"
                                            color="white"
                                        />
                                    </div>
                                {/each}
                            {/if}
                        </div>
                        <span class="line-clamp-2">{upgrade.name}</span>
                    </h3>
                {/if}
                {#if showSlot && upgrade.slot_name}
                    <p
                        class="text-[11px] mt-1 font-mono text-secondary/80 uppercase tracking-wider line-clamp-1"
                        title={upgrade.slot_name}
                    >
                        {upgrade.slot_name}
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
                            >{upgrade.games ?? 0}</span
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
                            >{upgrade.lists ?? 0}</span
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
                            >{upgrade.points ?? 0}</span
                        >
                        <span class="text-[9px] font-mono text-emerald-500/80"
                            >PTS</span
                        >
                    </div>
                </div>
            {/if}
        </div>
    </div>
{:else}
    <div class="detailed-card">
        <p>Detailed view for {upgrade.name} coming soon...</p>
    </div>
{/if}

<style>
    /* Custom component styles if needed */
</style>
