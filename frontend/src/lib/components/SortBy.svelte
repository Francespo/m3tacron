<script lang="ts">
    let { value, direction, options, onChange }: {
        value: string;
        direction: "asc" | "desc";
        options: Array<{ value: string; label: string }>;
        onChange: (newValue: string, newDirection: "asc" | "desc") => void;
    } = $props();

    function handleValueChange(e: Event) {
        const target = e.target as HTMLSelectElement;
        onChange(target.value, direction);
    }

    function handleDirectionToggle() {
        const newDir = direction === "asc" ? "desc" : "asc";
        onChange(value, newDir);
    }
</script>

<div class="flex items-center gap-2">
    <span class="text-xs text-secondary font-mono uppercase tracking-wider whitespace-nowrap">Sort by</span>
    <select
        class="bg-terminal-panel border border-border-dark rounded-md text-xs font-mono text-primary px-2 py-1"
        onchange={handleValueChange}
    >
        {#each options as opt}
            <option value={opt.value} selected={opt.value === value}>{opt.label}</option>
        {/each}
    </select>
    <button
        type="button"
        onclick={handleDirectionToggle}
        class="inline-flex items-center justify-center w-7 h-7 bg-terminal-panel border border-border-dark rounded-md text-secondary hover:text-primary hover:bg-[#ffffff05] transition-colors"
        aria-label={direction === "asc" ? "Sort ascending" : "Sort descending"}
    >
        {#if direction === "asc"}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
        {:else}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>
        {/if}
    </button>
</div>
