<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
    import Toggle from "./Toggle.svelte";

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
    <div class="flex items-center gap-2">
        <span class="text-[11px] font-bold tracking-[0.14em] text-secondary font-mono uppercase">Advanced Filters</span>
        <span class="flex-1 h-px bg-white/5 ml-2"></span>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-4">
        <div class="space-y-3 rounded-xl border border-white/5 bg-black/15 p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
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
                class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
            >
                <Toggle
                    size="xs"
                    ariaLabel="Toggle Unique"
                    checked={filters.isUnique}
                    onchange={(e) => (filters.isUnique = (e.currentTarget as HTMLInputElement).checked)}
                />
                <span class="font-mono">Unique</span>
            </label>
            <label
                class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
            >
                <Toggle
                    size="xs"
                    ariaLabel="Toggle Limited"
                    checked={filters.isLimited}
                    onchange={(e) => (filters.isLimited = (e.currentTarget as HTMLInputElement).checked)}
                />
                <span class="font-mono">Limited</span>
            </label>
            <label
                class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
            >
                <Toggle
                    size="xs"
                    ariaLabel="Toggle Generic"
                    checked={filters.isGeneric}
                    onchange={(e) => (filters.isGeneric = (e.currentTarget as HTMLInputElement).checked)}
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
                        class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                    >
                        <Toggle
                            size="xs"
                            ariaLabel={`Toggle base size ${size}`}
                            checked={filters.selectedBaseSizes.includes(size)}
                            onchange={() => toggleBaseSize(size)}
                        />
                        <span class="font-mono">{size}</span>
                    </label>
                {/each}
            </div>
        </div>
    {/if}
        </div>
        <div class="space-y-3 rounded-xl border border-white/5 bg-black/15 p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
            <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80">Pilot Stats</span>
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
        <div class="hidden 2xl:block rounded-xl border border-dashed border-white/10 bg-black/10 p-4 min-h-[120px] flex flex-col gap-2">
            <span class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary/70">Tips</span>
            <p class="text-[11px] font-mono leading-relaxed text-secondary/60">Ranges are inclusive. Combine factions with chassis for sharper card searches.</p>
        </div>
    </div>
</div>
