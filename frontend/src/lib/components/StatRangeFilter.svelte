<script lang="ts">
    let open = $state(true);
    import { filters } from "$lib/stores/filters.svelte";

    type Props = {
        label?: string;
    };
    let { label = "Stat ranges" }: Props = $props();
</script>

<div class="rounded-xl border border-white/5 bg-black/20 p-3.5 space-y-3 shadow- self-start h-fit[inset_0_1px_0_rgba(255,255,255,0.04)]">
    <button type="button" onclick={() => (open = !open)} class="flex items-center gap-1.5 w-full text-left hover:text-primary transition-colors">
        <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">{label}</span>
        <span class="flex-1 h-px bg-white/5 ml-2"></span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ml-2 shrink-0 transition-transform {open ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
    </button>
    {#if open}<div class="grid grid-cols-1 gap-2.5">
        {#each [
            { key: 'Lists', min: 'listsMin', max: 'listsMax' },
            { key: 'Entries', min: 'entriesMin', max: 'entriesMax' },
            { key: 'Games', min: 'gamesMin', max: 'gamesMax' },
            { key: 'Win rate %', min: 'winRateMin', max: 'winRateMax' },
        ] as row}
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
