<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
    import FilterAnyAllToggle from "./FilterAnyAllToggle.svelte";

    type Entry = { slot: string; count: number };
    // slotCounts JSON string stored in filters.slotCounts; legacy selectedSlots kept for migration.

    const SLOT_OPTIONS = [
        "Astromech","Cannon","Cargo","Command","Configuration","Crew","Device","Force Power","Gunner","Hardpoint","Hyperdrive","Illicit","Missile","Modification","Payload","Sensor","Tactical Relay","Talent","Team","Tech","Title","Torpedo","Turret",
    ];

    function slotToFont(s: string): string {
        const map: Record<string,string> = {
            "astromech":"astromech","cannon":"cannon","cargo":"cargo","command":"command","configuration":"config","crew":"crew","device":"device","force power":"forcepower","gunner":"gunner","hardpoint":"hardpoint","hyperdrive":"hardpoint","illicit":"illicit","missile":"missile","modification":"modification","payload":"device","sensor":"sensor","tactical relay":"tacticalrelay","talent":"talent","team":"team","tech":"tech","title":"title","torpedo":"torpedo","turret":"turret",
        };
        return map[s.toLowerCase()] ?? "modification";
    }

    function getEntries(): Entry[] {
        try {
            const raw = (filters as any).slotCounts as string;
            if (!raw) return [];
            return JSON.parse(raw) as Entry[];
        } catch { return []; }
    }
    function setEntries(entries: Entry[]) {
        (filters as any).slotCounts = entries.length ? JSON.stringify(entries) : "";
    }

    let slotSel = $state<string>("Talent");
    let countSel = $state<number>(1);
    let slotOpen = $state(false);

    let entries = $derived(getEntries());

    function addEntry() {
        if (!slotSel) return;
        const next = [...entries, { slot: slotSel, count: Math.max(1, countSel|0) }];
        setEntries(next);
    }
    function removeEntry(i: number) {
        setEntries(entries.filter((_, idx) => idx !== i));
    }
</script>

<div class="space-y-2.5">
    <div class="flex items-center justify-between gap-2">
        <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80">Available Slots</span>
        {#if entries.length > 1}
            <FilterAnyAllToggle bind:value={(filters as any).slotCountMode} />
        {/if}
    </div>

    {#if entries.length > 0}
        <div class="flex flex-wrap gap-1.5">
            {#each entries as e, i}
                <span class="inline-flex items-center gap-1.5 pl-2 pr-1 py-1 rounded-full bg-white/[0.08] border border-white/10 text-[11px] font-mono text-primary">
                    <i class="xwing-miniatures-font xwing-miniatures-font-{slotToFont(e.slot)} text-[12px] leading-none" aria-hidden="true"></i>
                    <span>{e.slot} ×{e.count}</span>
                    <button type="button" onclick={() => removeEntry(i)} class="w-4 h-4 rounded-full hover:bg-white/15 inline-flex items-center justify-center ml-0.5" aria-label="Remove">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                    </button>
                </span>
            {/each}
        </div>
    {/if}

    <div class="flex flex-wrap items-end gap-2">
        <div class="flex flex-col gap-1 flex-1 min-w-[140px]">
            <span class="text-[10px] font-mono text-secondary/60">Slot</span>
            <div class="relative">
                <button type="button" onclick={() => (slotOpen = !slotOpen)} onblur={() => setTimeout(() => (slotOpen = false), 140)} class="w-full flex items-center justify-between gap-2 bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none pr-7">
                    <span class="flex items-center gap-1.5 truncate">
                        <i class="xwing-miniatures-font xwing-miniatures-font-{slotToFont(slotSel)} text-[12px] leading-none" aria-hidden="true"></i>
                        <span class="truncate">{slotSel}</span>
                    </span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-secondary transition-transform {slotOpen ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
                </button>
                {#if slotOpen}
                    <div class="absolute z-[80] mt-1 w-full max-h-[200px] overflow-y-auto rounded-md border border-border-dark bg-terminal-panel shadow-xl">
                        {#each SLOT_OPTIONS as s}
                            {@const sel = slotSel === s}
                            <button type="button" onmousedown={(e) => { e.preventDefault(); slotSel = s; slotOpen = false; }} class="w-full text-left px-2 py-1.5 text-xs font-mono hover:bg-white/[0.06] flex items-center gap-2 {sel ? 'text-primary bg-white/[0.04]' : 'text-secondary'}">
                                <i class="xwing-miniatures-font xwing-miniatures-font-{slotToFont(s)} text-[12px] leading-none" aria-hidden="true"></i><span class="flex-1">{s}</span>{#if sel}<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="shrink-0"><path d="M5 12 10 17 19 7"/></svg>{/if}
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>
        </div>
        <label class="flex flex-col gap-1 w-[90px]">
            <span class="text-[10px] font-mono text-secondary/60">Count</span>
            <input type="number" min="1" max="9" class="bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none" bind:value={countSel} />
        </label>
        <button type="button" onclick={addEntry} class="px-3 py-1.5 rounded-full bg-white text-black text-xs font-mono font-bold hover:bg-white/90">Add</button>
    </div>
</div>
