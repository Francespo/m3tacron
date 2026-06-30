<script lang="ts">
    import {
        getWinRateColor,
        getFactionColor,
        getFactionLabel,
    } from "$lib/data/factions";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { getSlotIcon } from "$lib/data/slots";
    import BackLink from "$lib/components/BackLink.svelte";
    import CardHoverLink from "$lib/components/CardHoverLink.svelte";
    import SortBy from "$lib/components/SortBy.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";
    import type { PageData } from "./$types";

    export let data: PageData;

    // Client-side sort state for the Composition section.
    // Plain `let` + reassign works in this file's legacy-mode (Svelte 4
    // `export let` + `$:`) reactivity; the SortBy onChange callback
    // reassigns these and the `$:` derived `sortedPilots` recomputes.
    let pilotSortKey: "name" | "cost" | "initiative" = "name";
    let pilotSortDir: "asc" | "desc" = "asc";

    // Eagerly ensure xwingData is loaded (synchronously kick the fetch).
    // The xwingData store is shared across the app, so this no-ops once
    // another page has loaded it.
    xwingData.setSource(filters.dataSource as any);

    $: stats = data.stats;
    $: isXwa = filters.dataSource === "xwa";
    $: win_rate = stats
        ? (stats.games > 0 ? ((stats.wins / stats.games) * 100).toFixed(1) : "0.0")
        : "NA";
    $: faction = stats?.faction_xws || "unknown";
    $: factionLabel = getFactionLabel(faction);

    // Group upgrades by their slot_xws field.
    // Falls back to resolving the slot from the upgrade manifest
    // (sides[0].slots[0]) when slot_xws is empty.
    const groupUpgrades = (upgrades: any[]): Record<string, any[]> => {
        if (!Array.isArray(upgrades)) return {};
        const groups: Record<string, any[]> = {};
        for (const u of upgrades) {
            let slot = (u.slot_xws || "").toLowerCase().trim();
            if (!slot) {
                const upgData = xwingData.getUpgrade(u.xws);
                slot = (upgData?.sides?.[0]?.slots?.[0] || "other").toLowerCase();
            }
            if (!groups[slot]) groups[slot] = [];
            groups[slot].push(u);
        }
        return groups;
    };

    // Human-friendly label for a slot XWS. Title-cases by default with
    // a small map for awkward two-word slot names.
    const SLOT_LABELS: Record<string, string> = {
        forcepower: "Force Power",
        tacticalrelay: "Tactical Relay",
        hardpoint: "Hardpoint",
    };
    const formatSlotName = (slot: string): string => {
        if (!slot) return "Other";
        if (SLOT_LABELS[slot]) return SLOT_LABELS[slot];
        if (slot.length === 0) return "Other";
        return slot.charAt(0).toUpperCase() + slot.slice(1);
    };

    // Resolve a ship's chassis class for the pilot.
    const getShipClassLabel = (shipXws: string): string => {
        if (!shipXws) return "";
        const ship = xwingData.getShip(shipXws);
        if (!ship) return "";
        // Common chassis suffixes used by the manifest.
        const size = ship.size ? `[${ship.size}]` : "";
        return size;
    };

    // Sorted view of stats.pilots driven by pilotSortKey / pilotSortDir.
    // `name` resolves through xwingData so it sorts by the human label;
    // `cost` and `initiative` are numeric and read straight from the
    // pilot payload. Undefined values are coerced to a sort-friendly
    // sentinel (-Infinity) so they sink on desc and float on asc.
    $: sortedPilots = (() => {
        const pilots = (stats && stats.pilots) || [];
        const dir = pilotSortDir === "asc" ? 1 : -1;
        const valueFor = (p: any): number | string => {
            switch (pilotSortKey) {
                case "cost":
                    return typeof p.cost === "number" ? p.cost : 0;
                case "initiative":
                    return typeof p.initiative === "number"
                        ? p.initiative
                        : -1;
                case "name":
                default: {
                    const name = xwingData.getPilot(p.xws)?.name || p.xws || "";
                    return name.toLowerCase();
                }
            }
        };
        return [...pilots].sort((a, b) => {
            const va = valueFor(a);
            const vb = valueFor(b);
            if (typeof va === "string" && typeof vb === "string") {
                return va.localeCompare(vb) * dir;
            }
            return ((va as number) - (vb as number)) * dir;
        });
    })();
