<script lang="ts">
  import { onMount } from "svelte";
  import { filters } from "$lib/stores/filters.svelte";
  import { fetchShipOptionsPage, type ShipChassis } from "$lib/api/ships";
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
  let isLoadingMore = $state(false);
  let hasLoaded = $state(false);
  let hasMore = $state(false);
  let currentPage = $state(0);

  const PAGE_SIZE = 80;
  let requestVersion = 0;
  let refreshDebounce: ReturnType<typeof setTimeout> | null = null;

  function normalizeFaction(value: string): string {
    return value.toLowerCase().replace(/\s|-/g, "");
  }

  function getQueryKey(): string {
    const normalizedFactions = [...selectedFactions]
      .map(normalizeFaction)
      .sort()
      .join(",");
    return `${filters.dataSource}|${search.trim().toLowerCase()}|${normalizedFactions}`;
  }

  async function loadPage(page: number, reset = false) {
    const thisRequestVersion = ++requestVersion;
    if (reset) {
      isLoading = true;
    } else {
      isLoadingMore = true;
    }

    try {
      const response = await fetchShipOptionsPage(
        filters.dataSource,
        page,
        PAGE_SIZE,
        search,
        selectedFactions,
      );

      if (thisRequestVersion !== requestVersion) {
        return;
      }

      if (reset) {
        ships = response.items;
      } else {
        const seen = new Set(ships.map((s) => s.xws));
        const nextItems = response.items.filter((s) => !seen.has(s.xws));
        ships = [...ships, ...nextItems];
      }

      currentPage = page;
      hasMore = response.has_more;
      hasLoaded = true;
    } finally {
      if (thisRequestVersion !== requestVersion) {
        return;
      }

      if (reset) {
        isLoading = false;
      } else {
        isLoadingMore = false;
      }
    }
  }

  async function loadInitial(force = false) {
    if (hasLoaded && !force) {
      return;
    }

    ships = [];
    hasMore = false;
    currentPage = 0;
    await loadPage(0, true);

    // Prefetch one extra chunk in background so users see quick progressive fill.
    if (hasMore) {
      void loadPage(1, false);
    }
  }

  let filteredShips = $derived(ships);

  // Initial load only when already needed (selected chips from URL/history)
  onMount(() => {
    if (filters.selectedShips.length > 0) {
      void loadInitial(true);
    }
  });

  // Re-fetch when data source changes
  let currentDataSource = $state(filters.dataSource);
  $effect(() => {
    if (currentDataSource !== filters.dataSource) {
      currentDataSource = filters.dataSource;
      hasLoaded = false;
      ships = [];
      hasMore = false;
      if (isOpen || filters.selectedShips.length > 0) {
        void loadInitial(true);
      }
    }
  });

  // Defer ship chassis fetch until the panel is actually opened.
  $effect(() => {
    if (isOpen && !hasLoaded && !isLoading) {
      void loadInitial();
    }
  });

  $effect(() => {
    const queryKey = getQueryKey();
    if (!isOpen) {
      return;
    }

    if (refreshDebounce) {
      clearTimeout(refreshDebounce);
      refreshDebounce = null;
    }

    refreshDebounce = setTimeout(() => {
      void loadInitial(true);
    }, 220);

    return () => {
      if (refreshDebounce) {
        clearTimeout(refreshDebounce);
        refreshDebounce = null;
      }
    };
  });

  async function loadMore() {
    if (!hasMore || isLoading || isLoadingMore) {
      return;
    }
    await loadPage(currentPage + 1, false);
  }

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
              class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary group"
            >
              <!-- Toggle checkbox -->
              <input
                type="checkbox"
                class="rounded border-border-dark bg-black w-3 h-3 flex-shrink-0"
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
          {/each}

          {#if isLoadingMore}
            <div class="text-[11px] text-secondary font-mono py-1">
              Loading more ships...
            </div>
          {:else if hasMore}
            <button
              class="w-full text-[11px] font-mono py-1.5 rounded border border-border-dark text-secondary hover:text-primary hover:border-primary/30 transition-colors"
              onclick={loadMore}
            >
              Load more ships
            </button>
          {/if}
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
