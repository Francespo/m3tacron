<script lang="ts">
    import { onMount } from "svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { fetchAllShips, type ShipChassis } from "$lib/api/ships";

    let isOpen = $state(false);
    let search = $state("");
    let ships = $state<ShipChassis[]>([]);
    let isLoading = $state(false);

    let filteredShips = $derived(
        ships.filter(s => s.name.toLowerCase().includes(search.toLowerCase()))
    );

    // Initial load
    onMount(async () => {
        isLoading = true;
        ships = await fetchAllShips(filters.dataSource);
        isLoading = false;
    });

    // Re-fetch if data source changes
    let currentDataSource = $state(filters.dataSource);
    $effect(() => {
        if (currentDataSource !== filters.dataSource) {
            currentDataSource = filters.dataSource;
            fetchAllShips(filters.dataSource).then(data => ships = data);
        }
    });

    function toggleShip(xws: string) {
        if (filters.selectedShips.includes(xws)) {
            filters.selectedShips = filters.selectedShips.filter(s => s !== xws);
        } else {
            filters.selectedShips = [...filters.selectedShips, xws];
        }
    }

    function getFactionColor(factions: string[]): string {
        if (!factions || factions.length === 0) return "#666666";
        const faction = factions[0].toLowerCase().replace(/[\s-]/g, "");
        const colors: Record<string, string> = {
            rebelalliance: "#FF3333", galacticempire: "#2979FF",
            scumandvillainy: "#006400", resistance: "#FF8C00",
            firstorder: "#800020", galacticrepublic: "#E6D690",
            separatistalliance: "#607D8B",
        };
        return colors[faction] || "#666666";
    }
</script>

<div class="border-b border-border-dark">
    <button
        class="w-full py-4 flex items-center justify-between text-left text-sm font-bold tracking-widest text-primary font-mono uppercase focus:outline-none"
        onclick={() => (isOpen = !isOpen)}
        aria-expanded={isOpen}
    >
        <span>Ship Chassis</span>
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="transition-transform duration-200 {isOpen ? 'rotate-180' : ''}"
        >
            <path d="m6 9 6 6 6-6" />
        </svg>
    </button>

    {#if isOpen}
        <div class="pb-4 space-y-3">
            <input
                type="text"
                placeholder="Search ships..."
                class="w-full bg-black border border-border-dark rounded px-3 py-1.5 text-xs font-mono text-primary placeholder-secondary focus:border-primary focus:outline-none"
                bind:value={search}
            />
            
            <div class="max-h-[300px] overflow-y-auto pr-2 space-y-1 custom-scrollbar">
                {#if isLoading && ships.length === 0}
                    <div class="text-xs text-secondary font-mono py-2">Loading...</div>
                {:else if filteredShips.length === 0}
                    <div class="text-xs text-secondary font-mono py-2">No ships found.</div>
                {:else}
                    {#each filteredShips as ship}
                        <label class="flex items-center gap-3 p-1.5 rounded hover:bg-white/5 cursor-pointer group">
                            <input
                                type="checkbox"
                                class="rounded border-border-dark bg-black w-3.5 h-3.5 cursor-pointer flex-shrink-0"
                                checked={filters.selectedShips.includes(ship.xws)}
                                onchange={() => toggleShip(ship.xws)}
                            />
                            
                            <div class="w-6 flex items-center justify-center flex-shrink-0">
                                <i class="xwing-miniatures-ship xwing-miniatures-ship-{ship.xws} text-xl" style="color: {getFactionColor(ship.factions)}"></i>
                            </div>
                            
                            <span class="text-xs font-sans text-secondary group-hover:text-primary transition-colors flex-grow">
                                {ship.name}
                            </span>
                        </label>
                    {/each}
                {/if}
            </div>
        </div>
    {/if}
</div>

<style>
    .custom-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #333;
        border-radius: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
</style>
