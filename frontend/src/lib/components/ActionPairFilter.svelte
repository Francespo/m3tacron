<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
    import FilterAnyAllToggle from "./FilterAnyAllToggle.svelte";
    import Toggle from "./Toggle.svelte";

    /**
     * Composite filter for ship actions.
     * Each entry is { action: string|null, linked: string|null }
     * - action=null, linked=X  -> any ship where some action links to X
     * - action=X, linked=null -> ship has action X (primary)
     * - action=X, linked=Y    -> ship has action X linked to Y specifically
     * Combinations are OR-ed by default, AND when mode='all' (must satisfy all pairs).
     * Stored as JSON array in filters.actionPairs.
     */
    type Pair = { action: string | null; linked: string | null };

    const ACTION_OPTIONS = [
        "Barrel Roll","Boost","Calculate","Cloak","Coordinate","Evade","Focus","Jam","Lock","Reinforce","Reload","Rotate Arc","SLAM",
    ];

    function actionToFont(a: string): string {
        const m: Record<string, string> = {
            "barrel roll": "barrelroll", "boost": "boost", "calculate": "calculate",
            "cloak": "cloak", "coordinate": "coordinate", "evade": "evade",
            "focus": "focus", "jam": "jam", "lock": "lock", "reinforce": "reinforce",
            "reload": "reload", "rotate arc": "rotatearc", "slam": "slam",
        };
        return m[a.toLowerCase()] ?? "focus";
    }

    function getPairs(): Pair[] {
        try {
            const raw = (filters as any).actionPairs as string;
            if (!raw) return [];
            return JSON.parse(raw) as Pair[];
        } catch { return []; }
    }
    function setPairs(pairs: Pair[]) {
        (filters as any).actionPairs = pairs.length ? JSON.stringify(pairs) : "";
    }

    let actionSel = $state<string | null>(null);
    let linkedSel = $state<string | null>(null);
    let actionOpen = $state(false);
    let linkedOpen = $state(false);

    let pairs = $derived(getPairs());
    let mode = $derived((filters as any).actionPairMode as 'any'|'all' ?? 'any');

    function addPair() {
        if (!actionSel && !linkedSel) return;
        const next = [...pairs, { action: actionSel, linked: linkedSel }];
        setPairs(next);
        actionSel = null; linkedSel = null;
    }
    function removePair(i: number) {
        const next = pairs.filter((_, idx) => idx !== i);
        setPairs(next);
    }
</script>

