<script lang="ts">
    import { onMount } from "svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import Toggle from "./Toggle.svelte";
    import FilterAnyAllToggle from "./FilterAnyAllToggle.svelte";

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
    <button
        class="flex items-center justify-between w-full py-1.5 text-secondary hover:text-primary transition-colors"
        onclick={() => (isOpen = !isOpen)}
    >
        <span class="flex items-center gap-1.5">
            <span class="text-[11px] font-mono font-bold tracking-widest uppercase">Pilot</span>
            {#if selectedCount > 0}<span class="min-w-5 h-5 px-1 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center">{selectedCount}</span>{/if}
        </span>
        <span class="text-xs font-mono text-secondary flex items-center gap-1">{isOpen ? "Hide" : "Show"} <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="transition-transform {isOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg></span>
    </button>

    {#if isOpen}
        <div class="pt-3 space-y-3">
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
                        <label class="grid cursor-pointer text-xs text-secondary hover:text-primary" style="grid-template-columns: 14px 1fr auto; column-gap: 0.5rem; align-items: center;">
                            <Toggle size="xs" ariaLabel={`Toggle pilot ${pilot.name}`} checked={filters.selectedPilots.includes(pilot.xws)} onchange={() => togglePilot(pilot.xws)} />
                            <span class="font-mono truncate text-xs text-left">{pilot.name}</span>
                            <span class="text-[10px] font-mono text-secondary/60 truncate max-w-[7rem] text-right">{pilot.faction ?? ""}</span>
                        </label>
                    {/each}
                {/if}
            </div>
        </div>
    {/if}
</div>
