<script lang="ts">
    import { onMount } from "svelte";
    import { filters } from "$lib/stores/filters.svelte";
    import { xwingData } from "$lib/stores/xwingData.svelte";
    import Toggle from "./Toggle.svelte";
    import FilterAnyAllToggle from "./FilterAnyAllToggle.svelte";
    import { getFactionColor } from "$lib/data/factions";

    let { selectedFactions = [], showModeToggle = true }: { selectedFactions?: string[]; showModeToggle?: boolean } = $props();

    let isOpen = $state(true); // mini-collapsible
    let search = $state("");

    type PilotGroup = { key: string; name: string; ship: string; faction: string; xwsList: string[]; representative: any };
    // Group pilots by (normalized name + ship) so that "Luke (T-65)" variants collapse to one row.
    // Same pilot on different ships keeps separate rows (per request).
    let allPilots = $derived.by<PilotGroup[]>(() => {
        const src = xwingData.currentSource;
        const pilots = xwingData.data[src]?.pilots ?? {};
        const byKey = new Map<string, PilotGroup>();
        for (const p of Object.values(pilots) as any[]) {
            const key = `${(p.name ?? "").trim().toLowerCase()}|${p.ship ?? ""}`;
            let g = byKey.get(key);
            if (!g) {
                g = { key, name: p.name, ship: p.ship ?? "", faction: p.faction ?? "unknown", xwsList: [], representative: p };
                byKey.set(key, g);
            }
            g.xwsList.push(p.xws);
            // Prefer a non-suffixed xws as representative if available
            if (!g.representative || (g.representative.xws.includes("-") && !p.xws.includes("-"))) g.representative = p;
        }
        return [...byKey.values()];
    });

    let filteredPilots = $derived.by<PilotGroup[]>(() => {
        let r = allPilots;
        if (search) {
            const q = search.toLowerCase();
            r = r.filter((g) => g.name.toLowerCase().includes(q) || g.xwsList.some((x) => x.toLowerCase().includes(q)));
        }
        if (selectedFactions.length > 0) {
            const norm = (s: string) => s.toLowerCase().replace(/[\s-]/g, "");
            const wanted = new Set(selectedFactions.map(norm));
            r = r.filter((g) => wanted.has(norm(g.faction ?? "")));
        }
        return [...r].sort((a, b) => a.name.localeCompare(b.name) || a.ship.localeCompare(b.ship));
    });

    let selectedCount = $derived(allPilots.filter(isGroupSelected).length);
    let autoShow = $derived(selectedCount > 1);
    let effectiveShow = $derived(showModeToggle && autoShow);

    function isGroupSelected(g: PilotGroup): boolean {
        // Checked if ANY variant of the group is selected (union view)
        return g.xwsList.some((x) => filters.selectedPilots.includes(x));
    }
    function togglePilotGroup(g: PilotGroup) {
        const sel = new Set(filters.selectedPilots);
        const isSel = isGroupSelected(g);
        if (isSel) {
            for (const x of g.xwsList) sel.delete(x);
        } else {
            for (const x of g.xwsList) sel.add(x);
        }
        filters.selectedPilots = [...sel];
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

<div class="relative rounded-xl border border-white/5 bg-black/20 overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] w-full min-w-0 self-start h-fit">
    <div class="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-60" aria-hidden="true"></div>
    <button type="button" onclick={() => (isOpen = !isOpen)} class="w-full flex items-center justify-between gap-2 px-3.5 py-2.5 text-left hover:bg-white/[0.02] transition-colors">
        <span class="flex items-center gap-1.5 text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">
            <span>Pilot</span>
            {#if selectedCount > 0}<span class="min-w-5 h-5 px-1 rounded-full bg-primary text-black text-[10px] font-mono font-bold inline-flex items-center justify-center">{selectedCount}</span>{/if}
        </span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {isOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
    </button>
        {#if isOpen}<div class="px-3.5 pb-3.5 pt-1 space-y-3 min-w-0">
            {#if effectiveShow}<div class="flex items-center justify-between gap-2 min-w-0 flex-wrap">
                <FilterAnyAllToggle bind:value={filters.pilotFilterMode} label="Match" />
            </div>{/if}
            <input
                type="text"
                placeholder="Search pilots..."
                class="w-full bg-black border border-border-dark rounded-md px-2 py-1.5 text-xs font-mono text-primary placeholder-secondary focus:border-primary focus:outline-none"
                bind:value={search}
            />
            <div class="grid gap-1 max-h-[220px] overflow-y-auto overflow-x-hidden pilot-scrollbar pr-1 min-w-0" style="overscroll-behavior: contain; -webkit-overflow-scrolling: touch;">
                {#if filteredPilots.length === 0}
                    <div class="text-xs text-secondary font-mono">No pilots match.</div>
                {:else}
                    {#each filteredPilots as group (group.key)}
                        {@const shipXws = group.ship ?? ""}
                        {@const fac = group.faction ?? "unknown"}
                        <label class="grid cursor-pointer text-xs text-secondary hover:text-primary group min-w-0 w-full" style="grid-template-columns: 14px 20px minmax(0, 1fr) auto; column-gap: 0.5rem; align-items: center;">
                            <Toggle size="xs" ariaLabel={`Toggle pilot ${group.name}`} checked={isGroupSelected(group)} onchange={() => togglePilotGroup(group)} />
                            <span class="w-[20px] h-[14px] inline-flex items-center justify-center leading-none shrink-0"><i class="xwing-miniatures-ship xwing-miniatures-ship-{shipXws} text-sm leading-none"></i></span>
                            <span class="font-mono truncate text-xs text-left min-w-0" title="{group.name} — {shipXws}">{group.name}</span>
                            <span class="flex items-center gap-0.5 justify-end shrink-0"><span class="w-5 h-5 flex items-center justify-center"><span class="font-xwing text-xs leading-none opacity-80" style="color: {getFactionColor(fac)}">{fac === 'rebelalliance' ? '!' : fac === 'galacticempire' ? '@' : fac === 'scumandvillainy' ? '#' : fac === 'resistance' ? '!' : fac === 'firstorder' ? '+' : fac === 'galacticrepublic' ? '/' : fac === 'separatistalliance' ? '.' : '?'}</span></span></span>
                        </label>
                    {/each}
                {/if}
            </div>
        </div>{/if}
</div>

<style>
    .pilot-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .pilot-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .pilot-scrollbar::-webkit-scrollbar-thumb {
        background: #333;
        border-radius: 4px;
    }
    .pilot-scrollbar::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
</style>
