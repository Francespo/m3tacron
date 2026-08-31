<script lang="ts">
    let {
        label,
        min = $bindable(''),
        max = $bindable(''),
        placeholderMin = "—",
        placeholderMax = "—",
        width = "58px",
    }: {
        label: string;
        min?: string;
        max?: string;
        placeholderMin?: string;
        placeholderMax?: string;
        width?: string;
    } = $props();
</script>

<label class="flex items-center gap-1.5 flex-wrap">
    <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary/80 w-[5.2rem] shrink-0">{label}</span>
    <span class="text-[11px] font-mono text-secondary shrink-0">from</span>
    <input
        type="number"
        inputmode="numeric"
        placeholder={placeholderMin}
        class="bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none"
        style="width: {width}"
        bind:value={min}
    />
    <span class="text-[11px] font-mono text-secondary shrink-0">to</span>
    <input
        type="number"
        inputmode="numeric"
        placeholder={placeholderMax}
        class="bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none"
        style="width: {width}"
        bind:value={max}
    />
</label>
