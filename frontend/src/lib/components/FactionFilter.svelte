<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
    import { ALL_FACTIONS, getFactionColor, getFactionLabel } from "$lib/data/factions";
    let { selectedFactions = filters.selectedFactions }: { selectedFactions?: string[] } = $props();
    let factionOpen = $state(true);
    function toggleFaction(f: string) {
        if (filters.selectedFactions.includes(f)) filters.selectedFactions = filters.selectedFactions.filter((x) => x !== f);
        else filters.selectedFactions = [...filters.selectedFactions, f];
    }
</script>

<div class="rounded-xl border border-white/5 bg-black/20 p-3 space-y-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
    <div class="flex items-center justify-between gap-2">
        <span class="flex items-center gap-1.5 text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">
            Faction
            {#if filters.selectedFactions.length > 0}<span class="min-w-5 h-5 px-1 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center">{filters.selectedFactions.length}</span>{/if}
        </span>
        <button type="button" onclick={() => (factionOpen = !factionOpen)} class="text-xs font-mono text-secondary hover:text-primary flex items-center gap-1 shrink-0">
            {factionOpen ? "Hide" : "Show"} <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="transition-transform {factionOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
        </button>
    </div>
    {#if factionOpen}
        <div class="grid grid-cols-4 gap-1 pt-1">
            {#each ALL_FACTIONS as f}
                {@const _sel = filters.selectedFactions.includes(f)}
                <button type="button" title={getFactionLabel(f)} aria-label={getFactionLabel(f)} aria-pressed={_sel} onclick={() => toggleFaction(f)} class="flex flex-col items-center justify-center gap-0.5 rounded-md border px-0.5 py-1.5 transition-colors {_sel ? 'bg-white border-white shadow-sm' : 'bg-black/30 border-white/10 hover:border-white/20 hover:bg-white/[0.04]'}">
                    <span class="w-6 h-6 inline-flex items-center justify-center leading-none text-base"><span class="font-xwing leading-none text-base" style="color: {getFactionColor(f)};">{f === 'rebelalliance' ? '!' : f === 'galacticempire' ? '@' : f === 'scumandvillainy' ? '#' : f === 'resistance' ? '!' : f === 'firstorder' ? '+' : f === 'galacticrepublic' ? '/' : f === 'separatistalliance' ? '.' : '?'}</span></span>
                    <span class="w-2.5 h-2.5 rounded-[2px] border flex items-center justify-center shrink-0 {_sel ? 'bg-black/10 border-black/10' : 'bg-black/40 border-white/10'}">
                        {#if _sel}<svg width="6" height="6" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12 10 17 19 7"/></svg>{/if}
                    </span>
                </button>
            {/each}
        </div>
    {:else}
        <div class="flex flex-wrap gap-1.5">
            {#if filters.selectedFactions.length === 0}
                <span class="text-[11px] font-mono text-secondary/60">All factions</span>
            {:else}
                {#each filters.selectedFactions as f}
                    <span class="inline-flex items-center justify-center w-7 h-7 rounded-md bg-white border border-white/10" title={getFactionLabel(f)}><span class="font-xwing leading-none text-sm" style="color: {getFactionColor(f)};">{f === 'rebelalliance' ? '!' : f === 'galacticempire' ? '@' : f === 'scumandvillainy' ? '#' : f === 'resistance' ? '!' : f === 'firstorder' ? '+' : f === 'galacticrepublic' ? '/' : f === 'separatistalliance' ? '.' : '?'}</span></span>
                {/each}
            {/if}
        </div>
    {/if}
</div>
