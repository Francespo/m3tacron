<script lang="ts">
    /**
     * Reusable Sort Selector component for standardizing sorting UI across pages.
     */
    let {
        sortBy = $bindable(),
        sortDirection = $bindable(),
        options = [],
    }: {
        sortBy: string;
        sortDirection: string;
        options: { value: string; label: string }[];
    } = $props();

    let sortedOptions = $derived(
        [...options].sort((a, b) => a.label.localeCompare(b.label)),
    );

    // Defensive default: if parent passes an empty sortBy (or no
    // matching option), show the first sorted option as the visible
    // selection rather than rendering a blank <select>. The first
    // option in the array is also written back to sortBy on change
    // when the user picks anything, so the bound state stays sane.
    let displayValue = $derived(
        sortedOptions.find((o) => o.value === sortBy)?.value ??
            sortedOptions[0]?.value ??
            "",
    );

    function onSortChange(event: Event) {
        const target = event.currentTarget as HTMLSelectElement;
        sortBy = target.value;
    }

    function toggleDirection() {
        sortDirection = sortDirection === "desc" ? "asc" : "desc";
    }
</script>

<div class="space-y-1">
    <span class="text-xs font-mono font-bold tracking-wider text-secondary"
        >Sort By</span
    >
    <div class="flex gap-2">
        <select
            class="flex-1 bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none"
            value={displayValue}
            onchange={onSortChange}
        >
            {#each sortedOptions as option}
                <option value={option.value}>{option.label}</option>
            {/each}
        </select>
        <button
            class="w-9 flex items-center justify-center bg-black border border-border-dark rounded hover:bg-[#ffffff08] transition-colors"
            onclick={toggleDirection}
            title={sortDirection === "desc" ? "Descending" : "Ascending"}
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="text-secondary {sortDirection === 'asc'
                    ? 'rotate-180'
                    : ''}"
            >
                <path d="M12 5v14" />
                <path d="m19 12-7 7-7-7" />
            </svg>
        </button>
    </div>
</div>
