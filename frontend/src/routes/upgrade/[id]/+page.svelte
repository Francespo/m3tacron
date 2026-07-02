<script lang="ts">
    import { goto } from "$app/navigation";
    import SortBy from "$lib/components/SortBy.svelte";
    import StatIcon from "$lib/components/StatIcon.svelte";
    import { getWinRateColor } from "$lib/data/factions";
    import { getSlotIcon } from "$lib/data/slots";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import BackLink from "$lib/components/BackLink.svelte";

    let { data } = $props();

    // Static upgrade metadata from the reactive xwing-data manifest.
    // Loaded client-side; falls back to a placeholder when the manifest
    // hasn't been initialized yet (e.g. very first render before
    // xwingData.setSource has resolved).
    const uData = $derived(xwingData.getUpgrade(data.upgradeXws));
    const name = $derived(uData?.name || data.upgradeXws);
    const image = $derived(uData?.sides?.[0]?.image);
    const slotXws = $derived(
        uData?.sides?.[0]?.slots?.[0]?.toLowerCase() || "",
    );
    const description = $derived(uData?.sides?.[0]?.ability || "");
    const title = $derived(uData?.sides?.[0]?.title || name);
    const cost = $derived(uData?.cost?.value ?? 0);
    const limited = $derived(uData?.limited ?? 0);

    // Aggregate stats pulled from the cards/upgrades list row. The
    // backend has no dedicated upgrade-detail endpoint yet, so we read
    // the same shape the /cards page already populates for UpgradeCard.
    // All counts are defensively clamped to >= 0 in case the backend
    // returns null/undefined (e.g. upgrade excluded by format filters).
    const games = $derived(Math.max(0, Number(data.stats?.games_count ?? 0)));
    const wins = $derived(Math.max(0, Number(data.stats?.wins ?? 0)));
    const listsCount = $derived(
        Math.max(0, Number(data.stats?.list_count ?? 0)),
    );
    const differentListsCount = $derived(
        Math.max(0, Number(data.stats?.different_lists_count ?? 0)),
    );
    const wrPct = $derived(games > 0 ? (wins / games) * 100 : 0);
    const wrColor = $derived(getWinRateColor(wrPct));
    const wrDisplay = $derived(games > 0 ? `${wrPct.toFixed(1)}%` : "NA");

    // Sort/filter state for related lists. The backend has no endpoint
    // that returns lists filtered to a single upgrade yet (the
    // `filter_upgrade_id` slot in aggregate_card_stats is defined but
    // not wired to the SQL WHERE clause). The SortBy control is wired
    // up so the UI is in place; once a backend endpoint is added it
    // can be hooked up without touching the surrounding layout.
    let sortBy = $state<string>("Popularity");
    let sortDirection = $state<"asc" | "desc">("desc");

    // Drive the URL ?data_source=... param off the shared filter store
    // and react when it changes (mirrors pilot/[id]/+page.svelte).
    let initialized = $state(false);
    $effect(() => {
        if (initialized) return;
        if (data.ds === "legacy" || data.ds === "xwa") {
            filters.dataSource = data.ds;
        }
        initialized = true;
    });
    $effect(() => {
        if (!initialized) return;
        const ds = filters.dataSource;
        goto(`?data_source=${ds}`, {
            keepFocus: true,
            noScroll: true,
            replaceState: true,
        });
    });

    // Slot icon glyph (or empty string when unknown). font-xwing is the
    // X-Wing Miniatures font set in app.css; the class name follows the
    // pattern xwing-miniatures-font-{slot}.
    const slotIconChar = $derived(getSlotIcon(slotXws));
    const slotLabel = $derived(slotXws ? slotXws.toUpperCase() : "UPGRADE");
</script>

<svelte:head>
    <title>{name} — Upgrade Detail | M3taCron</title>
    <meta
        name="description"
        content="Detailed statistics for the {name} upgrade in X-Wing Miniatures."
    />
</svelte:head>

