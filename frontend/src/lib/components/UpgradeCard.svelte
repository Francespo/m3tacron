<script lang="ts">
    /**
     * UpgradeCard.svelte
     * Purpose: High-fidelity Upgrade card component with a strict square layout.
     */
    import { getWinRateColor } from "$lib/data/factions";
    import StatIcon from "./StatIcon.svelte";

    let {
        upgrade,
        viewMode = "grid",
    }: {
        upgrade: any;
        viewMode?: "grid" | "detailed";
    } = $props();

    // Stats calculation
    const wr = $derived(Number(upgrade.win_rate ?? 0));
    const wrColor = $derived(getWinRateColor(wr));
</script>

{#if viewMode === "grid"}
    <div class="w-full aspect-square relative group">
        <div
            class="absolute inset-0 bg-terminal-panel border border-border-dark rounded-xl overflow-hidden hover:border-primary/40 transition-all duration-300 hover:scale-[1.02] hover:z-10 flex flex-col p-3 shadow-lg"
        >
            <!-- Header: Icon + Name -->
            <div class="flex items-start gap-2 mb-2">
                <div
                    class="flex-shrink-0 w-8 h-8 rounded bg-primary/5 border border-primary/10 flex items-center justify-center"
                >
                    <StatIcon type={upgrade.type} size="1.2rem" color="white" />
                </div>
                <div class="flex-1 min-w-0">
                    <h3
                        class="text-sm font-sans font-bold text-primary leading-tight truncate uppercase tracking-tight"
                        title={upgrade.name}
                    >
                        {upgrade.name}
                    </h3>
                    <div class="flex items-center gap-2 mt-0.5">
                        <span class="text-[9px] font-sans text-secondary/60 uppercase tracking-widest">{upgrade.type}</span>
                    </div>
                </div>
            </div>

            <!-- Description (Truncated) -->
            <div class="flex-1 min-h-0 overflow-hidden mb-3">
                <p class="text-[10px] leading-relaxed text-secondary/80 line-clamp-4 italic font-sans">
                    {upgrade.text || "No description available."}
                </p>
            </div>

            <!-- Footer: Stats + Cost -->
            <div class="mt-auto pt-2 border-t border-white/5 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="flex items-center gap-1">
                        <span class="text-[10px] font-bold" style="color: {wrColor}">
                            {isNaN(wr) ? "NA" : wr.toFixed(0) + "%"}
                        </span>
                        <span class="text-[8px] font-sans text-secondary tracking-tighter uppercase">WR</span>
                    </div>
                    <div class="flex items-center gap-1">
                        <span class="text-[10px] font-bold text-primary">{upgrade.games || 0}</span>
                        <span class="text-[8px] font-sans text-secondary tracking-tighter uppercase">G</span>
                    </div>
                </div>

                {#if upgrade.cost}
                    <div class="px-1.5 py-0.5 rounded bg-white/5 border border-white/10">
                        <span class="text-[10px] font-bold text-primary">{upgrade.cost}</span>
                        <span class="text-[8px] font-sans text-secondary ml-0.5 uppercase">pts</span>
                    </div>
                {/if}
            </div>
        </div>
    </div>
{:else}
    <div class="p-4 bg-terminal-panel border border-border-dark rounded-xl">
        <div class="flex items-center gap-3 mb-2">
            <StatIcon type={upgrade.type} size="1.5rem" />
            <h3 class="text-xl font-bold text-primary">{upgrade.name}</h3>
        </div>
        <p class="text-secondary italic">{upgrade.text}</p>
    </div>
{/if}

<style>
    /* Custom component styles */
</style>
