<script lang="ts">
    import { onMount } from "svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { fetchAllShips, type ShipChassis } from "$lib/api/ships";
    import Toggle from "./Toggle.svelte";
    import FactionIcon from "./FactionIcon.svelte";
    import FilterAnyAllToggle from "./FilterAnyAllToggle.svelte";

    /** Page-local selected factions — hides ships not playable in these factions. */
    let { selectedFactions = [], showModeToggle = true }: { selectedFactions?: string[]; showModeToggle?: boolean } = $props();

    let isOpen = $state(true);
    let search = $state("");
    let ships = $state<ShipChassis[]>([]);
    let isLoading = $state(false);

    // Filter by search text AND by active factions
    let filteredShips = $derived.by(() => {
        let result = ships;

        // Text search
        if (search) {
            const q = search.toLowerCase();
            result = result.filter((s) => s.name.toLowerCase().includes(q));
        }

        // Faction reactivity: hide chassis not playable in any selected faction
        if (selectedFactions.length > 0) {
            result = result.filter((s) =>
                s.factions.some((f) => selectedFactions.includes(f)),
            );
        }

        return result;
    });

    // Initial load
    onMount(async () => {
        isLoading = true;
        ships = await fetchAllShips(filters.dataSource);
        isLoading = false;
    });

    // Re-fetch when data source changes
    let currentDataSource = $state(filters.dataSource);
    $effect(() => {
        if (currentDataSource !== filters.dataSource) {
            currentDataSource = filters.dataSource;
            fetchAllShips(filters.dataSource).then((data) => (ships = data));
        }
    });

    function toggleShip(xws: string) {
        if (filters.selectedShips.includes(xws)) {
            filters.selectedShips = filters.selectedShips.filter(
                (s) => s !== xws,
            );
        } else {
            filters.selectedShips = [...filters.selectedShips, xws];
        }
    }

    /** How many are currently selected? */
    let selectedCount = $derived(filters.selectedShips.length);
    let autoShow = $derived(selectedCount > 1);
    let effectiveShow = $derived(showModeToggle && autoShow);
</script>

<div class="relative rounded-xl border border-white/5 bg-black/20 overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] w-full self-start h-fit">
    <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
    <button type="button" onclick={() => (isOpen = !isOpen)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
        <span class="flex items-center gap-1.5 text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">
            <span>Ship Chassis</span>
            {#if selectedCount > 0}
                <span class="min-w-5 h-5 px-1 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center">{selectedCount}</span>
            {/if}
        </span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {isOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
    </button>
        {#if isOpen}<div class="px-3.5 pb-3.5 pt-1 space-y-3">
            {#if effectiveShow}<div class="flex items-center justify-between gap-2 flex-wrap">
                <FilterAnyAllToggle bind:value={filters.shipFilterMode} label="Match" />
            </div>{/if}
            <input
                type="text"
                placeholder="Search ships..."
                class="w-full bg-black border border-border-dark rounded-md px-2 py-1.5 text-xs font-mono text-primary placeholder-secondary focus:border-primary focus:outline-none"
                bind:value={search}
            />

            <div
                class="grid gap-1 max-h-[220px] overflow-y-auto custom-scrollbar pr-1"
            >
                {#if isLoading && ships.length === 0}
                    <div class="space-y-1.5">
                        {#each Array(3) as _}
                            <div
                                class="animate-pulse bg-[#ffffff06] rounded h-4 w-full"
                            ></div>
                        {/each}
                    </div>
                {:else if filteredShips.length === 0}
                    <div class="text-xs text-secondary font-mono">
                        No ships match.
                    </div>
                {:else}
                    {#each filteredShips as ship (ship.xws)}
                        <label
                            class="grid cursor-pointer text-xs text-secondary hover:text-primary group min-w-0 w-full" style="grid-template-columns: 14px 22px minmax(0, 1fr) auto; column-gap: 0.5rem; align-items: center;"
                        >
                            <Toggle
                                size="xs"
                                ariaLabel={`Toggle ship ${ship.name}`}
                                checked={filters.selectedShips.includes(ship.xws)}
                                onchange={() => toggleShip(ship.xws)}
                            />
                            <span class="w-[22px] h-[14px] inline-flex items-center justify-center leading-none shrink-0">
                                <i class="xwing-miniatures-ship xwing-miniatures-ship-{ship.xws} text-sm leading-none"></i>
                            </span>
                            <span class="font-mono truncate text-xs text-left min-w-0">{ship.name}</span>
                            <span class="flex items-center gap-0.5 justify-end shrink-0">
                                {#each ship.factions as faction}
                                    <FactionIcon faction={faction} size="sm" className="drop-shadow-sm opacity-90" />
                                {/each}
                            </span>
                        </label>
                    {/each}
                {/if}
            </div>
        </div>{/if}
</div>

<style>
    .chassis-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .chassis-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .chassis-scrollbar::-webkit-scrollbar-thumb {
        background: #333;
        border-radius: 4px;
    }
    .chassis-scrollbar::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
</style>
