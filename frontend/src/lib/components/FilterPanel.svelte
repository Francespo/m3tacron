<script lang="ts">
    import ContentSourceToggle from "./ContentSourceToggle.svelte";
    import TournamentFilters from "./TournamentFilters.svelte";
    import ActiveFilters from "./ActiveFilters.svelte";
    import type { Snippet } from "svelte";

    let { extra }: { extra?: Snippet } = $props();
</script>

<!-- Sticky filter sidebar panel (2nd column in 3-col layout) -->
<aside
    class="hidden lg:flex flex-col w-[280px] min-w-[280px] border-r border-border-dark bg-terminal-bg h-screen sticky top-0 overflow-y-auto p-4 space-y-4"
>
    <!-- 1) Global Header / Source Toggle -->
    <ContentSourceToggle />

    <!-- 2) Active Filters (Chips & Global Reset) -->
    <ActiveFilters />

    <!-- 3) Global Tournament Formats & Logistics -->
    <TournamentFilters />

    <!-- Page-specific extra filters -->
    {#if extra}
        {@render extra()}
    {/if}
</aside>
