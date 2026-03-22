<script lang="ts">
    /**
     * UpgradeCard.svelte
     * Purpose: High-fidelity Upgrade card component.
     * Replicates the current grid-card aesthetic while allowing for expanded views.
     */
    import { getWinRateColor } from "$lib/data/factions";
    import StatIcon from "./StatIcon.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";

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

    const uData = $derived(xwingData.getUpgrade(upgrade.xws));
    const name = $derived(uData?.name || upgrade.xws);
    const image = $derived(uData?.sides[0]?.image);
    const slot = $derived(uData?.sides[0]?.slots?.[0] || upgrade.slot_xws);

    // Stats calculation
    const games = $derived(upgrade.games_count ?? 0);
    const wins = $derived(upgrade.wins ?? 0);
    const wr = $derived(games > 0 ? (wins / games) * 100 : 0);
    const wrColor = $derived(getWinRateColor(wr));
    const listsCount = $derived(upgrade.list_count ?? upgrade.lists ?? 0);
    const differentListsCount = $derived(
        upgrade.different_lists_count ?? upgrade.different_list_count ?? 0,
    );
    const points = $derived(uData?.cost?.value ?? upgrade.points ?? upgrade.cost ?? 0);
    const slotName = $derived(upgrade.slot_name || slot);
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
                    <!-- Placeholder fallback using X-Wing Font Upgrade Icon -->
                    <StatIcon
                        type={slot || "upgrade"}
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
                        title={name}
                    >
                        <div class="flex items-center gap-1 flex-shrink-0">
                            {#if slot}
                                <div
                                    class="w-6 h-6 rounded bg-white/5 flex items-center justify-center border border-white/10"
                                >
                                    <StatIcon
                                        type={slot}
                                        size="1rem"
                                        color="white"
                                        className="drop-shadow-md opacity-90"
                                        style="filter: brightness(1.1);"
                                    />
                                </div>
                            {/if}
                        </div>
                        <span class="line-clamp-2">{name}</span>
                    </h3>
                {/if}
                {#if showSlot && slotName}
                    <p
                        class="text-[11px] mt-1 font-mono text-secondary/80 uppercase tracking-wider line-clamp-1"
                        title={slotName}
                    >
                        {slotName}
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
                </div>
            {/if}
        </div>
    </div>
{:else}
    <div class="detailed-card">
        <p>Detailed view for {name} coming soon...</p>
    </div>
{/if}

<style>
    /* Custom component styles if needed */
</style>
