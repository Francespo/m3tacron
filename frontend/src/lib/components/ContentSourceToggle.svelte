<script lang="ts">
    import { filters } from '$lib/stores/filters.svelte';
    import { setDataSource, setIncludeEpic } from '$lib/sync/contentSource';
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
        class="flex items-center gap-1.5 px-2.5 py-1 text-xs transition-colors border-r border-border-dark cursor-pointer select-none
            {filters.dataSource === 'xwa'
                ? 'bg-cyan-500/15 text-cyan-400 active:bg-cyan-500/25'
                : 'text-secondary hover:text-primary hover:bg-[#ffffff08] active:bg-[#ffffff14]'}"
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
        class="flex items-center gap-1.5 px-2.5 py-1 text-xs transition-colors border-r border-border-dark cursor-pointer select-none
            {filters.dataSource === 'legacy'
                ? 'bg-purple-500/15 text-purple-400 active:bg-purple-500/25'
                : 'text-secondary hover:text-primary hover:bg-[#ffffff08] active:bg-[#ffffff14]'}"
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

    <!-- Epic modifier toggle. Uses a button so the on/off state toggles cleanly
         and the label reuses the same tinted-bg + colored-text pattern as the source buttons. -->
    <button
        type="button"
        onclick={() => setIncludeEpic(!filters.includeEpic)}
        aria-pressed={filters.includeEpic}
        class="flex items-center gap-1.5 px-2.5 py-1 text-xs cursor-pointer select-none transition-colors
            {filters.includeEpic
                ? 'bg-amber-500/15 text-amber-400 active:bg-amber-500/25'
                : 'text-secondary hover:text-primary hover:bg-[#ffffff08] active:bg-[#ffffff14]'}"
    >
        <span
            class="inline-flex items-center justify-center rounded-[2px] border bg-black w-3 h-3 transition-[background-color,border-color,transform]
                {filters.includeEpic ? 'border-primary' : 'border-border-dark hover:border-primary/50'}"
            aria-hidden="true"
        >
            {#if filters.includeEpic}
                <svg
                    width="8"
                    height="8"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="3.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="text-primary"
                >
                    <path d="M20 6 9 17l-5-5" />
                </svg>
            {/if}
        </span>
        Epic
    </button>
</div>
