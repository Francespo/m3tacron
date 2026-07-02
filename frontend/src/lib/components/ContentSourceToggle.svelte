<script lang="ts">
    import { invalidateAll } from '$app/navigation';
    import { page } from '$app/state';
    import { filters } from '$lib/stores/filters.svelte';
    import Toggle from "./Toggle.svelte";

    /**
     * Update the data source AND push it to the URL so the current route's
     * `+page.ts` loader re-runs. Without the URL change, SvelteKit only
     * re-runs loaders on URL changes; mutating the filter store alone is
     * invisible to loaders on routes that read the data source from
     * `url.searchParams` (e.g. pilot / ship / upgrade detail pages).
     *
     * Implementation: we use the browser's `history.replaceState` directly
     * to update the URL bar (so the user sees the new state immediately)
     * and then call `invalidateAll()` to force the loader to re-run with
     * the new search params. We bypass SvelteKit's `goto` because some
     * routes (e.g. the pilot detail page) have their own per-page
     * `$effect` watchers that also call `goto`; running two `goto`s in
     * the same microtask causes SvelteKit to abort both navigations
     * (the tokens race and neither side calls `replaceState`).
     */
    async function setDataSource(value: 'xwa' | 'legacy') {
        filters.dataSource = value;
        // Build the next URL preserving pathname + other params
        // (page, size, tab, sort, formats, …) and mutate just
        // `data_source`.
        const next = new URL(page.url);
        next.searchParams.set('data_source', value);
        // Update the URL bar directly. This is the same call SvelteKit
        // itself makes under the hood; doing it ourselves avoids the
        // race with per-page $effect watchers.
        history.replaceState(history.state, '', next);
        // Re-run the current route's loaders against the new URL.
        await invalidateAll();
    }

    /**
     * Toggle the "include epic" flag and push it to the URL. When false
     * we DELETE the param rather than setting it to "false" so the URL
     * stays compact and matches the rest of the codebase's convention
     * (absent = off).
     */
    async function setIncludeEpic(value: boolean) {
        filters.includeEpic = value;
        const next = new URL(page.url);
        if (value) {
            next.searchParams.set('include_epic', 'true');
        } else {
            next.searchParams.delete('include_epic');
        }
        history.replaceState(history.state, '', next);
        await invalidateAll();
    }
</script>

<!--
    ContentSourceToggle
    -------------------
    Compact segmented control for switching the active game content source
    (XWA / Legacy) and toggling Epic-format inclusion. Designed to match the
    site's terminal aesthetic:

      - Single unified panel (bg-terminal-panel, border-border-dark) so the
        whole control reads as one cohesive unit.
      - `border-r` dividers (not rounded gaps) between segments.
      - font-mono throughout, with the "Source" section header rendered as
        an uppercase label in brackets to feel at home with the rest of the
        terminal-style UI.
      - Active state for XWA / Legacy is shown via a colored bg tint PLUS
        a small "status LED" dot, mirroring how the rest of the app signals
        active modes.
      - Epic is a binary toggle, so the checkbox is rendered as a small
        custom square with a check-mark when active — this makes the
        on/off state legible at a glance instead of relying on a hidden
        native input.
-->
<div
    class="inline-flex items-stretch bg-terminal-panel border border-border-dark rounded-md overflow-hidden font-mono select-none"
    role="group"
    aria-label="Content source"
>
    <!-- Section label: terminal-style bracketed header, sits in its own column
         with a subtle bg to visually separate it from the toggleable items. -->
    <div
        class="flex items-center px-2 py-1 text-[10px] uppercase tracking-wider text-secondary border-r border-border-dark bg-[#ffffff03]"
    >
        [Source]
    </div>

    <!-- XWA -->
    <button
        type="button"
        onclick={() => setDataSource('xwa')}
        aria-pressed={filters.dataSource === 'xwa'}
        class="flex items-center gap-1.5 px-2.5 py-1 text-xs transition-colors border-r border-border-dark cursor-pointer
            {filters.dataSource === 'xwa'
                ? 'bg-cyan-500/15 text-cyan-400'
                : 'text-secondary hover:text-primary hover:bg-[#ffffff08]'}"
    >
        <span
            class="inline-block w-1.5 h-1.5 rounded-full transition-all
                {filters.dataSource === 'xwa'
                    ? 'bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.7)]'
                    : 'bg-transparent border border-border-dark'}"
            aria-hidden="true"
        ></span>
        XWA
    </button>

    <!-- Legacy -->
    <button
        type="button"
        onclick={() => setDataSource('legacy')}
        aria-pressed={filters.dataSource === 'legacy'}
        class="flex items-center gap-1.5 px-2.5 py-1 text-xs transition-colors border-r border-border-dark cursor-pointer
            {filters.dataSource === 'legacy'
                ? 'bg-purple-500/15 text-purple-400'
                : 'text-secondary hover:text-primary hover:bg-[#ffffff08]'}"
    >
        <span
            class="inline-block w-1.5 h-1.5 rounded-full transition-all
                {filters.dataSource === 'legacy'
                    ? 'bg-purple-400 shadow-[0_0_6px_rgba(168,85,247,0.7)]'
                    : 'bg-transparent border border-border-dark'}"
            aria-hidden="true"
        ></span>
        LGCY
    </button>

    <!-- Thin vertical separator (just a divider, no glyph — keeps the panel
         visually clean while still splitting source from modifier). -->
    <div
        class="flex items-center px-1 border-r border-border-dark bg-[#ffffff03]"
        aria-hidden="true"
    ></div>

    <!-- Epic modifier toggle. Uses the canonical Toggle component so the
         on/off state matches the rest of the site, and the label reuses the
         same tinted-bg + colored-text pattern as the source buttons. -->
    <label
        class="flex items-center gap-1.5 px-2.5 py-1 text-xs cursor-pointer transition-colors
            {filters.includeEpic
                ? 'bg-amber-500/15 text-amber-400'
                : 'text-secondary hover:text-primary hover:bg-[#ffffff08]'}"
    >
        <Toggle
            size="xs"
            ariaLabel="Include epic content"
            checked={filters.includeEpic}
            onchange={(e) => setIncludeEpic((e.currentTarget as HTMLInputElement).checked)}
        />
        Epic
    </label>
</div>
