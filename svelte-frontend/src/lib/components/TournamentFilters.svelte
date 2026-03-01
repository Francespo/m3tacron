<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";

    let dateOpen = $state(false);
    let locationOpen = $state(false);
    let formatOpen = $state(false);

    // Available options (loaded from API or hardcoded)
    const continents = [
        "Africa",
        "Asia",
        "Europe",
        "North America",
        "Oceania",
        "South America",
        "Unknown",
        "Virtual",
    ];
    const formats = [
        "Standard",
        "Extended",
        "Custom",
        "Escalation",
        "Epic",
        "Legacy Standard",
        "Legacy Extended",
    ];

    function toggleContinent(c: string) {
        if (filters.selectedContinents.includes(c)) {
            filters.selectedContinents = filters.selectedContinents.filter(
                (x) => x !== c,
            );
        } else {
            filters.selectedContinents = [...filters.selectedContinents, c];
        }
    }

    function toggleFormat(f: string) {
        if (filters.selectedFormats.includes(f)) {
            filters.selectedFormats = filters.selectedFormats.filter(
                (x) => x !== f,
            );
        } else {
            filters.selectedFormats = [...filters.selectedFormats, f];
        }
    }
</script>

<div class="w-full space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
        <span class="text-xs font-bold tracking-widest text-primary font-mono">
            TOURNAMENT FILTERS
        </span>
        <button
            class="text-secondary hover:text-primary transition-colors p-1"
            onclick={() => filters.resetAll()}
            title="Reset Filters"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                ><path
                    d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"
                /><path d="M3 3v5h5" /></svg
            >
        </button>
    </div>

    <!-- Date Range Accordion -->
    <div class="border-b border-border-dark">
        <button
            class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
            onclick={() => (dateOpen = !dateOpen)}
        >
            <span class="text-xs font-mono font-bold tracking-wider"
                >Date Range</span
            >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="transition-transform {dateOpen ? 'rotate-180' : ''}"
                ><path d="m6 9 6 6 6-6" /></svg
            >
        </button>
        {#if dateOpen}
            <div class="pb-3 space-y-1.5 pl-2">
                <input
                    type="date"
                    class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.dateStart}
                />
                <span class="text-xs text-secondary block text-center">to</span>
                <input
                    type="date"
                    class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.dateEnd}
                />
            </div>
        {/if}
    </div>

    <!-- Location Accordion -->
    <div class="border-b border-border-dark">
        <button
            class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
            onclick={() => (locationOpen = !locationOpen)}
        >
            <span class="text-xs font-mono font-bold tracking-wider"
                >Location</span
            >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="transition-transform {locationOpen ? 'rotate-180' : ''}"
                ><path d="m6 9 6 6 6-6" /></svg
            >
        </button>
        {#if locationOpen}
            <div class="pb-3 space-y-1 pl-2 max-h-[200px] overflow-y-auto">
                {#each continents as c}
                    <label
                        class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                    >
                        <input
                            type="checkbox"
                            class="rounded border-border-dark bg-black w-3 h-3"
                            checked={filters.selectedContinents.includes(c)}
                            onchange={() => toggleContinent(c)}
                        />
                        <span class="font-mono">{c}</span>
                    </label>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Format Accordion -->
    <div class="border-b border-border-dark">
        <button
            class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
            onclick={() => (formatOpen = !formatOpen)}
        >
            <span class="text-xs font-mono font-bold tracking-wider"
                >Format</span
            >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="transition-transform {formatOpen ? 'rotate-180' : ''}"
                ><path d="m6 9 6 6 6-6" /></svg
            >
        </button>
        {#if formatOpen}
            <div class="pb-3 space-y-1 pl-2 max-h-[200px] overflow-y-auto">
                {#each formats as f}
                    <label
                        class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                    >
                        <input
                            type="checkbox"
                            class="rounded border-border-dark bg-black w-3 h-3"
                            checked={filters.selectedFormats.includes(f)}
                            onchange={() => toggleFormat(f)}
                        />
                        <span class="font-mono">{f}</span>
                    </label>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Search Name -->
    <div class="space-y-1">
        <span class="text-xs font-mono font-bold tracking-wider text-secondary"
            >Search Name</span
        >
        <input
            type="text"
            placeholder="Search name..."
            class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary placeholder:text-[#555] focus:border-primary focus:outline-none"
            bind:value={filters.searchName}
        />
    </div>
</div>
