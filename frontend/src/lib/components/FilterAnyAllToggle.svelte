<script lang="ts">
    let { value = $bindable('any'), label = 'Match' }: { value: 'any' | 'all'; label?: string } = $props();
</script>

<div class="flex items-center gap-2">
    <span class="text-[10px] font-mono font-bold tracking-widest uppercase text-secondary/70">{label}</span>
    <div class="inline-flex bg-black/60 border border-white/10 rounded-full p-0.5 gap-0.5">
        <button
            type="button"
            class="px-2.5 py-1 rounded-full text-[11px] font-mono font-medium transition-colors {value === 'any' ? 'bg-white text-black shadow-sm' : 'text-secondary hover:text-primary'}"
            onclick={() => (value = 'any')}
            aria-pressed={value === 'any'}
        >
            Any
        </button>
        <button
            type="button"
            class="px-2.5 py-1 rounded-full text-[11px] font-mono font-medium transition-colors {value === 'all' ? 'bg-white text-black shadow-sm' : 'text-secondary hover:text-primary'}"
            onclick={() => (value = 'all')}
            aria-pressed={value === 'all'}
        >
            All
        </button>
    </div>
</div>