<div class="min-h-screen p-6 md:p-8 font-sans">
    <!-- Back link.
         Content source controls now live in the desktop Sidebar /
         mobile nav drawer; removed from this page header. -->
    <div class="mb-4">
        <BackLink href="/cards?tab=upgrades" ariaLabel="Back to Cards" />
    </div>

    <!-- Header Section -->
    <div
        class="flex flex-col md:flex-row gap-8 mb-10 items-center bg-terminal-panel border border-border-dark rounded-lg p-6 md:p-8 shadow-lg"
    >
        <!-- Upgrade Image -->
        <div class="flex-shrink-0">
            <div
                class="w-[220px] h-[300px] bg-black/40 rounded-lg border border-white/5 flex items-center justify-center overflow-hidden p-3"
            >
                {#if image}
                    <img
                        src={image}
                        alt={name}
                        class="max-w-full max-h-full object-contain drop-shadow-[0_0_15px_rgba(255,255,255,0.08)]"
                    />
                {:else}
                    <div class="text-center">
                        <StatIcon
                            type={slotXws || "upgrade"}
                            size="3.5rem"
                            color="rgba(255,255,255,0.15)"
                        />
                        <p class="text-secondary font-mono text-xs mt-3">
                            NO IMAGE
                        </p>
                    </div>
                {/if}
            </div>
        </div>

        <!-- Upgrade Info + Stat Badges -->
        <div class="flex-1 min-w-0 w-full">
            <div class="flex items-start gap-3 flex-wrap">
                <!-- Slot Badge (xwing font glyph + label) -->
                <div
                    class="flex items-center gap-2 px-2 py-1 rounded-md bg-white/5 border border-white/10"
                    title={slotLabel}
                >
                    {#if slotIconChar}
                        <i
                            class="font-xwing text-base text-primary"
                            style="line-height:1"
                        >
                            {slotIconChar}
                        </i>
                    {/if}
                    <span class="text-[11px] font-mono text-secondary uppercase tracking-wider">
                        {slotLabel}
                    </span>
                </div>
                <span
                    class="px-2 py-1 text-[11px] font-mono font-bold rounded-md bg-blue-500/20 text-blue-400 border border-blue-500/30"
                >
                    UPGRADE
                </span>
                {#if limited > 0}
                    <span
                        class="px-2 py-1 text-[11px] font-mono font-bold rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    >
                        LIMITED × {limited}
                    </span>
                {/if}
            </div>

            <h1
                class="text-3xl md:text-4xl font-sans font-bold text-primary mt-3"
            >
                {name}
            </h1>
            {#if title && title !== name}
                <p class="text-secondary font-mono text-sm mt-1">
                    {title}
                </p>
            {/if}

            <!-- Stat pills -->
            <div class="flex flex-wrap gap-2 mt-5">
                <span
                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold"
                >
                    WR <span style="color: {wrColor};">{wrDisplay}</span>
                </span>
                <span
                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                >
                    GAMES {games.toLocaleString()}
                </span>
                <span
                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                >
                    LISTS {listsCount.toLocaleString()}
                </span>
                <span
                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-primary"
                >
                    (UNIQUE {differentListsCount.toLocaleString()})
                </span>
                <span
                    class="px-1.5 py-0.5 bg-[#ffffff05] border border-border-dark rounded-md text-[10px] font-mono font-bold text-emerald-400"
                >
                    PTS {cost}
                </span>
            </div>
        </div>
    </div>

    <!-- Description / Card Text -->
    <section class="mb-10">
        <h2
            class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 mb-4 flex items-baseline gap-2"
        >
            <span>Card Text</span>
        </h2>
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
        >
            {#if description}
                <p
                    class="text-primary font-sans text-base leading-relaxed whitespace-pre-line"
                >
                    {description}
                </p>
            {:else}
                <p class="text-secondary font-mono text-sm italic">
                    No card text available.
                </p>
            {/if}
        </div>
    </section>

    <!-- Lists Using This Upgrade (placeholder until backend endpoint exists) -->
    <section class="mb-10">
        <div class="flex items-end justify-between gap-4 flex-wrap">
            <h2
                class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 mb-4 flex items-baseline gap-2"
            >
                <span>Top Lists Using This Upgrade</span>
            </h2>
            <div class="w-full sm:w-72 mb-4">
                <SortBy
                    value={sortBy}
                    direction={sortDirection}
                    options={[
                        { value: "Popularity", label: "Lists" },
                        { value: "Win Rate", label: "Win Rate" },
                        { value: "Games", label: "Games" },
                    ]}
                    onChange={(v, d) => {
                        sortBy = v;
                        sortDirection = d;
                    }}
                />
            </div>
        </div>
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center"
        >
            <p class="text-secondary font-mono text-sm">
                Lists filtered to a single upgrade are not yet available.
            </p>
            <p class="text-secondary font-mono text-xs mt-2 opacity-70">
                The current backend has no endpoint that returns lists
                containing a specific upgrade. A follow-up backend change
                (mirroring the pilot/ship detail endpoints) is required to
                populate this section.
            </p>
        </div>
    </section>

    <!-- Squadrons Using This Upgrade (placeholder) -->
    <section>
        <h2
            class="text-xl font-sans font-bold text-primary uppercase tracking-wider border-b border-border-dark pb-2 mb-4 flex items-baseline gap-2"
        >
            <span>Top Squadrons Using This Upgrade</span>
        </h2>
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-8 text-center"
        >
            <p class="text-secondary font-mono text-sm">
                Squadron data filtered to a single upgrade is not yet
                available.
            </p>
            <p class="text-secondary font-mono text-xs mt-2 opacity-70">
                Same limitation as above — the backend has no per-upgrade
                squadron endpoint yet.
            </p>
        </div>
    </section>
</div>
