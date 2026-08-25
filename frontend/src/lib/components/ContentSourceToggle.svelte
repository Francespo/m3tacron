<script lang="ts">
    import { filters } from '$lib/stores/filters.svelte';
    import { setDataSource } from '$lib/sync/contentSource';
    let { compact = false }: { compact?: boolean } = $props();
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
    class="inline-flex items-stretch bg-terminal-panel border border-border-dark rounded-md overflow-hidden font-mono select-none {compact ? 'text-[11px]' : ''}"
    role="group"
    aria-label="Content source"
>
    {#if !compact}
    <div class="hidden sm:flex items-center px-2 py-1 text-[10px] uppercase tracking-wider text-secondary border-r border-border-dark bg-[#ffffff03]">[Source]</div>
    {/if}

    <button type="button" onclick={() => setDataSource('xwa')} aria-pressed={filters.dataSource === 'xwa'} class="flex items-center gap-1.5 {compact ? 'px-2 py-1 text-[11px]' : 'px-2.5 py-1 text-xs'} transition-colors border-r border-border-dark cursor-pointer select-none {filters.dataSource === 'xwa' ? 'bg-amber-500/15 text-amber-400 active:bg-amber-500/25' : 'text-secondary hover:text-primary hover:bg-[#ffffff08] active:bg-[#ffffff14]'}">
        <span class="inline-block w-1.5 h-1.5 rounded-full transition-all {filters.dataSource === 'xwa' ? 'bg-amber-400 shadow-[0_0_6px_rgba(245,158,11,0.7)]' : 'bg-transparent border border-border-dark'}" aria-hidden="true"></span>
        XWA
    </button>
    <button type="button" onclick={() => setDataSource('legacy')} aria-pressed={filters.dataSource === 'legacy'} class="flex items-center gap-1.5 {compact ? 'px-2 py-1 text-[11px]' : 'px-2.5 py-1 text-xs'} transition-colors cursor-pointer select-none {filters.dataSource === 'legacy' ? 'bg-violet-500/15 text-violet-400 active:bg-violet-500/25' : 'text-secondary hover:text-primary hover:bg-[#ffffff08] active:bg-[#ffffff14]'}">
        <span class="inline-block w-1.5 h-1.5 rounded-full transition-all {filters.dataSource === 'legacy' ? 'bg-violet-400 shadow-[0_0_6px_rgba(139,92,246,0.7)]' : 'bg-transparent border border-border-dark'}" aria-hidden="true"></span>
        {compact ? 'LGCY' : 'LGCY'}
    </button>

</div>
