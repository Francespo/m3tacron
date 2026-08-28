<script lang="ts">
    import { onMount } from "svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import Toggle from "./Toggle.svelte";
    import FilterAnyAllToggle from "./FilterAnyAllToggle.svelte";
    import { getFactionColor } from "$lib/data/factions";

    let { selectedFactions = [] }: { selectedFactions?: string[] } = $props();

    let isOpen = $state(true);
    let search = $state("");

    // Flatten pilots from manifest, filtered by search + faction
    let allPilots = $derived.by(() => {
        const src = xwingData.currentSource;
        const pilots = xwingData.data[src]?.pilots ?? {};
        return Object.values(pilots) as any[];
    });

    let filteredPilots = $derived.by(() => {
        let r = allPilots;
        if (search) {
            const q = search.toLowerCase();
            r = r.filter((p: any) => p.name.toLowerCase().includes(q) || p.xws.toLowerCase().includes(q));
        }
        if (selectedFactions.length > 0) {
            const norm = (s: string) => s.toLowerCase().replace(/[\s-]/g, "");
            const wanted = new Set(selectedFactions.map(norm));
            r = r.filter((p: any) => wanted.has(norm(p.faction ?? "")));
        }
        return r.sort((a: any, b: any) => a.name.localeCompare(b.name));
    });

    let selectedCount = $derived(filters.selectedPilots.length);

    function togglePilot(xws: string) {
        if (filters.selectedPilots.includes(xws)) {
            filters.selectedPilots = filters.selectedPilots.filter((s) => s !== xws);
        } else {
            filters.selectedPilots = [...filters.selectedPilots, xws];
        }
    }

    // Ensure manifest loaded
    onMount(() => { xwingData.setSource(filters.dataSource as any); });
    let currentSource = $state(filters.dataSource);
    $effect(() => {
        if (currentSource !== filters.dataSource) {
            currentSource = filters.dataSource;
            xwingData.setSource(filters.dataSource as any);
        }
    });
</script>

<div>
    <div class="flex items-center justify-between w-full py-1 text-secondary">
        <span class="flex items-center gap-1.5">
            <span class="text-[11px] font-mono font-bold tracking-widest uppercase">Pilot</span>
            {#if selectedCount > 0}<span class="min-w-5 h-5 px-1 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center">{selectedCount}</span>{/if}
        </span>
    </div>
        <div class="pt-2.5 space-y-3">
            <div class="flex items-center justify-between gap-2 flex-wrap">
                <FilterAnyAllToggle bind:value={filters.pilotFilterMode} label="Match" />
                <span class="text-[11px] font-mono text-secondary/60">Any = O · All = E</span>
            </div>
            <input
                type="text"
                placeholder="Search pilots..."
                class="w-full bg-black border border-border-dark rounded-md px-2 py-1.5 text-xs font-mono text-primary placeholder-secondary focus:border-primary focus:outline-none"
                bind:value={search}
            />
            <div class="grid gap-1 max-h-[260px] overflow-y-auto pr-1">
                {#if filteredPilots.length === 0}
                    <div class="text-xs text-secondary font-mono">No pilots match.</div>
                {:else}
                    {#each filteredPilots as pilot}
                        {@const shipXws = pilot.ship ?? ""}
                        {@const fac = pilot.faction ?? "unknown"}
                        <label class="grid cursor-pointer text-xs text-secondary hover:text-primary group" style="grid-template-columns: 14px 20px 1fr auto; column-gap: 0.5rem; align-items: center;">
                            <Toggle size="xs" ariaLabel={`Toggle pilot ${pilot.name}`} checked={filters.selectedPilots.includes(pilot.xws)} onchange={() => togglePilot(pilot.xws)} />
                            <span class="w-[20px] h-[14px] inline-flex items-center justify-center leading-none"><i class="xwing-miniatures-ship xwing-miniatures-ship-{shipXws} text-sm leading-none"></i></span>
                            <span class="font-mono truncate text-xs text-left">{pilot.name}</span>
                            <span class="flex items-center gap-0.5 justify-end"><span class="w-5 h-5 flex items-center justify-center"><span class="font-xwing text-xs leading-none opacity-80" style="color: {getFactionColor(fac)}">{fac === 'rebelalliance' ? '!' : fac === 'galacticempire' ? '@' : fac === 'scumandvillainy' ? '#' : fac === 'resistance' ? '!' : fac === 'firstorder' ? '+' : fac === 'galacticrepublic' ? '/' : fac === 'separatistalliance' ? '.' : '?'}</span></span></span>
                        </label>
                    {/each}
                {/if}
            </div>
        </div>
</div>