</script>

<div class="max-w-6xl mx-auto space-y-8">
    <!-- Back link.
         Content source controls now live in the desktop Sidebar /
         mobile nav drawer; removed from this page header. -->
    <BackLink href="/lists" ariaLabel="Back to Lists" />

    {#if !stats}
        <div class="text-center py-12">
            <h2 class="text-xl font-sans font-bold text-primary mb-2">
                List Not Found
            </h2>
            <p class="text-secondary font-mono text-sm">
                We couldn't find data for this list (or it has no recorded games
                in the current filters).
            </p>
        </div>
    {:else}
        <!-- Header Section -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-6 md:p-8 relative overflow-hidden"
        >
            <!-- Background Glow -->
            <div
                class="absolute -top-32 -right-32 w-[28rem] h-[28rem] rounded-full blur-[100px] pointer-events-none"
                style="background-color: {getFactionColor(faction)}25;"
            ></div>
            <div
                class="absolute -bottom-40 -left-40 w-[24rem] h-[24rem] rounded-full blur-[120px] pointer-events-none opacity-50"
                style="background-color: {getFactionColor(faction)}15;"
            ></div>

            <div class="relative z-10 space-y-6">
                <!-- Title Row -->
                <div class="flex items-start gap-5 flex-wrap">
                    <FactionIcon
                        {faction}
                        size="xl"
                        className="leading-none shrink-0"
                    />
                    <div class="min-w-0 flex-1 space-y-1">
                        <div
                            class="text-[11px] font-mono uppercase tracking-[0.2em] text-secondary"
                            style="color: {getFactionColor(faction)};"
                        >
                            {factionLabel}
                        </div>
                        <h1
                            class="text-3xl md:text-5xl font-sans font-bold text-primary leading-tight break-words"
                        >
                            {stats.name || "Untitled List"}
                        </h1>
                    </div>
                </div>

                <!-- Key Metrics Row -->
                <div
                    class="flex flex-wrap items-center gap-2"
                >
                    <!-- Points -->
                    <span
                        class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-md text-[10px] font-mono font-bold"
                    >
                        PTS {stats.points ?? 0}
                    </span>

                    <!-- Original Points (if different) -->
                    {#if stats.original_points !== undefined && stats.original_points !== null && stats.original_points !== stats.points}
                        <span
                            class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-secondary"
                        >
                            ORIGINAL PTS {stats.original_points}
                        </span>
                    {/if}

                    <!-- Win Rate -->
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold"
                        style="color: {getWinRateColor(Number(win_rate))};"
                    >
                        WR {win_rate}%
                    </span>

                    <!-- Games -->
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                    >
                        GAMES {stats.games ?? 0}
                    </span>

                    <!-- Wins / Losses -->
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                    >
                        W/L <span class="text-emerald-400">{stats.wins ?? 0}</span><span class="text-secondary/60">/</span><span class="text-rose-400/80">{(stats.games ?? 0) - (stats.wins ?? 0)}</span>
                    </span>

                    <!-- Loadout (XWA only) -->
                    {#if isXwa && (stats.total_loadout ?? 0) > 0}
                        <span
                            class="px-1.5 py-0.5 bg-violet-500/20 text-violet-400 border border-violet-500/30 rounded-md text-[10px] font-mono font-bold"
                        >
                            LV {stats.total_loadout}
                        </span>
                    {/if}
                </div>
            </div>
        </div>

        <!-- Pilots / Composition Section -->
        <div class="space-y-4">
            <div class="flex items-center justify-between gap-3 mb-4">
                <h2
                    class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 flex items-baseline gap-2"
                >
                    Composition
                    <span
                        class="text-secondary text-base font-normal"
                        >({(stats.pilots || []).length}
                        pilot{(stats.pilots || []).length === 1 ? "" : "s"})</span
                    >
                </h2>
                <SortBy
                    value={pilotSortKey}
                    direction={pilotSortDir}
                    options={[
                        { value: "name", label: "Name" },
                        { value: "cost", label: "Cost" },
                        { value: "initiative", label: "Initiative" }
                    ]}
                    onChange={(v, d) => {
                        pilotSortKey = v as "name" | "cost" | "initiative";
                        pilotSortDir = d;
                    }}
                />
            </div>

            <div class="flex flex-col gap-5">
                {#each sortedPilots as pilot (pilot.xws)}
                    {@const pilotData = xwingData.getPilot(pilot.xws)}
                    {@const shipData = xwingData.getShip(pilot.ship_xws)}
                    {@const pilotImg = pilotData?.image}
                    {@const shipIcon = shipData?.icon}
                    {@const shipName = shipData?.name || "Unknown Ship"}
                    {@const shipClassLabel = getShipClassLabel(pilot.ship_xws)}
                    {@const loadout = pilotData?.loadout}
                    {@const upgradeGroups = groupUpgrades(pilot.upgrades ?? [])}
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden"
                    >
                        <div class="flex flex-col md:flex-row">
                            <!-- Pilot Image Column -->
                            <div
                                class="md:w-40 md:shrink-0 p-5 md:p-6 flex items-center justify-center bg-[#0a0a0a]/40 border-b md:border-b-0 md:border-r border-border-dark"
                            >
                                <div
                                    class="w-28 h-28 md:w-32 md:h-32 rounded-lg bg-[#0a0a0a] border border-border-dark flex items-center justify-center overflow-hidden shrink-0"
                                >
                                    {#if pilotImg}
                                        <img
                                            src={pilotImg}
                                            alt={pilotData?.name ?? ""}
                                            class="w-full h-full object-contain"
                                            loading="lazy"
                                        />
                                    {:else}
                                        <i
                                            class="xwing-miniatures-ship xwing-miniatures-ship-{(pilotData?.ship || pilot.ship_xws || "unknown").replace(/[^a-z0-9]/g, "")} text-6xl opacity-70"
                                            style="color: {getFactionColor(faction)}"
                                        ></i>
                                    {/if}
                                </div>
                            </div>

                            <!-- Info + Upgrades Column -->
                            <div
                                class="flex-1 p-5 md:p-6 space-y-4 min-w-0"
                            >
                                <!-- Pilot Header -->
                                <div
                                    class="flex items-start justify-between gap-4 flex-wrap"
                                >
                                    <div class="space-y-2 min-w-0 flex-1">
                                        <div
                                            class="flex items-center gap-2 flex-wrap"
                                        >
                                            <CardHoverLink
                                                xws={pilot.xws}
                                                type="pilot"
                                                name={pilotData?.name ||
                                                    pilot.xws}
                                                className="text-xl md:text-2xl font-sans font-bold break-words"
                                            />
                                            {#if pilot.initiative !== undefined && pilot.initiative !== null && pilot.initiative > 0}
                                                <span
                                                    class="text-xs font-mono bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded-md border border-orange-500/30 shrink-0"
                                                    title="Initiative"
                                                >
                                                    I{pilot.initiative}
                                                </span>
                                            {/if}
                                            {#if isXwa && loadout}
                                                <span
                                                    class="text-xs font-mono bg-violet-500/20 text-violet-300 px-2 py-0.5 rounded-md border border-violet-500/30 shrink-0"
                                                    title="Loadout value"
                                                >
                                                    LV {loadout}
                                                </span>
                                            {/if}
                                        </div>

                                        <!-- Ship row -->
                                        <div
                                            class="flex items-center gap-2 text-sm flex-wrap"
                                        >
                                            {#if shipIcon}
                                                <img
                                                    src={shipIcon}
                                                    alt={shipName}
                                                    class="w-5 h-5 object-contain opacity-90 shrink-0"
                                                    loading="lazy"
                                                />
                                            {:else if pilot.ship_xws}
                                                <i
                                                    class="xwing-miniatures-ship xwing-miniatures-ship-{pilot.ship_xws.replace(/[^a-z0-9]/g, "")} text-base opacity-80 shrink-0"
                                                    style="color: {getFactionColor(faction)}"
                                                ></i>
                                            {/if}
                                            <span
                                                class="font-mono text-secondary uppercase tracking-wider font-semibold"
                                                >{shipName}</span
                                            >
                                            {#if shipClassLabel}
                                                <span
                                                    class="font-mono text-secondary/60 text-xs"
                                                    >{shipClassLabel}</span
                                                >
                                            {/if}
                                        </div>
                                    </div>

                                    <!-- Cost -->
                                    <div class="text-right shrink-0">
                                        <div
                                            class="text-[10px] font-mono text-secondary uppercase tracking-wider"
                                        >
                                            Cost
                                        </div>
                                        <div
                                            class="text-2xl md:text-3xl font-mono text-green-400 font-bold leading-none"
                                        >
                                            {Math.max(0, pilot.cost ?? 0)}
                                            <span
                                                class="text-sm text-secondary/60 font-normal"
                                                >PT</span
                                            >
                                        </div>
                                    </div>
                                </div>

                                <!-- Upgrades -->
                                {#if pilot.upgrades && pilot.upgrades.length > 0}
                                    <div
                                        class="pt-4 border-t border-border-dark space-y-3"
                                    >
                                        <div
                                            class="text-[10px] font-mono text-secondary uppercase tracking-[0.2em] font-semibold"
                                        >
                                            Upgrades
                                        </div>
                                        {#if Object.keys(upgradeGroups).length > 0}
                                            <div
                                                class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-3"
                                            >
                                                {#each Object.entries(upgradeGroups) as [slot, upgrades]}
                                                    {@const slotIcon = getSlotIcon(slot)}
                                                    <div class="space-y-2">
                                                        <!-- Slot header -->
                                                        <div
                                                            class="flex items-center gap-1.5"
                                                        >
                                                            <span
                                                                class="font-xwing text-violet-400 text-base leading-none w-4 text-center"
                                                                title={formatSlotName(
                                                                    slot,
                                                                )}
                                                            >
                                                                {slotIcon}
                                                            </span>
                                                            <span
                                                                class="text-[10px] font-mono text-secondary uppercase tracking-wider font-semibold"
                                                            >
                                                                {formatSlotName(
                                                                    slot,
                                                                )}
                                                            </span>
                                                        </div>
                                                        <!-- Upgrades list -->
                                                        <div
                                                            class="flex flex-col gap-1.5"
                                                        >
                                                            {#each upgrades as upgrade}
                                                                {@const upgXws = upgrade.xws}
                                                                {@const upgData = upgXws
                                                                    ? xwingData.getUpgrade(
                                                                          upgXws,
                                                                      )
                                                                    : null}
                                                                {@const upgImg = upgData
                                                                    ?.sides?.[0]
                                                                        ?.image}
                                                                {@const upgName = upgData
                                                                    ?.name ||
                                                                    upgrade.xws}
                                                                {@const upgCost = upgData
                                                                    ?.cost?.value}
                                                                <div
                                                                    class="flex items-center gap-2 bg-terminal-panel border border-border-dark rounded-md px-2 py-1.5 min-w-0"
                                                                >
                                                                    <div
                                                                        class="w-8 h-8 shrink-0 rounded-md bg-[#0a0a0a] border border-border-dark flex items-center justify-center overflow-hidden"
                                                                    >
                                                                        {#if upgImg}
                                                                            <img
                                                                                src={upgImg}
                                                                                alt={upgName}
                                                                                class="w-full h-full object-contain"
                                                                                loading="lazy"
                                                                            />
                                                                        {:else}
                                                                            <i
                                                                                class="xwing-miniatures-ship text-base opacity-60"
                                                                            ></i>
                                                                        {/if}
                                                                    </div>
                                                                <div
                                                                    class="min-w-0 flex-1"
                                                                >
                                                                    <CardHoverLink
                                                                        xws={upgXws}
                                                                        type="upgrade"
                                                                        name={upgName}
                                                                        className="text-sm font-sans truncate"
                                                                    />
                                                                    <div
                                                                        class="text-[10px] font-mono text-secondary/70"
                                                                    >
                                                                        {#if upgCost !== undefined && upgCost !== null}
                                                                            <span
                                                                                class="text-emerald-400"
                                                                                >{upgCost}pt</span
                                                                            >
                                                                        {:else}
                                                                            <span
                                                                                >—</span
                                                                            >
                                                                        {/if}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        {/each}
                                                    </div>
                                                </div>
                                            {/each}
                                        </div>
                                    {/if}
                                </div>
                            {/if}
                        </div>
                    </div>
                    </div>
                {/each}
            </div>
        </div>
    {/if}
</div>
