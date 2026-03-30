<script lang="ts">
  import { onMount } from "svelte";
  import { filters } from "$lib/stores/filters.svelte";
  import { fetchAllShips, type ShipChassis } from "$lib/api/ships";
  import {
    getFactionColor,
    getFactionChar,
    getFactionLabel,
  } from "$lib/data/factions";

  /** Page-local selected factions — hides ships not playable in these factions. */
  let { selectedFactions = [] }: { selectedFactions?: string[] } = $props();

  let isOpen = $state(false);
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
      filters.selectedShips = filters.selectedShips.filter((s) => s !== xws);
    } else {
      filters.selectedShips = [...filters.selectedShips, xws];
    }
  }

  /** How many are currently selected? */
  let selectedCount = $derived(filters.selectedShips.length);
</script>

<div class="border-b border-border-dark mt-1">
  <button
    class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
    onclick={() => (isOpen = !isOpen)}
  >
    <div class="flex items-center gap-2">
      <span class="text-xs font-mono font-bold tracking-wider">
        Ship Chassis
      </span>
      {#if selectedCount > 0}
        <span
          class="text-[10px] bg-white/10 text-secondary px-1.5 rounded-full font-mono"
        >
          {selectedCount}
        </span>
      {/if}
    </div>
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      class="transition-transform {isOpen ? 'rotate-180' : ''}"
      ><path d="m6 9 6 6 6-6" /></svg
    >
  </button>

  {#if isOpen}
    <div class="pb-3 space-y-2 pl-2">
      <!-- Quick search within chassis list -->
      <input
        type="text"
        placeholder="Search ships..."
        class="w-full bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary placeholder-secondary focus:border-primary focus:outline-none"
        bind:value={search}
      />

      <!-- Scrollable chassis list -->
      <div
        class="max-h-[180px] overflow-y-auto pr-1 space-y-1 chassis-scrollbar"
      >
        {#if isLoading && ships.length === 0}
          <div class="text-xs text-secondary font-mono">Loading...</div>
        {:else if filteredShips.length === 0}
          <div class="text-xs text-secondary font-mono">No ships match.</div>
        {:else}
          {#each filteredShips as ship}
            <label
              class="flex items-center gap-2 py-1.5 cursor-pointer text-xs text-secondary hover:text-primary group"
            >
              <!-- Toggle checkbox -->
              <input
                type="checkbox"
                class="rounded border-border-dark bg-black w-4 h-4 flex-shrink-0"
                checked={filters.selectedShips.includes(ship.xws)}
                onchange={() => toggleShip(ship.xws)}
              />

              <!-- Ship icon (X-Wing miniatures ship font) - Uncolored -->
              <i
                class="xwing-miniatures-ship xwing-miniatures-ship-{ship.xws} text-sm flex-shrink-0"
              ></i>

              <!-- Ship name -->
              <span class="font-mono truncate flex-grow text-xs">
                {ship.name}
              </span>

              <!-- Faction symbols (colored) -->
              <span class="flex items-center gap-0.5 flex-shrink-0">
                {#each ship.factions as faction}
                  <span
                    class="font-xwing text-sm drop-shadow-sm opacity-90"
                    style="color: {getFactionColor(faction)};"
                    title={getFactionLabel(faction)}
                  >
                    {getFactionChar(faction)}
                  </span>
                {/each}
              </span>
            </label>
            {#if false}{/if}
          {/each}
        {/if}
      </div>
    </div>
  {/if}
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
