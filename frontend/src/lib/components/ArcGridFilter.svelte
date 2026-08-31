<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";

    // Compact 2–3 column grid of per-arc from→to inputs, OR between arcs.
    const arcs = [
        { label: "Front Arc", minKey: "frontArcMin" as const, maxKey: "frontArcMax" as const },
        { label: "Single Turret", minKey: "singleTurretMin" as const, maxKey: "singleTurretMax" as const },
        { label: "Double Turret", minKey: "doubleTurretMin" as const, maxKey: "doubleTurretMax" as const },
        { label: "Full Front", minKey: "fullFrontMin" as const, maxKey: "fullFrontMax" as const },
        { label: "Rear Arc", minKey: "rearArcMin" as const, maxKey: "rearArcMax" as const },
        { label: "Bullseye", minKey: "bullseyeMin" as const, maxKey: "bullseyeMax" as const },
    ];
</script>

<div class="space-y-2">
    <div class="flex items-center justify-between gap-2">
        <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80">Armament — Arcs</span>
        <span class="text-[10px] font-mono text-secondary/50">Any matching arc (OR)</span>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2.5">
        {#each arcs as arc}
            <label class="flex items-center gap-1.5 rounded-lg border border-white/5 bg-black/15 px-2 py-2">
                <span class="text-[10px] font-bold font-mono uppercase tracking-wider text-secondary w-[5.2rem] shrink-0">{arc.label}</span>
                <span class="text-[10px] font-mono text-secondary/70">from</span>
                <input
                    type="number"
                    inputmode="numeric"
                    placeholder="—"
                    class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none"
                    value={(filters as any)[arc.minKey]}
                    oninput={(e) => ((filters as any)[arc.minKey] = (e.currentTarget as HTMLInputElement).value)}
                    aria-label="{arc.label} min"
                />
                <span class="text-[10px] font-mono text-secondary/70">to</span>
                <input
                    type="number"
                    inputmode="numeric"
                    placeholder="—"
                    class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none"
                    value={(filters as any)[arc.maxKey]}
                    oninput={(e) => ((filters as any)[arc.maxKey] = (e.currentTarget as HTMLInputElement).value)}
                    aria-label="{arc.label} max"
                />
            </label>
        {/each}
    </div>
    <p class="text-[10px] font-mono leading-relaxed text-secondary/50">Empty cells are ignored. A pilot matches if <span class="text-secondary">any</span> specified arc is in range.</p>
</div>
