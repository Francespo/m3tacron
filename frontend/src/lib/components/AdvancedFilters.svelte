<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";

    let { isPilotsTab = true }: { isPilotsTab?: boolean } = $props();

    function toggleBaseSize(size: string) {
        if (filters.selectedBaseSizes.includes(size)) {
            filters.selectedBaseSizes = filters.selectedBaseSizes.filter(
                (s) => s !== size,
            );
        } else {
            filters.selectedBaseSizes = [...filters.selectedBaseSizes, size];
        }
    }
</script>

<div class="w-full space-y-4">
    <div class="flex items-center justify-between">
        <span
            class="text-xs font-bold tracking-widest text-primary font-mono uppercase"
        >
            Advanced Filters
        </span>
    </div>

    <!-- Point Costs (Range) -->
    <div class="space-y-1">
        <span
            class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase"
            >Point Costs</span
        >
        <div class="flex items-center gap-2">
            <span class="text-xs text-secondary font-mono">from</span>
            <input
                type="number"
                class="w-[60px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                bind:value={filters.pointsMin}
            />
            <span class="text-xs text-secondary font-mono">to</span>
            <input
                type="number"
                class="w-[60px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                bind:value={filters.pointsMax}
            />
        </div>
    </div>

    <!-- Loadout Value (XWA Pilots Only) -->
    {#if isPilotsTab && filters.dataSource === "xwa"}
        <div class="space-y-1">
            <span
                class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase"
                >Loadout Value</span
            >
            <div class="flex items-center gap-2">
                <span class="text-xs text-secondary font-mono">from</span>
                <input
                    type="number"
                    class="w-[60px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.loadoutMin}
                />
                <span class="text-xs text-secondary font-mono">to</span>
                <input
                    type="number"
                    class="w-[60px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.loadoutMax}
                />
            </div>
        </div>
    {/if}

    <!-- Uniqueness toggles -->
    <div class="space-y-1">
        <span
            class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase"
            >Uniqueness</span
        >
        <div class="flex items-center gap-4 flex-wrap">
            <label
                class="flex items-center gap-2 py-1.5 cursor-pointer text-xs text-secondary hover:text-primary"
            >
                <input
                    type="checkbox"
                    class="rounded border-border-dark bg-black w-4 h-4"
                    bind:checked={filters.isUnique}
                />
                <span class="font-mono">Unique</span>
            </label>
            <label
                class="flex items-center gap-2 py-1.5 cursor-pointer text-xs text-secondary hover:text-primary"
            >
                <input
                    type="checkbox"
                    class="rounded border-border-dark bg-black w-4 h-4"
                    bind:checked={filters.isLimited}
                />
                <span class="font-mono">Limited</span>
            </label>
            <label
                class="flex items-center gap-2 py-1.5 cursor-pointer text-xs text-secondary hover:text-primary"
            >
                <input
                    type="checkbox"
                    class="rounded border-border-dark bg-black w-4 h-4"
                    bind:checked={filters.isGeneric}
                />
                <span class="font-mono">Generic</span>
            </label>
        </div>
    </div>

    <!-- Base Size (Pilots Only) -->
    {#if isPilotsTab}
        <div class="space-y-1">
            <span
                class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase"
                >Base Size</span
            >
            <div class="flex items-center gap-4">
                {#each ["S", "M", "L", "H"] as size}
                    <label
                        class="flex items-center gap-2 py-1.5 cursor-pointer text-xs text-secondary hover:text-primary"
                    >
                        <input
                            type="checkbox"
                            class="rounded border-border-dark bg-black w-4 h-4"
                            checked={filters.selectedBaseSizes.includes(size)}
                            onchange={() => toggleBaseSize(size)}
                        />
                        <span class="font-mono">{size}</span>
                    </label>
                {/each}
            </div>
        </div>
    {/if}

    <!-- Pilot-Specific Stats -->
    {#if isPilotsTab}
        <div class="space-y-2 pt-2">
            <!-- Initiative -->
            <div class="flex items-center gap-2 w-full">
                <span
                    class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase w-20"
                    >Initiative:</span
                >
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.initMin}
                />
                <span class="text-xs text-secondary font-mono">to</span>
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.initMax}
                />
            </div>
            <!-- Hull -->
            <div class="flex items-center gap-2 w-full">
                <span
                    class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase w-20"
                    >Hull:</span
                >
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.hullMin}
                />
                <span class="text-xs text-secondary font-mono">to</span>
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.hullMax}
                />
            </div>
            <!-- Shields -->
            <div class="flex items-center gap-2 w-full">
                <span
                    class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase w-20"
                    >Shields:</span
                >
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.shieldsMin}
                />
                <span class="text-xs text-secondary font-mono">to</span>
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.shieldsMax}
                />
            </div>
            <!-- Agility -->
            <div class="flex items-center gap-2 w-full">
                <span
                    class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase w-20"
                    >Agility:</span
                >
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.agilityMin}
                />
                <span class="text-xs text-secondary font-mono">to</span>
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.agilityMax}
                />
            </div>
            <!-- Attack -->
            <div class="flex items-center gap-2 w-full">
                <span
                    class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase w-20"
                    >Attack:</span
                >
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.attackMin}
                />
                <span class="text-xs text-secondary font-mono">to</span>
                <input
                    type="number"
                    class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={filters.attackMax}
                />
            </div>
        </div>
    {/if}
</div>
