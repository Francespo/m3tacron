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
    import SortBy from "$lib/components/SortBy.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";
    import { invalidateAll } from "$app/navigation";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    // Alternative-design toggle: `?upg=realsize` renders upgrades at "real
    // card size" (as large as the vertical pilot cards), one per row in a
    // vertical list. Default (no param) = the compact 2-column design.
    let upgradeStyle = $derived(
        typeof window !== "undefined" &&
            new URLSearchParams(window.location.search).get("upg") === "realsize"
            ? "realsize"
            : "compact",
    );

    // Client-side sort state for the Composition section.
    let pilotSortKey = $state<"name" | "cost" | "initiative">("name");
    let pilotSortDir = $state<"asc" | "desc">("asc");

    // Ensure xwingData manifest is loaded so getPilot/getShip/getUpgrade
    // return real human-readable names and card images. Safe to call
    // repeatedly; setSource is a no-op when the requested source is
    // already active and initialized. Wrapped in $effect (same pattern as
    // the squadron detail page) so the initial render subscribes to the
    // store and re-renders once the manifest arrives.
    $effect(() => {
        xwingData.setSource(filters.dataSource as any);
    });

    // The loader streams the stats in via `statsPromise` (non-blocking
    // navigation). Resolve it into reactive state; the {#await} in the
    // template shows a skeleton while it loads. `stats` stays null until
    // resolved so the derived values below have safe defaults.
    let stats = $state<any>(null);
    $effect(() => {
        data.statsPromise.then((s: any) => {
            stats = s;
        });
    });

    function retry() {
        invalidateAll();
    }

    let isXwa = $derived(filters.dataSource === "xwa");
    let win_rate = $derived(
        stats
            ? (stats.games > 0
                  ? ((stats.wins / stats.games) * 100).toFixed(1)
                  : "0.0")
            : "NA",
    );
    let faction = $derived(stats?.faction_xws || "unknown");
    let factionLabel = $derived(getFactionLabel(faction));

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
    let sortedPilots = $derived.by(() => {
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
    });
</script>

