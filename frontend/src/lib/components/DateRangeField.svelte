<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
    let { label = "Date Range", hideLabel = false }: { label?: string; hideLabel?: boolean } = $props();
    let startRef: HTMLInputElement | undefined = $state();
    let endRef: HTMLInputElement | undefined = $state();

    function openPicker(el?: HTMLInputElement) {
        try { (el as any)?.showPicker?.(); } catch { el?.focus(); el?.click(); }
    }
</script>

<div class="space-y-2">
    {#if !hideLabel}<div class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">{label}</div>{/if}
    <div class="grid grid-cols-1 gap-2">
        <div class="flex items-center gap-1.5">
            <span class="text-[11px] font-mono text-secondary w-8 shrink-0">From</span>
            <div class="relative flex-1">
                <input bind:this={startRef} type="date" class="w-full bg-black border border-border-dark rounded px-2 py-1.5 pr-8 text-xs font-mono text-primary focus:border-primary focus:outline-none" bind:value={filters.dateStart} aria-label="Start date" />
                <button type="button" class="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 inline-flex items-center justify-center rounded text-secondary hover:text-primary hover:bg-white/10" onclick={() => openPicker(startRef)} aria-label="Open calendar for start date">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
                </button>
            </div>
            {#if filters.dateStart}
                <button type="button" class="w-6 h-6 grid place-items-center rounded hover:bg-white/10 text-secondary hover:text-primary" onclick={() => (filters.dateStart = '')} aria-label="Clear start date"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="M6 6 12 12"/></svg></button>
            {/if}
        </div>
        <div class="flex items-center gap-1.5">
            <span class="text-[11px] font-mono text-secondary w-8 shrink-0">To</span>
            <div class="relative flex-1">
                <input bind:this={endRef} type="date" class="w-full bg-black border border-border-dark rounded px-2 py-1.5 pr-8 text-xs font-mono text-primary focus:border-primary focus:outline-none" bind:value={filters.dateEnd} aria-label="End date" />
                <button type="button" class="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 inline-flex items-center justify-center rounded text-secondary hover:text-primary hover:bg-white/10" onclick={() => openPicker(endRef)} aria-label="Open calendar for end date">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
                </button>
            </div>
            {#if filters.dateEnd}
                <button type="button" class="w-6 h-6 grid place-items-center rounded hover:bg-white/10 text-secondary hover:text-primary" onclick={() => (filters.dateEnd = '')} aria-label="Clear end date"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="M6 6 12 12"/></svg></button>
            {/if}
        </div>
    </div>
</div>
