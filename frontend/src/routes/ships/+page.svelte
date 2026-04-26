<script lang="ts">
  import FilterPanel from "$lib/components/FilterPanel.svelte";
  import SortSelector from "$lib/components/SortSelector.svelte";
  import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
  import { API_BASE } from "$lib/api";
  import {
    getFactionColor,
    getFactionChar,
    getFactionLabel,
    getWinRateColor,
    ALL_FACTIONS,
  } from "$lib/data/factions";
  import { page as currentPage } from "$app/stores";
  import { onDestroy } from "svelte";
  import { filters } from "$lib/stores/filters.svelte";
  import { xwingData } from "$lib/stores/xwingData.svelte";
  import { createQuerySync } from "$lib/querySync";

  let items = $state<any[]>([]);
  let total = $state<number>(0);
  let loadingItems = $state(false);
  let loadError = $state<string | null>(null);
  let requestVersion = 0;
  let page = $state(1);
  let sortBy = $state("Popularity");
  let sortDirection = $state("desc");
  let selectedFactions = $state<string[]>([]);
  let factionOpen = $state(false);
  const size = 50;
  const querySync = createQuerySync(
    () => $currentPage.url.searchParams.toString(),
    250,
  );
  onDestroy(() => querySync.clear());

  function sameStringArray(a: string[], b: string[]): boolean {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (a[i] !== b[i]) return false;
    }
    return true;
  }

  function syncFromUrl() {
    const params = $currentPage.url.searchParams;

    const nextPage = Number(params.get("page") ?? "0") + 1;
    if (Number.isFinite(nextPage) && nextPage > 0 && page !== nextPage) {
      page = nextPage;
    }

    const nextSortBy = params.get("sort_metric") || "Popularity";
    if (sortBy !== nextSortBy) sortBy = nextSortBy;

    const nextSortDirection = params.get("sort_direction") || "desc";
    if (sortDirection !== nextSortDirection) {
      sortDirection = nextSortDirection;
    }

    const nextFactions = params.getAll("factions");
    if (!sameStringArray(nextFactions, selectedFactions)) {
      selectedFactions = [...nextFactions];
    }
  }

  async function loadShips(
    url: URL,
    expectedVersion: number,
    signal: AbortSignal,
  ) {
    const apiUrl = new URL(`${API_BASE}/ships`, url.origin);
    for (const [key, value] of url.searchParams.entries()) {
      apiUrl.searchParams.append(key, value);
    }

    if (!apiUrl.searchParams.has("page")) {
      apiUrl.searchParams.set("page", String(Math.max(0, page - 1)));
    }
    if (!apiUrl.searchParams.has("size")) {
      apiUrl.searchParams.set("size", String(size));
    }

    const response = await fetch(apiUrl.toString(), { signal });
    if (!response.ok) {
      throw new Error(`Failed to fetch ships (${response.status})`);
    }

    const payload = await response.json();
    if (expectedVersion !== requestVersion) return;

    items = payload?.items ?? [];
    total = Number(payload?.total ?? 0);
  }

  $effect(() => {
    syncFromUrl();
  });

  $effect(() => {
    const url = $currentPage.url;
    const expectedVersion = ++requestVersion;
    const controller = new AbortController();

    loadingItems = true;
    loadError = null;

    loadShips(url, expectedVersion, controller.signal)
      .catch((e) => {
        if (controller.signal.aborted || expectedVersion !== requestVersion)
          return;
        loadError = e instanceof Error ? e.message : String(e);
        items = [];
        total = 0;
      })
      .finally(() => {
        if (expectedVersion === requestVersion) {
          loadingItems = false;
        }
      });

    return () => {
      controller.abort();
    };
  });

  // Trigger URL updates on filter changes
  $effect(() => {
    // Ensure data is active
    xwingData.setSource(filters.dataSource as any);

    const params = new URLSearchParams();
    params.set("page", String(page - 1));
    params.set("size", String(size));
    params.set("data_source", filters.dataSource);
    params.set("sort_metric", sortBy);
    params.set("sort_direction", sortDirection);
    for (const format of filters.selectedFormats)
      params.append("formats", format);
    for (const f of selectedFactions) params.append("factions", f);
    for (const s of filters.selectedShips) params.append("ships", s);
    for (const p of filters.selectedSources) params.append("sources", p);
    for (const c of filters.selectedContinents) params.append("continent", c);
    for (const c of filters.selectedCountries) params.append("country", c);
    for (const c of filters.selectedCities) params.append("city", c);
    if (filters.dateStart) params.set("date_start", filters.dateStart);
    if (filters.dateEnd) params.set("date_end", filters.dateEnd);

    querySync.schedule(params);
  });

  function prevPage() {
    if (page > 1) page--;
  }
  function nextPage() {
    if (page * size < total) page++;
  }

  function toggleFaction(f: string) {
    if (selectedFactions.includes(f)) {
      selectedFactions = selectedFactions.filter((x) => x !== f);
    } else {
      selectedFactions = [...selectedFactions, f];
    }
  }
