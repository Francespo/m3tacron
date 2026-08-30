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
    function slotToFont(s: string): string {
        const m: Record<string, string> = {
            "astromech": "astromech", "cannon": "cannon", "cargo": "cargo", "command": "command", "configuration": "config", "crew": "crew", "device": "device", "force power": "forcepower", "gunner": "gunner", "hardpoint": "hardpoint", "hyperdrive": "hardpoint", "illicit": "illicit", "missile": "missile", "modification": "modification", "payload": "device", "sensor": "sensor", "tactical relay": "tacticalrelay", "talent": "talent", "team": "team", "tech": "tech", "title": "title", "torpedo": "torpedo", "turret": "turret",
        };
        return m[s.toLowerCase().trim()] ?? "modification";
    }
    function actionToFont(a: string): string {
        const m: Record<string, string> = {
            "barrel roll": "barrelroll", "boost": "boost", "calculate": "calculate", "cloak": "cloak", "coordinate": "coordinate", "evade": "evade", "focus": "focus", "jam": "jam", "lock": "lock", "reinforce": "reinforce", "reload": "reload", "rotate arc": "rotatearc", "slam": "slam",
        };
        return m[a.toLowerCase().trim()] ?? "focus";
    }
    function parseSlotCountKey(key: string): { slot: string; count: number } | null {
        // key is "slotCount:SlotName:Count" — split by last colon
        const rest = key.slice(10);
        const lastColon = rest.lastIndexOf(":");
        if (lastColon === -1) return null;
        const slot = rest.slice(0, lastColon);
        const count = parseInt(rest.slice(lastColon + 1), 10);
        if (!slot || isNaN(count)) return null;
        return { slot, count };
    }
    function parseActionPairLabel(label: string): { action: string | null; linked: string | null } {
        const parts = label.split(" → ");
        if (parts.length === 2) return { action: parts[0] === "Any" ? null : parts[0], linked: parts[1] };
        const a = label.trim();
        return { action: a === "Any" ? null : a, linked: null };
    }
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

<div class="relative w-full rounded-xl border border-white/[0.08] bg-terminal-panel/90 backdrop-blur shadow-[inset_0_1px_0_rgba(255,255,255,0.04),0_4px_20px_rgba(0,0,0,0.25)] {open ? 'overflow-visible' : 'overflow-hidden'}">
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
                        {#if chip.key.startsWith("slotCount:")}
                            {@const parsed = parseSlotCountKey(chip.key)}
                            <button type="button" onclick={(e) => { e.stopPropagation(); if(onRemoveChip) onRemoveChip(chip.key); }} aria-label={`Remove ${chip.label}`} title={chip.label} class="inline-flex items-center justify-center w-7 h-7 rounded-md bg-white border border-white/10 shrink-0 hover:bg-white/90 transition-colors relative">
                                <i class="xwing-miniatures-font xwing-miniatures-font-{parsed ? slotToFont(parsed.slot) : 'modification'} text-[13px] leading-none text-black" style="text-transform:none" aria-hidden="true"></i>
                                {#if parsed && parsed.count > 1}
                                    <span class="absolute -top-1 -right-1 min-w-[14px] h-[14px] px-0.5 rounded-full bg-black text-white text-[8px] font-mono font-bold flex items-center justify-center border border-white">{parsed.count}</span>
                                {/if}
                            </button>
                        {:else if chip.key.startsWith("slot:")}
                            {@const s = chip.key.slice(5)}
                            <button type="button" onclick={(e) => { e.stopPropagation(); if(onRemoveChip) onRemoveChip(chip.key); }} aria-label={`Remove ${chip.label}`} title={chip.label} class="inline-flex items-center justify-center w-7 h-7 rounded-md bg-white border border-white/10 shrink-0 hover:bg-white/90 transition-colors">
                                <i class="xwing-miniatures-font xwing-miniatures-font-{slotToFont(s)} text-[13px] leading-none text-black" style="text-transform:none" aria-hidden="true"></i>
                            </button>
                        {:else if chip.key.startsWith("actionPair:")}
                            {@const pair = parseActionPairLabel(chip.label)}
                            <button type="button" onclick={(e) => { e.stopPropagation(); if(onRemoveChip) onRemoveChip(chip.key); }} aria-label={`Remove ${chip.label}`} title={chip.label} class="inline-flex items-center justify-center gap-0.5 px-1.5 h-7 rounded-md bg-white border border-white/10 shrink-0 hover:bg-white/90 transition-colors">
                                {#if pair.action}
                                    <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(pair.action)} text-[11px] leading-none text-black" style="text-transform:none" aria-hidden="true"></i>
                                {:else}
                                    <span class="text-[8px] font-mono font-bold text-black/60">ANY</span>
                                {/if}
                                {#if pair.linked}
                                    <span class="text-[8px] text-black/40">→</span>
                                    <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(pair.linked)} text-[11px] leading-none text-black" style="text-transform:none" aria-hidden="true"></i>
                                {/if}
                            </button>
                        {:else if chip.key.startsWith("action:")}
                            {@const a = chip.key.slice(7)}
                            <button type="button" onclick={(e) => { e.stopPropagation(); if(onRemoveChip) onRemoveChip(chip.key); }} aria-label={`Remove ${chip.label}`} title={chip.label} class="inline-flex items-center justify-center w-7 h-7 rounded-md bg-white border border-white/10 shrink-0 hover:bg-white/90 transition-colors">
                                <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(a)} text-[13px] leading-none text-black" style="text-transform:none" aria-hidden="true"></i>
                            </button>
                        {:else if chip.key.startsWith("linkedAction:")}
                            {@const a = chip.key.slice(13)}
                            <button type="button" onclick={(e) => { e.stopPropagation(); if(onRemoveChip) onRemoveChip(chip.key); }} aria-label={`Remove ${chip.label}`} title={chip.label} class="inline-flex items-center justify-center w-7 h-7 rounded-md bg-white border border-white/10 shrink-0 hover:bg-white/90 transition-colors">
                                <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(a)} text-[13px] leading-none text-black" style="text-transform:none" aria-hidden="true"></i>
                            </button>
                        {:else if chip.key.startsWith("faction:")}
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
                <button type="button" onclick={(e) => { e.stopPropagation(); onClear(); }} class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white text-black text-[11px] font-mono font-bold shadow-sm hover:bg-white/90 active:bg-white/80 transition-colors">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                    Clear
                </button>
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
