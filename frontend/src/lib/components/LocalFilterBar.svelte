<script lang="ts">
    import type { Snippet } from "svelte";
    import { filterSections } from "$lib/stores/filterSections.svelte";
    import { getFactionColor } from "$lib/data/factions";
    const FACTION_GLYPHS: Record<string, string> = {
        rebelalliance: "!",
        galacticempire: "@",
        scumandvillainy: "#",
        resistance: "!",
        firstorder: "+",
        galacticrepublic: "/",
        separatistalliance: ".",
    };
    type Props = {
        id: string;
        label?: string;
        defaultOpen?: boolean;
        activeCount?: number;
        chips?: { key: string; label: string }[];
        onRemoveChip?: (key: string) => void;
        onClear?: () => void;
        children: Snippet;
    };
    let { id, label = "Filters", defaultOpen = false, activeCount = 0, chips = [], onRemoveChip, onClear, children }: Props = $props();
    $effect(() => { filterSections.ensureLoaded(id, defaultOpen); });
    let open = $derived(!filterSections.isCollapsed(id));
    function toggle(){ filterSections.toggle(id); }
    function onKey(e: KeyboardEvent){ if(e.key === "Enter" || e.key === " "){ e.preventDefault(); toggle(); } }
</script>

<div class="relative w-full rounded-xl border border-white/[0.08] bg-terminal-panel/90 backdrop-blur overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.04),0_4px_20px_rgba(0,0,0,0.25)]">
    <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/25 to-transparent transition-opacity duration-200 {open ? 'opacity-100' : 'opacity-0'}" aria-hidden="true"></div>
    <!-- Header: fixed py so label never jumps on open/close -->
    <div
        role="button"
        tabindex="0"
        aria-expanded={open}
        aria-controls={id}
        onclick={toggle}
        onkeydown={onKey}
        class="w-full flex items-center justify-between gap-3 px-4 py-3 text-left cursor-pointer select-none hover:bg-white/[0.02] active:bg-white/[0.04] transition-colors group"
    >
        <span class="flex items-center gap-2.5 min-w-0 flex-1 flex-wrap">
            <!-- Funnel icon: flat, same bg as chevron when idle; white when filters active -->
            <span class="w-7 h-7 rounded-lg border flex items-center justify-center shrink-0 transition-colors {activeCount > 0 ? 'bg-white border-white text-black' : 'bg-black/30 border-white/10 text-secondary group-hover:border-white/20 group-hover:text-primary'}">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
            </span>
            <span class="text-xs font-mono font-bold tracking-[0.14em] uppercase {open ? 'text-primary' : 'text-secondary group-hover:text-primary'} shrink-0 transition-colors">{label}</span>
            {#if activeCount > 0}
                <span class="min-w-5 h-5 px-1.5 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center shrink-0 shadow-sm">{activeCount}</span>
            {/if}
            {#if chips.length > 0}
                <span class="hidden sm:flex flex-wrap gap-1.5 items-center min-w-0" onclick={(e) => e.stopPropagation()} role="presentation">
                    {#each chips.slice(0, 6) as chip}
                        {#if chip.key.startsWith("faction:")}
                            {@const f = chip.key.slice(8)}
                            <button type="button" onclick={(e) => { e.stopPropagation(); if(onRemoveChip) onRemoveChip(chip.key); }} aria-label={`Remove ${chip.label}`} title={chip.label} class="inline-flex items-center justify-center w-7 h-7 rounded-md bg-white border border-white/10 shrink-0 hover:bg-white/90 transition-colors">
                                <span class="font-xwing leading-none text-sm" style="color: {getFactionColor(f)};">{FACTION_GLYPHS[f] ?? "?"}</span>
                            </button>
                        {:else if chip.key.startsWith("ship:")}
                            {@const xws = chip.key.slice(5)}
                            <button type="button" onclick={(e) => { e.stopPropagation(); if(onRemoveChip) onRemoveChip(chip.key); }} aria-label={`Remove ${chip.label}`} title={chip.label} class="inline-flex items-center justify-center w-8 h-8 rounded-md bg-white border border-white/10 shrink-0 hover:bg-white/90 transition-colors">
                                <i class="xwing-miniatures-ship xwing-miniatures-ship-{xws} text-[16px] leading-none text-black"></i>
                            </button>
                        {:else}
                            <span class="inline-flex items-center gap-1 pl-2 pr-1 py-0.5 rounded-full bg-white/[0.08] border border-white/10 text-[11px] font-mono text-primary max-w-[10rem] truncate backdrop-blur">
                                <span class="truncate">{chip.label}</span>
                                {#if onRemoveChip}
                                    <button type="button" onclick={(e) => { e.stopPropagation(); onRemoveChip(chip.key); }} aria-label={`Remove ${chip.label}`} class="ml-0.5 w-4 h-4 rounded-full hover:bg-white/15 inline-flex items-center justify-center shrink-0 transition-colors">
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                                    </button>
                                {/if}
                            </span>
                        {/if}
                    {/each}
                    {#if chips.length > 6}
                        <span class="text-[10px] font-mono text-secondary">+{chips.length - 6}</span>
                    {/if}
                </span>
            {/if}
        </span>
        <span class="flex items-center gap-1.5 shrink-0">
            {#if onClear && activeCount > 0}
                <button type="button" onclick={(e) => { e.stopPropagation(); onClear(); }} class="text-xs font-mono text-secondary hover:text-primary underline underline-offset-2 decoration-white/20 hover:decoration-primary/40 transition-colors">Clear</button>
            {/if}
            <span class="w-7 h-7 rounded-lg border flex items-center justify-center shrink-0 transition-all duration-200 {open ? 'rotate-180 bg-white border-white text-black shadow-sm' : 'bg-black/30 border-white/10 text-secondary group-hover:border-white/20 group-hover:text-primary'}">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
            </span>
        </span>
    </div>
    {#if open}
        <div id={id} class="px-4 sm:px-5 pb-5 pt-4 border-t border-white/[0.06] bg-gradient-to-b from-black/30 via-black/20 to-black/10">
            {@render children()}
        </div>
    {/if}
</div>
