<script lang="ts">
  import FilterPanel from "$lib/components/FilterPanel.svelte";
  import SortSelector from "$lib/components/SortSelector.svelte";
  import ListRowCard from "$lib/components/ListRowCard.svelte";
  import { API_BASE } from "$lib/api";
  import {
    ALL_FACTIONS,
    getFactionLabel,
    getFactionColor,
    getFactionChar,
  } from "$lib/data/factions";
  import { page as currentPage } from "$app/stores";
  import { onDestroy } from "svelte";
  import { filters } from "$lib/stores/filters.svelte";
  import ShipChassisFilter from "$lib/components/ShipChassisFilter.svelte";
  import { xwingData } from "$lib/stores/xwingData.svelte";
  import { createQuerySync } from "$lib/querySync";

  let page = $state(1);
  let sortBy = $state("Games");
  let sortDirection = $state("desc");
  let selectedFactions = $state<string[]>([]);
  let factionOpen = $state(false);
  let minGames = $state(3);
  let items = $state<any[]>([]);
  let total = $state<number>(0);
  let loadingItems = $state(false);
  let loadError = $state<string | null>(null);
  let requestVersion = 0;

  const size = 20;
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

    const nextSortBy = params.get("sort_metric") || "Games";
    if (sortBy !== nextSortBy) sortBy = nextSortBy;

    const nextSortDirection = params.get("sort_direction") || "desc";
    if (sortDirection !== nextSortDirection) {
      sortDirection = nextSortDirection;
    }

    const nextMinGames = Number(params.get("min_games") ?? "3");
    if (
      Number.isFinite(nextMinGames) &&
      nextMinGames > 0 &&
      minGames !== nextMinGames
    ) {
      minGames = nextMinGames;
    }

    const nextFactions = params.getAll("factions");
    if (!sameStringArray(nextFactions, selectedFactions)) {
      selectedFactions = [...nextFactions];
    }
  }

  async function fetchLists(url: URL, signal: AbortSignal) {
    const apiUrl = new URL(`${API_BASE}/lists`, url.origin);
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
      throw new Error(`Failed to fetch lists: ${response.status}`);
    }

    return response.json();
  }

  async function loadLists(
    url: URL,
    expectedVersion: number,
    signal: AbortSignal,
  ) {
    try {
      const payload = await fetchLists(url, signal);
      if (expectedVersion !== requestVersion) return;
      items = payload?.items ?? [];
      total = Number(payload?.total ?? 0);
      return;
    } catch (e) {
      if (signal.aborted) return;
      console.warn("Primary lists fetch failed, retrying same-origin /api", e);
    }

    const fallbackUrl = new URL("/api/lists", url.origin);
    for (const [key, value] of url.searchParams.entries()) {
      fallbackUrl.searchParams.append(key, value);
    }
    if (!fallbackUrl.searchParams.has("page")) {
      fallbackUrl.searchParams.set("page", String(Math.max(0, page - 1)));
    }
    if (!fallbackUrl.searchParams.has("size")) {
      fallbackUrl.searchParams.set("size", String(size));
    }

    const fallbackResponse = await fetch(fallbackUrl.toString(), { signal });
    if (!fallbackResponse.ok) {
      throw new Error(
        `Fallback lists fetch failed: ${fallbackResponse.status}`,
      );
    }

    const fallbackPayload = await fallbackResponse.json();
    if (expectedVersion !== requestVersion) return;
    items = fallbackPayload?.items ?? [];
    total = Number(fallbackPayload?.total ?? 0);
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

    loadLists(url, expectedVersion, controller.signal)
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

  // Re-fetch when local filters change
  $effect(() => {
    // Ensure data is active
    xwingData.setSource(filters.dataSource as any);

    const params = new URLSearchParams();
    params.set("page", String(page - 1));
    params.set("size", String(size));
    params.set("sort_metric", sortBy);
    params.set("sort_direction", sortDirection);
    params.set("min_games", String(minGames));
    params.set("data_source", filters.dataSource);

    for (const f of selectedFactions) params.append("factions", f);
    for (const s of filters.selectedShips) params.append("ships", s);
    for (const format of filters.selectedFormats)
      params.append("formats", format);
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

{#snippet listFilters()}
  <div class="space-y-3">
    <span class="text-xs font-bold tracking-widest text-primary font-mono">
      LIST FILTERS
    </span>

    <SortSelector
      bind:sortBy
      bind:sortDirection
      options={[
        { value: "Games", label: "Popularity (Games)" },
        { value: "Win Rate", label: "Win Rate" },
        { value: "Points Cost", label: "Points" },
      ]}
    />

    <!-- Min Games -->
    <div class="space-y-1">
      <span class="text-xs font-mono font-bold tracking-wider text-secondary"
        >Min Games</span
      >
      <input
        type="number"
        min="1"
        class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none"
        bind:value={minGames}
      />
    </div>

    <!-- Faction Checkboxes -->
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
        <div class="pb-3 space-y-1 max-h-[200px] overflow-y-auto pl-2">
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
                style="color: {getFactionColor(f)};"
              >
                {getFactionChar(f)}
              </span>
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
  <title>Lists | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
  <FilterPanel extra={listFilters} />

  <main class="flex-1 p-6 md:p-8">
    <h1 class="text-2xl font-sans font-bold text-primary mb-1">List Browser</h1>
    <p class="text-secondary font-mono text-sm mb-6">{total} Lists Found</p>

    {#if loadingItems}
      <p class="text-xs font-mono text-secondary mb-4 animate-pulse">
        Loading lists...
      </p>
    {:else if loadError}
      <p class="text-xs font-mono text-[#fca5a5] mb-4">
        Could not load lists: {loadError}
      </p>
    {/if}

    <!-- List Cards -->
    <div class="space-y-3">
      {#each items as list}
        <ListRowCard {list} />
      {/each}
    </div>

    {#if !loadingItems && !loadError && items.length === 0}
      <p class="text-xs font-mono text-secondary mt-6">
        No lists match the current filters.
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