<div class="space-y-2.5">
    <div class="flex items-center justify-between gap-2">
        <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80">Actions</span>
        {#if pairs.length > 1}
            <FilterAnyAllToggle bind:value={(filters as any).actionPairMode} />
        {/if}
    </div>

    <!-- Existing pairs as pills -->
    {#if pairs.length > 0}
        <div class="flex flex-wrap gap-1.5">
            {#each pairs as p, i}
                <span class="inline-flex items-center gap-1.5 pl-2 pr-1 py-1 rounded-full bg-white/[0.08] border border-white/10 text-[11px] font-mono text-primary">
                    {#if p.action}
                        <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(p.action)} text-[12px] leading-none" aria-hidden="true"></i>
                        <span>{p.action}</span>
                    {:else}
                        <span class="text-secondary/60">Any</span>
                    {/if}
                    {#if p.linked}
                        <span class="text-secondary/40">→</span>
                        <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(p.linked)} text-[12px] leading-none" aria-hidden="true"></i>
                        <span>{p.linked}</span>
                    {/if}
                    <button type="button" onclick={() => removePair(i)} class="w-4 h-4 rounded-full hover:bg-white/15 inline-flex items-center justify-center ml-0.5" aria-label="Remove">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                    </button>
                </span>
            {/each}
        </div>
    {/if}

    <!-- Composer — custom dropdowns with icons -->
    <div class="flex flex-wrap items-end gap-2">
        <div class="flex flex-col gap-1 flex-1 min-w-[130px]">
            <span class="text-[10px] font-mono text-secondary/60">Action</span>
            <div class="relative">
                <button type="button" onclick={() => (actionOpen = !actionOpen)} onblur={() => setTimeout(() => (actionOpen = false), 140)} class="w-full flex items-center justify-between gap-2 bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none pr-7">
                    <span class="flex items-center gap-1.5 truncate">
                        {#if actionSel}
                            <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(actionSel)} text-[12px] leading-none" aria-hidden="true"></i>
                            <span class="truncate">{actionSel}</span>
                        {:else}
                            <span class="text-secondary/60">Any / —</span>
                        {/if}
                    </span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {actionOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
                </button>
                {#if actionOpen}
                    <div class="absolute z-[80] mt-1 w-full max-h-[200px] overflow-y-auto rounded-md border border-border-dark bg-terminal-panel shadow-xl">
                        <button type="button" onmousedown={(e) => { e.preventDefault(); actionSel = null; actionOpen = false; }} class="w-full text-left px-2 py-1.5 text-xs font-mono hover:bg-white/[0.06] flex items-center gap-2 {actionSel === null ? 'text-primary bg-white/[0.04]' : 'text-secondary'}">
                            <span class="text-secondary/60 w-[12px] text-center">—</span><span>Any / —</span>
                        </button>
                        {#each ACTION_OPTIONS as a}
                            {@const sel = actionSel === a}
                            <button type="button" onmousedown={(e) => { e.preventDefault(); actionSel = a; actionOpen = false; }} class="w-full text-left px-2 py-1.5 text-xs font-mono hover:bg-white/[0.06] flex items-center gap-2 {sel ? 'text-primary bg-white/[0.04]' : 'text-secondary'}">
                                <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(a)} text-[12px] leading-none" aria-hidden="true"></i><span class="flex-1">{a}</span>{#if sel}<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="shrink-0"><path d="M5 12 10 17 19 7"/></svg>{/if}
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>
        </div>
        <span class="text-secondary/40 pb-2">→</span>
        <div class="flex flex-col gap-1 flex-1 min-w-[130px]">
            <span class="text-[10px] font-mono text-secondary/60">Linked action</span>
            <div class="relative">
                <button type="button" onclick={() => (linkedOpen = !linkedOpen)} onblur={() => setTimeout(() => (linkedOpen = false), 140)} class="w-full flex items-center justify-between gap-2 bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none pr-7">
                    <span class="flex items-center gap-1.5 truncate">
                        {#if linkedSel}
                            <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(linkedSel)} text-[12px] leading-none" aria-hidden="true"></i>
                            <span class="truncate">{linkedSel}</span>
                        {:else}
                            <span class="text-secondary/60">— none</span>
                        {/if}
                    </span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {linkedOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
                </button>
                {#if linkedOpen}
                    <div class="absolute z-[80] mt-1 w-full max-h-[200px] overflow-y-auto rounded-md border border-border-dark bg-terminal-panel shadow-xl">
                        <button type="button" onmousedown={(e) => { e.preventDefault(); linkedSel = null; linkedOpen = false; }} class="w-full text-left px-2 py-1.5 text-xs font-mono hover:bg-white/[0.06] flex items-center gap-2 {linkedSel === null ? 'text-primary bg-white/[0.04]' : 'text-secondary'}">
                            <span class="text-secondary/60 w-[12px] text-center">—</span><span>— none</span>
                        </button>
                        {#each ACTION_OPTIONS as a}
                            {@const sel = linkedSel === a}
                            <button type="button" onmousedown={(e) => { e.preventDefault(); linkedSel = a; linkedOpen = false; }} class="w-full text-left px-2 py-1.5 text-xs font-mono hover:bg-white/[0.06] flex items-center gap-2 {sel ? 'text-primary bg-white/[0.04]' : 'text-secondary'}">
                                <i class="xwing-miniatures-font xwing-miniatures-font-{actionToFont(a)} text-[12px] leading-none" aria-hidden="true"></i><span class="flex-1">{a}</span>{#if sel}<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="shrink-0"><path d="M5 12 10 17 19 7"/></svg>{/if}
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>
        </div>
        <button type="button" onclick={addPair} disabled={!actionSel && !linkedSel} class="px-3 py-1.5 rounded-full bg-white text-black text-xs font-mono font-bold disabled:opacity-30 disabled:cursor-not-allowed hover:bg-white/90">Add</button>
    </div>
</div>
