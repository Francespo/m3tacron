<script lang="ts">
    let open = $state(true);
    import { filters } from "$lib/stores/filters.svelte";

    type Props = {
        label?: string;
        hideLists?: boolean;
    };
    let { label = "Stat ranges", hideLists = false }: Props = $props();
    const baseRows = [
        { key: 'Lists', min: 'listsMin' as const, max: 'listsMax' as const },
        { key: 'Entries', min: 'entriesMin' as const, max: 'entriesMax' as const },
        { key: 'Games', min: 'gamesMin' as const, max: 'gamesMax' as const },
        { key: 'Win rate %', min: 'winRateMin' as const, max: 'winRateMax' as const },
    ];
    let rows = $derived(hideLists ? baseRows.filter(r => r.key !== 'Lists') : baseRows);
</script>

<div class="relative rounded-xl border border-white/5 bg-black/20 overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] w-full self-start h-fit">
    <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
    <button type="button" onclick={() => (open = !open)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
        <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">{label}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {open ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
    </button>
    {#if open}<div class="px-3.5 pb-3.5 pt-1 grid grid-cols-1 gap-2.5">
        {#each rows as row}
            <label class="flex items-center gap-1.5 flex-wrap">
                <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary/80 w-[5.2rem] shrink-0">{row.key}</span>
                <span class="text-[11px] font-mono text-secondary shrink-0">from</span>
                <input
                    type="number"
                    inputmode="numeric"
                    placeholder="—"
                    class="w-[58px] sm:w-[64px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none"
                    value={(filters as any)[row.min]}
                    oninput={(e) => ((filters as any)[row.min] = (e.currentTarget as HTMLInputElement).value)}
                />
                <span class="text-[11px] font-mono text-secondary shrink-0">to</span>
                <input
                    type="number"
                    inputmode="numeric"
                    placeholder="—"
                    class="w-[58px] sm:w-[64px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none"
                    value={(filters as any)[row.max]}
                    oninput={(e) => ((filters as any)[row.max] = (e.currentTarget as HTMLInputElement).value)}
                />
            </label>
        {/each}
    </div>{/if}
</div>
