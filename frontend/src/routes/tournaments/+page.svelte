<script lang="ts">
  import FilterPanel from "$lib/components/FilterPanel.svelte";
  import SortSelector from "$lib/components/SortSelector.svelte";
  import { API_BASE } from "$lib/api";
  import { filters } from "$lib/stores/filters.svelte";
  import { page as currentPage } from "$app/stores";
  import { onDestroy } from "svelte";
  import { createQuerySync } from "$lib/querySync";
  import { getFormatLabel, getFormatColor } from "$lib/data/formats";

  let page = $state(1);
  let sortBy = $state("Date");
  let sortDirection = $state("desc");
  let search = $state("");
  const size = 20;

  let items = $state<any[]>([]);
  let total = $state<number>(0);
  let loadingItems = $state(false);
  let loadError = $state<string | null>(null);
  let requestVersion = 0;

  const querySync = createQuerySync(
    () => $currentPage.url.searchParams.toString(),
    200,
  );
  onDestroy(() => querySync.clear());

  function syncFromUrl() {
    const params = $currentPage.url.searchParams;

    const nextPage = Number(params.get("page") ?? "0") + 1;
    if (Number.isFinite(nextPage) && nextPage > 0 && page !== nextPage) {
      page = nextPage;
    }

    const nextSortBy = params.get("sort_metric") || "Date";
    if (sortBy !== nextSortBy) sortBy = nextSortBy;

    const nextSortDirection = params.get("sort_direction") || "desc";
    if (sortDirection !== nextSortDirection) {
      sortDirection = nextSortDirection;
    }

    const nextSearch = params.get("search") || "";
    if (search !== nextSearch) search = nextSearch;
  }

  async function loadTournaments(
    url: URL,
    expectedVersion: number,
    signal: AbortSignal,
  ) {
    const apiUrl = new URL(`${API_BASE}/tournaments`, url.origin);

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
      throw new Error(`Failed to fetch tournaments (${response.status})`);
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

    loadTournaments(url, expectedVersion, controller.signal)
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

  $effect(() => {
    const params = new URLSearchParams();
    params.set("page", String(page - 1));
    params.set("size", String(size));
    params.set("data_source", filters.dataSource);
    for (const format of filters.selectedFormats)
      params.append("formats", format);
    // Date filters
    if (filters.dateStart) params.set("date_start", filters.dateStart);
    if (filters.dateEnd) params.set("date_end", filters.dateEnd);
    // Location filters
    for (const c of filters.selectedContinents) params.append("continent", c);
    for (const c of filters.selectedCountries) params.append("country", c);
    for (const c of filters.selectedCities) params.append("city", c);
    for (const p of filters.selectedSources) params.append("sources", p);

    params.set("sort_metric", sortBy);
    params.set("sort_direction", sortDirection);
    if (search) params.set("search", search);

    querySync.schedule(params);
  });

  function prevPage() {
    if (page > 1) page--;
  }
  function nextPage() {
    if (page * size < total) page++;
  }
</script>

{#snippet tournamentSorting()}
  <SortSelector
    bind:sortBy
    bind:sortDirection
    options={[
      { value: "Date", label: "Date" },
      { value: "Players", label: "Players" },
      { value: "Name", label: "Name" },
    ]}
  />
{/snippet}

<svelte:head>
  <title>Tournaments | M3taCron</title>
</svelte:head>

<div class="flex min-h-screen">
  <!-- Filter Panel (2nd column) -->
  <FilterPanel extra={tournamentSorting} />

  <!-- Main Content (3rd column) -->
  <main class="flex-1 p-6 md:p-8">
    <h1 class="text-2xl font-sans font-bold text-primary mb-1">Tournaments</h1>
    <p class="text-secondary font-mono text-sm mb-6">
      {total} Tournaments Found
    </p>

    {#if loadingItems}
      <p class="text-xs font-mono text-secondary mb-4 animate-pulse">
        Loading tournaments...
      </p>
    {:else if loadError}
      <p class="text-xs font-mono text-[#fca5a5] mb-4">
        Could not load tournaments: {loadError}
      </p>
    {/if}

    <!-- Tournament Rows -->
    <div class="space-y-2">
      {#each items as t}
        <a
          href="/tournaments/{t.id}"
          class="flex items-center gap-4 bg-terminal-panel border border-border-dark rounded-md px-4 py-3 hover:border-secondary/40 transition-colors group"
        >
          <!-- Format Badge -->
          <div
            class="flex items-center justify-center min-w-[60px] self-stretch text-center"
          >
            <span
              class="text-[10px] font-mono font-bold tracking-wider uppercase"
              style="color: {getFormatColor(t.format)};"
            >
              {getFormatLabel(t.format)}
            </span>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="mb-1.5">
              <h3
                class="text-sm font-sans font-bold text-primary truncate group-hover:text-white"
                title={t.name}
              >
                {t.name}
              </h3>
            </div>
            <div class="flex items-center text-xs font-mono text-secondary">
              <span class="w-[88px] shrink-0" title={t.date}>
                {t.date}
              </span>
              <span class="mx-2 text-secondary/60">•</span>
              <span class="truncate" title={t.location || "Unknown Location"}>
                {t.location || "Unknown Location"}
              </span>
            </div>
          </div>

          <!-- Player Count -->
          <div
            class="w-12 shrink-0 flex flex-col items-center justify-center text-center"
          >
            <span class="text-2xl font-sans font-bold text-primary"
              >{t.players ?? "?"}</span
            >
            <span class="text-[10px] font-mono text-secondary block">PLY</span>
          </div>
        </a>
      {/each}
    </div>

    {#if !loadingItems && !loadError && items.length === 0}
      <p class="text-xs font-mono text-secondary mt-6">
        No tournaments match the current filters.
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
