<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
    import { ALL_FACTIONS, getFactionColor, getFactionLabel } from "$lib/data/factions";
    let { selectedFactions = filters.selectedFactions }: { selectedFactions?: string[] } = $props();
    let factionOpen = $state(true); // always open
    function toggleFaction(f: string) {
        if (filters.selectedFactions.includes(f)) filters.selectedFactions = filters.selectedFactions.filter((x) => x !== f);
        else filters.selectedFactions = [...filters.selectedFactions, f];
    }
</script>

<div class="relative rounded-xl border border-white/5 bg-black/20 overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] w-full self-start h-fit">
    <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent opacity-60" aria-hidden="true"></div>
    <button type="button" onclick={() => (factionOpen = !factionOpen)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
        <span class="flex items-center gap-1.5 text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">
            Faction
            {#if filters.selectedFactions.length > 0}<span class="min-w-5 h-5 px-1 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center">{filters.selectedFactions.length}</span>{/if}
        </span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {factionOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
    </button>
    {#if factionOpen}<div class="px-3.5 pb-3.5 pt-1">
        <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
            {#each ALL_FACTIONS as f}
                {@const _sel = filters.selectedFactions.includes(f)}
                <button type="button" title={getFactionLabel(f)} aria-label={getFactionLabel(f)} aria-pressed={_sel} onclick={() => toggleFaction(f)} class="flex flex-col items-center justify-center gap-0.5 rounded-lg border px-1 py-2 transition-colors {_sel ? 'bg-white border-white shadow-sm' : 'bg-black/30 border-white/10 hover:border-white/20 hover:bg-white/[0.04]'}">
                    <span class="w-7 h-7 inline-flex items-center justify-center leading-none text-lg"><span class="font-xwing leading-none text-lg" style="color: {getFactionColor(f)};">{f === 'rebelalliance' ? '!' : f === 'galacticempire' ? '@' : f === 'scumandvillainy' ? '#' : f === 'resistance' ? '!' : f === 'firstorder' ? '+' : f === 'galacticrepublic' ? '/' : f === 'separatistalliance' ? '.' : '?'}</span></span>
                    <span class="w-2.5 h-2.5 rounded-[2px] border flex items-center justify-center shrink-0 {_sel ? 'bg-black/10 border-black/10' : 'bg-black/40 border-white/10'}">
                        {#if _sel}<svg width="6" height="6" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12 10 17 19 7"/></svg>{/if}
                    </span>
                </button>
            {/each}
        </div>
    </div>{/if}
</div>
