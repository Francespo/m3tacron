<script lang="ts">
    import { getFactionColor, getWinRateColor } from "$lib/data/factions";
    import { filters } from "$lib/stores/filters.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { getSlotIcon } from "$lib/data/slots";
    import FactionIcon from "./FactionIcon.svelte";

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

    let listHref = $derived(
        `/list/${encodeURIComponent(list.signature || list.name || list.id)}`,
    );
</script>

<a
    href={listHref}
    class="group flex bg-terminal-panel border border-border-dark border-l-[3px] rounded-lg overflow-hidden hover:border-primary/40 hover:bg-[#ffffff04] transition-colors cursor-pointer block"
    style="border-left: 3px solid {factionColor};"
>
    <!-- Content -->
    <div class="flex-1 p-3 md:p-4 space-y-3 min-w-0">
        <!-- Header: Faction icon + List Name + Stats -->
        <div class="flex items-center justify-between flex-wrap gap-2">
            <!-- Faction Icon and List Name -->
            <div class="flex items-center gap-3 min-w-0 flex-1">
                <FactionIcon
                    faction={list.faction_xws || "unknown"}
                    size="lg"
                    className="shrink-0"
                />
                <span
                    class="text-sm font-sans font-bold text-primary group-hover:text-accent transition-colors truncate"
                >
                    {list.name || "Untitled List"}
                </span>
            </div>

            <!-- Stats Badges (PTS colored emerald, GAMES standardized) -->
            <div class="flex items-center gap-1.5 flex-wrap shrink-0">
                <span
                    class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-md text-[10px] font-mono font-bold"
                >
                    PTS {displayedPoints}
                    {#if displayedPoints !== (list.points ?? 0)}
                        <span class="text-secondary/60 text-[10px] ml-1 font-normal"
                            >(orig. {list.points ?? 0})</span
                        >
                    {:else if list.original_points && list.original_points !== list.points}
                        <span class="text-secondary/60 text-[10px] ml-1 font-normal"
                            >(orig. {list.original_points})</span
                        >
                    {/if}
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

        <!-- Pilots Row -->
        <div class="flex flex-wrap gap-2">
            {#each list.pilots || [] as pilotEntry}
                {@const pilotXws = normalizeXws(pilotEntry.xws)}
                {@const pilot = xwingData.getPilot(pilotXws)}
                {@const pilotSubtitle = pilot?.caption || pilot?.shipAbility?.name}
                <div
                    class="bg-[#ffffff05] border border-[#ffffff08] rounded-md p-2.5 min-w-[220px] flex-1 space-y-1.5"
                >
                    <div class="flex items-start gap-3 min-w-0">
                        <i
                            class="xwing-miniatures-ship xwing-miniatures-ship-{(pilot?.ship ?? '').replace(/[^a-z0-9]/g, '')} text-3xl text-secondary flex-shrink-0"
                            aria-hidden="true"
                        ></i>
                        <div class="flex-1 min-w-0 space-y-1.5">
                            <div>
                                <span
                                    class="text-sm font-sans font-bold text-primary"
                                >
                                    {pilot?.name ?? pilotXws}
                                </span>
                                {#if pilotSubtitle}
                                    <p
                                        class="text-[11px] text-secondary/80 italic leading-tight line-clamp-1"
                                    >
                                        {pilotSubtitle}
                                    </p>
                                {/if}
                            </div>
                            {#if pilotEntry.upgrades?.length > 0}
                                <div class="flex flex-wrap gap-1">
                                    {#each pilotEntry.upgrades as upgEntry}
                                        {@const upgradeXws = normalizeXws(upgEntry.xws)}
                                        {@const upg = xwingData.getUpgrade(upgradeXws)}
                                        {@const slot = upg?.sides?.[0]?.slots?.[0] || 'unknown'}
                                        <span
                                            class="inline-flex items-center gap-0.5 px-1.5 py-0.5 border border-border-dark rounded-md bg-[#00000030] text-[10px] font-mono text-secondary"
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
                            {:else}
                                <div
                                    class="text-[10px] font-mono uppercase tracking-wider text-emerald-400/70"
                                >
                                    Standard Loadout
                                </div>
                            {/if}
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    </div>
</a>
