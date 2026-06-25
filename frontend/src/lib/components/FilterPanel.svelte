<script lang="ts">
    // Desktop-only sticky filter sidebar (2nd column in 3-col layout).
    // The mobile equivalent lives in `MobileFilterDrawer` in `+layout.svelte`.
    // Both render the same children snippet so per-page filter content stays
    // in one place.
    import ContentSourceToggle from "./ContentSourceToggle.svelte";
    import TournamentFilters from "./TournamentFilters.svelte";
    import ActiveFilters from "./ActiveFilters.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import type { Snippet } from "svelte";

    // Snippet convention: callers pass their page-specific filter content as
    // the default `children` snippet, e.g.
    //   <FilterPanel>
    //     {#snippet children()}
    //       ...page filters...
    //     {/snippet}
    //   </FilterPanel>
    let { children }: { children?: Snippet } = $props();
</script>

<!-- Sticky filter sidebar panel (2nd column in 3-col layout) -->
<aside
    class="hidden lg:flex flex-col w-[280px] min-w-[280px] border-r border-border-dark bg-terminal-bg h-screen sticky top-0 overflow-y-auto p-4 space-y-4"
>
    <!-- 1) Global Header / Source Toggle -->
    <ContentSourceToggle />

    <div class="h-px bg-border-dark"></div>

    <!-- 2) Active Filters (Chips & Global Reset) -->
    <ActiveFilters />

    {#if filters.activeChips.length > 0}
        <div class="h-px bg-border-dark"></div>
    {/if}

    <!-- 3) Global Tournament Formats & Logistics -->
    <TournamentFilters />

    <!-- Page-specific extra filters -->
    {#if children}
        <div class="h-px bg-border-dark"></div>
        {@render children()}
    {/if}
</aside>