<div class="max-w-6xl mx-auto space-y-8">
    <!-- Back link.
         Content source controls now live in the desktop Sidebar /
         mobile nav drawer; removed from this page header. -->
    <BackLink href="/lists" ariaLabel="Back to Lists" />

    {#await data.statsPromise}
        <div class="text-center py-12">
            <p class="text-secondary font-mono text-sm animate-pulse mb-6">
                Loading…
            </p>
            <!-- Loading Skeleton (matches detail layout: header card with
                 metrics, then pilot/composition rows) -->
            <div class="space-y-6 text-left">
                <div
                    class="bg-terminal-panel border border-border-dark rounded-lg p-6 md:p-8 space-y-4"
                >
                    <div
                        class="animate-pulse bg-[#ffffff06] rounded h-5 w-28"
                    ></div>
                    <div
                        class="animate-pulse bg-[#ffffff06] rounded h-10 w-3/4 max-w-md"
                    ></div>
                    <div class="flex gap-2 flex-wrap">
                        {#each Array(4) as _}
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded-md h-6 w-16"
                            ></div>
                        {/each}
                    </div>
                </div>
                <div class="space-y-4">
                    {#each Array(3) as _}
                        <div
                            class="bg-terminal-panel border border-border-dark rounded-lg p-5 flex gap-4"
                        >
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded-lg w-24 h-24 shrink-0 hidden md:block"
                            ></div>
                            <div class="flex-1 space-y-2">
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-5 w-1/3"
                                ></div>
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-3 w-1/2"
                                ></div>
                                <div
                                    class="animate-pulse bg-[#ffffff06] rounded h-12 w-full mt-2"
                                ></div>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    {:then _resolved}
        {#if !stats}
        <div class="text-center py-12">
            <h2 class="text-xl font-sans font-bold text-primary mb-2">
                List Not Found
            </h2>
            <p class="text-secondary font-mono text-sm mb-6">
                We couldn't find data for this list (or it has no recorded games
                in the current filters).
            </p>
            <button
                type="button"
                onclick={retry}
                class="px-4 py-2 border border-border-dark rounded-md text-sm font-sans text-primary hover:bg-[rgba(255,255,255,0.05)] active:bg-[rgba(255,255,255,0.1)] transition-colors"
            >
                Try again
            </button>
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

                <!-- Key Metrics Row: entries→games→winrate→points→loadout -->
                <div
                    class="flex flex-wrap items-center gap-2"
                >
                    <!-- Entries -->
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                    >
                        ENTRIES {(stats as any)?.entries ?? (stats as any)?.count ?? stats.games ?? 0}
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

                    <!-- Win Rate -->
                    <span
                        class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold"
                        style="color: {getWinRateColor(Number(win_rate))};"
                    >
                        WR {win_rate}%
                    </span>

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

            <div class="flex flex-col gap-6">
                {#each sortedPilots as pilot, i (pilot.xws + ":" + i)}
                    {@const pilotData = xwingData.getPilot(pilot.xws)}
                    {@const shipData = xwingData.getShip(pilot.ship_xws)}
                    {@const pilotImg = pilotData?.image}
                    {@const shipIcon = shipData?.icon}
                    {@const shipName = shipData?.name || "Unknown Ship"}
                    {@const shipClassLabel = getShipClassLabel(pilot.ship_xws)}
                    {@const loadout = pilotData?.loadout}
                    {@const upgradeGroups = groupUpgrades(pilot.upgrades ?? [])}
                    {@const pilotName = pilotData?.name || pilot.xws}
                    {@const hasUpgrades = (pilot.upgrades ?? []).length > 0}
                    {@const isLandscape = !!pilotImg && pilotImg.includes("/quickbuilds/")}
                    <div class="p-1.5 md:p-2.5">
                    <div
                        class="group bg-terminal-panel border border-border-dark rounded-lg flex flex-col md:flex-row relative"
                    >
                        <!-- Image stage: the card art floats directly in the
                             capsule — NO container/box/border behind it. The halo
                             is a drop-shadow applied to the art itself. On hover
                             the art scales up and its z-index rises so the halo
                             extends OUTSIDE the capsule, overlaying nearby
                             content as a higher layer. -->
                        <div
                            class="relative md:shrink-0 bg-[#050505] flex items-center justify-center p-3 md:p-4 border-b md:border-b-0 md:border-r border-border-dark w-full md:w-auto"
                        >
                            <a
                                href="/pilot/{pilot.xws}"
                                class="group/image relative block transition-transform duration-300 hover:scale-[1.05] hover:z-30 {isLandscape
                                    ? 'md:h-72 lg:h-80 w-full md:w-auto max-w-full aspect-[1275/739]'
                                    : 'h-72 lg:h-80 w-auto max-w-full aspect-[617/874]'}"
                                title="View {pilotName} details"
                                aria-label="View {pilotName} details"
                            >
                                {#if pilotImg}
                                    <img
                                        src={pilotImg}
                                        alt={pilotName}
                                        class="w-full h-full object-contain drop-shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-all duration-300 hover:drop-shadow-[0_0_36px_rgba(255,255,255,0.35)]"
                                        loading="lazy"
                                    />
                                {:else}
                                    <div
                                        class="w-full h-full flex items-center justify-center"
                                    >
                                        <i
                                            class="xwing-miniatures-ship xwing-miniatures-ship-{(pilotData?.ship || pilot.ship_xws || "unknown").replace(/[^a-z0-9]/g, "")} opacity-70"
                                            style="color: {getFactionColor(faction)}; font-size: 4rem; line-height: 1;"
                                        ></i>
                                    </div>
                                {/if}
                            </a>
                        </div>

                        <!-- Info column: name / ship chassis / ship size / cost
                             (kept as before), plus upgrades for portrait pilots. -->
                        <div
                            class="flex-1 p-5 md:p-6 space-y-4 min-w-0 {isLandscape && !hasUpgrades
                                ? 'flex flex-col justify-center'
                                : ''}"
                        >
                            <!-- Pilot Header -->
                            <div
                                class="flex items-start justify-between gap-4 flex-wrap"
                            >
                                <div class="space-y-2 min-w-0 flex-1">
                                    <div
                                        class="flex items-center gap-2 flex-wrap"
                                    >
                                        <!-- Pilot name link (no hover tooltip —
                                             the card image sits right next to it).
                                             Click still navigates to /pilot/[id]. -->
                                        <a
                                            href="/pilot/{pilot.xws}"
                                            class="text-2xl md:text-3xl font-sans font-bold break-words leading-snug text-primary hover:text-accent transition-colors border-b border-transparent hover:border-accent/50"
                                        >
                                            {pilotName}
                                        </a>
                                        <!-- Cost capsule (initiative is already on
                                             the card art, so it's not shown here).
                                             Cost sits next to the name, beside the
                                             loadout value. -->
                                        <span
                                            class="text-xs font-mono bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-md border border-emerald-500/30 shrink-0"
                                            title="Cost"
                                        >
                                            {Math.max(0, pilot.cost ?? 0)} PT
                                        </span>
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
                            </div>

                            <!-- Upgrades — bipartite capsules (horizontal card
                                 image half + name/cost half, no inner square),
                                 2 columns. Each capsule clicks through to
                                 /upgrade/[id]. -->
                            {#if hasUpgrades}
                                <div
                                    class="pt-4 border-t border-border-dark space-y-3"
                                >
                                    <div
                                        class="text-[10px] font-mono text-secondary uppercase tracking-[0.2em] font-semibold"
                                    >
                                        Upgrades
                                    </div>
                                    {#if Object.keys(upgradeGroups).length > 0}
                                        <!-- Each upgrade capsule has a FIXED height (98px) regardless of how
                                             many lines its name wraps to, so upgrade rows never stretch the
                                             pilot card. All upgrades remain visible. -->
                                        <div
                                            class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 {upgradeStyle === 'realsize'
                                                ? '!grid-cols-1'
                                                : ''}"
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
                                                        class="flex flex-col gap-2"
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
                                                            <div class="p-1">
                                                                <a
                                                                    href="/upgrade/{upgXws}"
                                                                    class="group/upg flex items-stretch bg-terminal-panel border border-border-dark rounded-lg min-w-0 relative"
                                                                    title="View {upgName} details"
                                                                >
                                                                    <!-- Image half: the upgrade art floats directly in the capsule
                                                                         with NO container/border behind it. Compact style: ~25%
                                                                         taller than before (h-36/40). Realsize style: as tall as the
                                                                         vertical pilot cards (h-72/80). On hover the art scales up
                                                                         and its z-index rises so the halo extends OUTSIDE. -->
                                                                    <div
                                                                        class="w-1/2 shrink-0 relative flex items-center justify-center p-2 md:p-2.5 {upgradeStyle === 'realsize'
                                                                            ? 'h-72 lg:h-80'
                                                                            : 'h-36 md:h-40'}"
                                                                    >
                                                                        <div
                                                                            class="relative w-full h-full flex items-center justify-center transition-transform duration-300 hover:scale-[1.1] hover:z-30"
                                                                        >
                                                                            {#if upgImg}
                                                                                <img
                                                                                    src={upgImg}
                                                                                    alt={upgName}
                                                                                    class="w-full h-full object-contain drop-shadow-[0_0_10px_rgba(255,255,255,0.1)] transition-all duration-300 hover:drop-shadow-[0_0_26px_rgba(255,255,255,0.3)]"
                                                                                    loading="lazy"
                                                                                />
                                                                            {:else}
                                                                                <div
                                                                                    class="w-full h-full flex items-center justify-center"
                                                                                >
                                                                                    <i
                                                                                        class="xwing-miniatures-ship text-2xl opacity-60"
                                                                                    ></i>
                                                                                </div>
                                                                            {/if}
                                                                        </div>
                                                                    </div>
                                                                    <!-- Text half: fixed height matching the image half so every
                                                                         capsule is identical regardless of name line count. -->
                                                                    <div
                                                                        class="flex-1 min-w-0 p-2.5 md:p-3 flex flex-col justify-center overflow-hidden {upgradeStyle === 'realsize'
                                                                            ? 'h-72 lg:h-80'
                                                                            : 'h-36 md:h-40'}"
                                                                    >
                                                                        <div
                                                                            class="text-sm md:text-base font-sans font-semibold text-primary transition-colors leading-snug line-clamp-2 break-words"
                                                                        >
                                                                            {upgName}
                                                                        </div>
                                                                        <div
                                                                            class="flex items-center gap-2 shrink-0 mt-1.5"
                                                                        >
                                                                            {#if upgCost !== undefined && upgCost !== null}
                                                                                <span
                                                                                    class="text-xs font-mono bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-md border border-emerald-500/30"
                                                                                    title="Cost"
                                                                                >
                                                                                    {upgCost} PT
                                                                                </span>
                                                                            {:else}
                                                                                <span
                                                                                    class="text-xs font-mono text-secondary/70"
                                                                                    >—</span
                                                                                >
                                                                            {/if}
                                                                        </div>
                                                                    </div>
                                                                </a>
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
    {/await}
</div>
