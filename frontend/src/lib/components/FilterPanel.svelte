<script lang="ts">
    import ContentSourceToggle from "./ContentSourceToggle.svelte";
    import TournamentFilters from "./TournamentFilters.svelte";
    import ActiveFilters from "./ActiveFilters.svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { page } from "$app/stores";
    import type { Snippet } from "svelte";

    let {
        extra,
        mobileOpen = $bindable(false),
        showMobileTrigger = true,
    }: {
        extra?: Snippet;
        mobileOpen?: boolean;
        showMobileTrigger?: boolean;
    } = $props();

    function closeMobileFilters() {
        mobileOpen = false;
    }

    $effect(() => {
        $page.url.pathname;
        closeMobileFilters();
    });

    $effect(() => {
        if (typeof document === "undefined") return;
        document.body.classList.toggle("mobile-filters-open", mobileOpen);
        return () => {
            document.body.classList.remove("mobile-filters-open");
        };
    });

    $effect(() => {
        if (typeof window === "undefined" || !mobileOpen) return;

        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                closeMobileFilters();
            }
        };

        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    });
</script>

{#snippet panelContent()}
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
    {#if extra}
        <div class="h-px bg-border-dark"></div>
        {@render extra()}
    {/if}
{/snippet}

<!-- Sticky filter sidebar panel (2nd column in 3-col layout) -->
<aside
    class="hidden lg:flex flex-col w-[280px] min-w-[280px] border-r border-border-dark bg-terminal-bg h-screen sticky top-0 overflow-y-auto p-4 space-y-4"
>
    {@render panelContent()}
</aside>

{#if showMobileTrigger}
    <button
        type="button"
        class="lg:hidden fixed bottom-4 right-4 z-[115] min-h-11 px-4 rounded border border-border-dark bg-terminal-panel text-primary font-mono text-xs tracking-wider uppercase shadow-[0_8px_30px_rgba(0,0,0,0.6)]"
        onclick={() => (mobileOpen = true)}
        aria-controls="mobile-filter-panel"
        aria-expanded={mobileOpen}
        aria-label="Open filters"
    >
        Filters
    </button>
{/if}

<div
    class="lg:hidden fixed inset-0 z-[125] transition-opacity duration-200 {mobileOpen
        ? 'pointer-events-auto'
        : 'pointer-events-none'}"
    aria-hidden={!mobileOpen}
>
    <button
        type="button"
        class="absolute inset-0 bg-black/70 transition-opacity duration-200 {mobileOpen
            ? 'opacity-100'
            : 'opacity-0'}"
        onclick={closeMobileFilters}
        aria-label="Close filters"
    ></button>

    <aside
        id="mobile-filter-panel"
        class="absolute right-0 top-0 h-[100dvh] w-[min(90vw,340px)] bg-terminal-bg border-l border-border-dark transition-transform duration-200 ease-out flex flex-col {mobileOpen
            ? 'translate-x-0'
            : 'translate-x-full'}"
    >
        <div class="h-14 px-3 border-b border-border-dark flex items-center justify-between">
            <span class="text-primary font-mono text-xs font-bold tracking-widest"
                >FILTERS</span
            >
            <button
                type="button"
                onclick={closeMobileFilters}
                aria-label="Close filters"
                class="min-h-11 min-w-11 inline-flex items-center justify-center rounded border border-border-dark text-secondary hover:text-primary hover:bg-white/5"
            >
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
                >
                    <path d="M18 6 6 18"></path>
                    <path d="m6 6 12 12"></path>
                </svg>
            </button>
        </div>

        <div class="flex-1 overflow-y-auto p-4 space-y-4">
            {@render panelContent()}
        </div>
    </aside>
</div>
