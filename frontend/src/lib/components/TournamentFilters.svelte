<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";

    let dateOpen = $state(false);
    let locationOpen = $state(false);
    let formatOpen = $state(false);
    let platformOpen = $state(false);

    // Available options
    const continents = [
        "Africa",
        "Asia",
        "Europe",
        "North America",
        "Oceania",
        "South America",
        "Unknown",
        "Unknown",
        "Virtual",
    ];

    const platforms = [
        { id: "longshanks", label: "Longshanks" },
        { id: "listfortress", label: "ListFortress" },
        { id: "rollbetter", label: "Rollbetter" },
    ];

    // Hierarchical formats matching backend logic
    const formatGroups = [
        {
            label: "2.5",
            formats: [
                { id: "amg", label: "AMG" },
                { id: "xwa", label: "XWA" },
            ],
        },
        {
            label: "2.0",
            formats: [
                { id: "legacy_x2po", label: "Legacy (X2PO)" },
                { id: "legacy_xlc", label: "Legacy (XLC)" },
                { id: "ffg", label: "FFG" },
            ],
        },
        {
            label: "Unknown",
            formats: [{ id: "other", label: "Unknown" }],
        },
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

    function togglePlatform(pId: string) {
        if (filters.selectedPlatforms.includes(pId)) {
            filters.selectedPlatforms = filters.selectedPlatforms.filter(
                (x) => x !== pId,
            );
        } else {
            filters.selectedPlatforms = [...filters.selectedPlatforms, pId];
        }
    }

    function toggleFormat(fId: string) {
        if (filters.selectedFormats.includes(fId)) {
            filters.selectedFormats = filters.selectedFormats.filter(
                (x) => x !== fId,
            );
        } else {
            filters.selectedFormats = [...filters.selectedFormats, fId];
        }
    }
</script>

<div class="w-full space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
        <span class="text-xs font-bold tracking-widest text-primary font-mono">
            TOURNAMENT FILTERS
        </span>
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
            <div class="pb-3 space-y-3 pl-2 max-h-[300px] overflow-y-auto pr-1">
                {#each formatGroups as group}
                    <div class="space-y-1">
                        <span
                            class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase"
                            >{group.label}</span
                        >
                        {#each group.formats as f}
                            <label
                                class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary pl-1"
                            >
                                <input
                                    type="checkbox"
                                    class="rounded border-border-dark bg-black w-3 h-3"
                                    checked={filters.selectedFormats.includes(
                                        f.id,
                                    )}
                                    onchange={() => toggleFormat(f.id)}
                                />
                                <span class="font-mono">{f.label}</span>
                            </label>
                        {/each}
                    </div>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Platform Filter Section -->
    <div class="border-b border-border-dark">
        <button
            class="flex items-center justify-between w-full py-2 text-secondary hover:text-primary transition-colors"
            onclick={() => (platformOpen = !platformOpen)}
        >
            <span class="text-xs font-mono font-bold tracking-wider"
                >Platform</span
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
                class="transition-transform {platformOpen ? 'rotate-180' : ''}"
                ><path d="m6 9 6 6 6-6" /></svg
            >
        </button>
        {#if platformOpen}
            <div class="pb-3 space-y-1 pl-2">
                {#each platforms as platform}
                    <label
                        class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                    >
                        <input
                            type="checkbox"
                            class="rounded border-border-dark bg-black w-3 h-3"
                            checked={filters.selectedPlatforms.includes(
                                platform.id,
                            )}
                            onchange={() => togglePlatform(platform.id)}
                        />
                        <span class="font-mono">{platform.label}</span>
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
