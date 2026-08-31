<script lang="ts">
    // Filter sidebar — previously a fixed desktop-only panel (lg+).
    // Now the filter chrome is a right-side drawer on ALL breakpoints
    // (reusing MobileFilterDrawer). This component is kept for
    // backwards-compatibility and as a possible inline variant, but
    // pages no longer mount it as the primary filter surface.
    // The mobile equivalent lives in `MobileFilterDrawer` (rendered by each
    // page). Both render the same two-section structure: a collapsible
    // "data filter" section (TournamentFilters) on top, then a
    // page-specific section below a strong divider. Both share section ids
    // via `FilterSection` so the persisted collapse preference is shared
    // between the desktop panel and the mobile drawer.
    import TournamentFilters from "./TournamentFilters.svelte";
    import ActiveFilters from "./ActiveFilters.svelte";
    import FilterSection from "./FilterSection.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { slugify } from "$lib/stores/filterSections.svelte";
    import type { Snippet } from "svelte";

    type Props = {
        // Page-specific filter content, rendered in the bottom section.
        children?: Snippet;
        // Top-section naming: "Data filter" everywhere except /tournaments,
        // which passes "Tournament filters" (contextual naming).
        dataFilterTitle?: string;
        dataFilterDescription?: string;
        // Bottom-section header; absent -> no bottom section is rendered.
        pageFilterTitle?: string;
    };

    let {
        children,
        dataFilterTitle = "Dataset filters",
        dataFilterDescription = "Tournament filters are applied to the page's input data. The page-specific filters and the tournament filters are complementary — for example, if you filter for tournaments on a list page, only data from tournaments that match your filter is shown.",
        pageFilterTitle,
    }: Props = $props();
</script>

<!-- Sticky filter sidebar panel (2nd column in 3-col layout).
     [scrollbar-gutter:stable] reserves the scrollbar gutter so content
     never shifts sideways when the column overflows. -->
<aside
    class="hidden lg:flex flex-col w-[280px] min-w-[280px] border-r border-border-dark bg-terminal-bg h-screen sticky top-0 overflow-x-hidden overflow-y-auto [scrollbar-gutter:stable] p-4 space-y-4"
>
    <!-- 1) Active Filters (Chips & Global Reset). The XWA / LEGACY / Epic
         content-source controls now live exclusively in the desktop
         Sidebar (and the mobile nav drawer); they were removed from
         here as part of consolidating those controls. -->
    <ActiveFilters />

    {#if filters.activeChips.length > 0}
        <div class="h-px bg-border-dark"></div>
    {/if}

    <!-- 2) Data-scope filters (tournament format, date, source/platform,
         location, tournament-name search). Collapsible; the preference
         persists via FilterSection. -->
    <FilterSection
        id="data"
        label={dataFilterTitle}
        description={dataFilterDescription}
    >
        <TournamentFilters />
    </FilterSection>

    <!-- 3) Page-specific filters, strongly separated from the data section
         above. -->
    {#if pageFilterTitle && children}
        <div class="h-0.5 bg-border-dark mt-3 mb-4"></div>

        <FilterSection
            id={'page:' + slugify(pageFilterTitle)}
            label={pageFilterTitle}
        >
            {@render children()}
        </FilterSection>
    {/if}
</aside>
