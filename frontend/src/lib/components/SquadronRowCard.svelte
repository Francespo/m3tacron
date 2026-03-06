<script lang="ts">
    import { getFactionColor, getFactionLabel } from "$lib/data/factions";

    let { list } = $props<{ list: any }>();

    let fColor = $derived(getFactionColor(list.faction_key));

    // Aggregate ships from pilots to display counts
    let ships = $derived(() => {
        const counts: Record<string, { icon: string; count: number }> = {};
        for (const p of list.pilots) {
            if (!counts[p.ship_name]) {
                counts[p.ship_name] = { icon: p.ship_icon, count: 0 };
            }
            counts[p.ship_name].count++;
        }
        return Object.entries(counts)
            .map(([name, data]) => ({
                name,
                icon: data.icon,
                count: data.count,
            }))
            .sort((a, b) => a.name.localeCompare(b.name));
    });
</script>

<a
    href="/squadron/{encodeURIComponent(list.signature || '')}"
    class="flex relative bg-terminal-panel border border-[#ffffff14] rounded-lg overflow-hidden group hover:bg-[rgba(255,255,255,0.02)] transition-colors cursor-pointer block"
    style="border-color: {fColor}11; border-left: 4px solid {fColor};"
>
    <!-- Card Content -->
    <div class="flex-1 p-4 flex flex-col gap-3">
        <!-- Header -->
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
                <span class="font-xwing text-2xl" style="color: {fColor};">
                    {#if list.faction_key === "rebelalliance"}!{:else if list.faction_key === "galacticempire"}@{:else if list.faction_key === "scumandvillainy"}#{:else if list.faction_key === "resistance"}!{:else if list.faction_key === "firstorder"}+{:else if list.faction_key === "galacticrepublic"}/{:else if list.faction_key === "separatistalliance"}.{/if}
                </span>
                <span
                    class="text-sm font-bold font-mono tracking-wide"
                    style="color: {fColor};"
                >
                    {getFactionLabel(list.faction_key)}
                </span>
            </div>

            <!-- Stats Badges -->
            <div class="flex items-center gap-2 font-mono text-xs font-bold">
                <span class="text-primary">[{list.count} LISTS]</span>
                <span
                    class={list.win_rate >= 50
                        ? "text-green-400"
                        : list.win_rate > 0
                          ? "text-orange-400"
                          : "text-gray-400"}
                >
                    [{list.win_rate.toFixed(1)}% WR]
                </span>
                <span class="text-secondary tracking-tight">
                    ({list.games} G)
                </span>
            </div>
        </div>

        <!-- Ships Container -->
        <div class="flex flex-wrap gap-2 items-center">
            {#each ships() as ship}
                <div
                    class="flex items-center bg-[rgba(255,255,255,0.03)] border border-[#ffffff14] rounded px-2 py-1 gap-2"
                >
                    <span class="text-xs font-mono font-bold text-secondary"
                        >{ship.count}x</span
                    >
                    <i
                        class="xwing-miniatures-ship xwing-miniatures-ship-{ship.icon} text-lg text-primary"
                    ></i>
                    <span
                        class="text-xs font-mono text-primary truncate max-w-[120px]"
                        title={ship.name}>{ship.name}</span
                    >
                </div>
            {/each}
        </div>
    </div>
</a>