</script>

{#snippet shipFilters()}
  <div class="space-y-3">
    <span class="text-xs font-bold tracking-widest text-primary font-mono">
      SHIP FILTERS
    </span>

    <SortSelector
      bind:sortBy
      bind:sortDirection
      options={[
        { value: "Popularity", label: "Popularity (Lists)" },
        { value: "Win Rate", label: "Win Rate" },
        { value: "Games", label: "Popularity (Games)" },
        { value: "Name", label: "Name" },
      ]}
    />

    <!-- Faction -->
    <div class="border-b border-border-dark mt-1">
      <button
        class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
        onclick={() => (factionOpen = !factionOpen)}
      >
        <div class="flex items-center gap-2">
          <span class="text-xs font-mono font-bold tracking-wider">
            Faction
          </span>
          {#if selectedFactions.length > 0}
            <span
              class="text-[10px] bg-white/10 text-secondary px-1.5 rounded-full font-mono"
            >
              {selectedFactions.length}
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
          class="transition-transform {factionOpen ? 'rotate-180' : ''}"
          ><path d="m6 9 6 6 6-6" /></svg
        >
      </button>

      {#if factionOpen}
        <div class="pb-3 space-y-1 max-h-[180px] overflow-y-auto pl-2">
          {#each ALL_FACTIONS as f}
            <label
              class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
            >
              <input
                type="checkbox"
                class="rounded border-border-dark bg-black w-3 h-3"
                checked={selectedFactions.includes(f)}
                onchange={() => toggleFaction(f)}
              />
              <span
                class="font-xwing text-sm"
                style="color: {getFactionColor(f)};">{getFactionChar(f)}</span
              >
              <span class="font-mono">{getFactionLabel(f)}</span>
            </label>
          {/each}
        </div>
      {/if}
    </div>

    <ShipChassisFilter {selectedFactions} />
  </div>
{/snippet}

<svelte:head>
  <title>Ships | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
  <FilterPanel extra={shipFilters} />

  <main class="flex-1 p-6 md:p-8">
    <h1 class="text-2xl font-sans font-bold text-primary mb-1">Ships</h1>
    <p class="text-secondary font-mono text-sm mb-6">{total} Ships Found</p>

    {#if loadingItems}
      <p class="text-xs font-mono text-secondary mb-4 animate-pulse">
        Loading ships...
      </p>
    {:else if loadError}
      <p class="text-xs font-mono text-[#fca5a5] mb-4">
        Could not load ships: {loadError}
      </p>
    {/if}

    <!-- Ships Heatmap Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each items as ship}
        {@const shipData = xwingData.getShip(ship.xws)}
        {@const games = ship.games_count ?? 0}
        {@const wins = ship.wins ?? 0}
        {@const wr = games > 0 ? (wins / games) * 100 : 0}
        {@const wrColor = getWinRateColor(wr)}
        {@const lists = ship.list_count ?? 0}
        {@const factionKey = ship.faction_xws ?? "unknown"}
        {@const factionColor = getFactionColor(factionKey)}
        {@const pilotsCount =
          ship.pilots_count ?? xwingData.getPilotCountByShip(ship.xws)}
        <!-- Glow intensity proportional to games (popularity) -->
        {@const glowOpacity = Math.min(0.3, (games / 2000) * 0.3)}

        <a href="/ship/{ship.xws}" class="block group">
          <div
            class="relative bg-terminal-panel border border-border-dark rounded-md p-4 flex flex-col items-center gap-2 hover:border-secondary/50 group-hover:scale-[1.03] group-hover:-translate-y-1 transition-all duration-200"
            style="box-shadow: 0 0 20px {factionColor}{Math.round(
              glowOpacity * 255,
            )
              .toString(16)
              .padStart(2, '0')}; border-color: {factionColor}30;"
          >
            <!-- Faction icon (small, top-right) -->
            <span
              class="absolute top-2 right-2 font-xwing text-sm opacity-50"
              style="color: {factionColor};"
            >
              {getFactionChar(factionKey)}
            </span>

            <!-- Ship Icon (from X-Wing ship font via CSS pseudo-element) -->
            <i
              class="xwing-miniatures-ship xwing-miniatures-ship-{ship.xws
                ? ship.xws.replace(/[^a-z0-9]/g, '')
                : ''} transition-transform"
              style="color: {factionColor}; opacity: 0.9; font-size: 10rem; line-height: 1;"
            ></i>

            <!-- Ship Name -->
            <span
              class="text-xs font-sans font-bold text-primary text-center leading-tight"
            >
              {shipData?.name || ship.xws || "Unknown Ship"}
            </span>

            <!-- Stats Grid (2x2) -->
            <div class="grid grid-cols-2 gap-1 w-full">
              <div class="text-center bg-[#ffffff05] rounded px-1 py-0.5">
                <span
                  class="text-xs font-mono font-bold"
                  style="color: {wrColor};"
                  >{games === 0 ? "NA" : Number(wr).toFixed(1) + "%"}</span
                >
                <span class="text-[9px] font-mono text-secondary block">WR</span
                >
              </div>
              <div class="text-center bg-[#ffffff05] rounded px-1 py-0.5">
                <span class="text-xs font-mono text-primary">{games}</span>
                <span class="text-[9px] font-mono text-secondary block"
                  >Games</span
                >
              </div>
              <div class="text-center bg-[#ffffff05] rounded px-1 py-0.5">
                <span class="text-xs font-mono text-primary">{lists}</span>
                <span class="text-[9px] font-mono text-secondary block"
                  >Lists</span
                >
              </div>
              <div class="text-center bg-[#ffffff05] rounded px-1 py-0.5">
                <span class="text-xs font-mono text-primary">{pilotsCount}</span
                >
                <span class="text-[9px] font-mono text-secondary block"
                  >Pilots</span
                >
              </div>
            </div>
          </div>
        </a>
      {/each}
    </div>

    {#if !loadingItems && !loadError && items.length === 0}
      <p class="text-xs font-mono text-secondary mt-6">
        No ships match the current filters.
      </p>
    {/if}

    <!-- Pagination -->
    {#if total > size}
      <div
        class="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-border-dark"
      >
        <button
          class="px-3 py-1 text-xs font-mono border border-border-dark rounded hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
          onclick={prevPage}
          disabled={page <= 1}
        >
          ← Prev
        </button>
        <span class="text-xs font-mono text-secondary">Page {page}</span>
        <button
          class="px-3 py-1 text-xs font-mono border border-border-dark rounded hover:bg-[#ffffff08] text-secondary hover:text-primary transition-colors disabled:opacity-30"
          onclick={nextPage}
          disabled={page * size >= total}
        >
          Next →
        </button>
      </div>
    {/if}
  </main>
</div>
