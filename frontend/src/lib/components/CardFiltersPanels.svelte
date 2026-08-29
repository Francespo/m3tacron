<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
    import Toggle from "./Toggle.svelte";
    import MultiSelectPills from "./MultiSelectPills.svelte";
    import ActionPairFilter from "./ActionPairFilter.svelte";
    import SlotCountFilter from "./SlotCountFilter.svelte";

    let { isPilotsTab = true }: { isPilotsTab?: boolean } = $props();

    function toggleBaseSize(size: string) {
        if (filters.selectedBaseSizes.includes(size)) {
            filters.selectedBaseSizes = filters.selectedBaseSizes.filter((s) => s !== size);
        } else {
            filters.selectedBaseSizes = [...filters.selectedBaseSizes, size];
        }
    }

    const SLOT_OPTIONS = [
        "Astromech","Cannon","Cargo","Command","Configuration","Crew","Device","Force Power","Gunner","Hardpoint","Hyperdrive","Illicit","Missile","Modification","Payload","Sensor","Tactical Relay","Talent","Team","Tech","Title","Torpedo","Turret",
    ];
    const KEYWORD_OPTIONS = [
        "A-wing","B-wing","Bounty Hunter","Clone","Dark Side","Droid","Freighter","Jedi","Light Side","Mandalorian","Partisan","Sith","Spectre","TIE","X-wing","Y-wing","YT-1300",
    ];
    const ACTION_OPTIONS = [
        "Barrel Roll","Boost","Calculate","Cloak","Coordinate","Evade","Focus","Jam","Lock","Reinforce","Reload","Rotate Arc","SLAM",
    ];

    const ARCS = [
        { label: "Front Arc", font: "frontarc", minKey: "frontArcMin" as const, maxKey: "frontArcMax" as const },
        { label: "Single Turret", font: "singleturretarc", minKey: "singleTurretMin" as const, maxKey: "singleTurretMax" as const },
        { label: "Double Turret", font: "doubleturretarc", minKey: "doubleTurretMin" as const, maxKey: "doubleTurretMax" as const },
        { label: "Full Front", font: "fullfrontarc", minKey: "fullFrontMin" as const, maxKey: "fullFrontMax" as const },
        { label: "Rear Arc", font: "reararc", minKey: "rearArcMin" as const, maxKey: "rearArcMax" as const },
        { label: "Bullseye", font: "bullseyearc", minKey: "bullseyeMin" as const, maxKey: "bullseyeMax" as const },
    ];

    const STAT_ROWS = [
        { label: "Initiative", min: "initMin" as const, max: "initMax" as const, color: "#fb923c", font: null as string|null },
        { label: "Hull", min: "hullMin" as const, max: "hullMax" as const, color: "#facc15", font: "hull" },
        { label: "Shields", min: "shieldsMin" as const, max: "shieldsMax" as const, color: "#60a5fa", font: "shield" },
        { label: "Agility", min: "agilityMin" as const, max: "agilityMax" as const, color: "#4ade80", font: "agility" },
    ];
    // Point/Loadout banner colors (match Upgrade/Pilot card PTS/LV badges)
    const POINTS_COLOR = "#34d399"; // emerald-400
    const LOADOUT_COLOR = "#a78bfa"; // violet-400

    // Helpers for slot/action icon mapping (use StatIcon charMap keys)
    function slotToIconType(slot: string): string {
        return slot.toLowerCase().replace(/\s+/g, "");
    }
    function actionToIconType(action: string): string {
        return action.toLowerCase().replace(/\s+/g, "");
    }
</script>

<div class="w-full space-y-4">
    <div class="flex items-center gap-2">
        <span class="text-[11px] font-bold tracking-[0.14em] text-secondary font-mono uppercase">Advanced Filters</span>
        <span class="flex-1 h-px bg-white/5 ml-2"></span>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-4">

        <!-- Card 1: Cost & Legality -->
        <div class="space-y-3 rounded-xl border border-white/5 bg-black/15 p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
            <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80">Cost &amp; Legality</span>

            <div class="space-y-1">
                <span class="text-[10px] font-bold font-mono tracking-wider uppercase flex items-center gap-1.5" style="color: {POINTS_COLOR};">Points Cost</span>
                <div class="flex items-center gap-2">
                    <span class="text-xs text-secondary font-mono">from</span>
                    <input type="number" class="w-[60px] bg-black rounded px-2 py-1 text-xs font-mono focus:outline-none" style="border: 1px solid {POINTS_COLOR}33; color: {POINTS_COLOR};" bind:value={filters.pointsMin} placeholder="—" />
                    <span class="text-xs text-secondary font-mono">to</span>
                    <input type="number" class="w-[60px] bg-black rounded px-2 py-1 text-xs font-mono focus:outline-none" style="border: 1px solid {POINTS_COLOR}33; color: {POINTS_COLOR};" bind:value={filters.pointsMax} placeholder="—" />
                </div>
            </div>

            {#if isPilotsTab && filters.dataSource === "xwa"}
                <div class="space-y-1">
                    <span class="text-[10px] font-bold font-mono tracking-wider uppercase flex items-center gap-1.5" style="color: {LOADOUT_COLOR};">Loadout Value</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-secondary font-mono">from</span>
                        <input type="number" class="w-[60px] bg-black rounded px-2 py-1 text-xs font-mono focus:outline-none" style="border: 1px solid {LOADOUT_COLOR}33; color: {LOADOUT_COLOR};" bind:value={filters.loadoutMin} placeholder="—" />
                        <span class="text-xs text-secondary font-mono">to</span>
                        <input type="number" class="w-[60px] bg-black rounded px-2 py-1 text-xs font-mono focus:outline-none" style="border: 1px solid {LOADOUT_COLOR}33; color: {LOADOUT_COLOR};" bind:value={filters.loadoutMax} placeholder="—" />
                    </div>
                </div>
            {/if}

            <div class="space-y-1.5">
                <span class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase">Copies</span>
                <div class="flex items-center gap-4 flex-wrap">
                    <label class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary">
                        <Toggle size="xs" ariaLabel="Toggle Unique" checked={filters.isUnique} onchange={(e) => (filters.isUnique = (e.currentTarget as HTMLInputElement).checked)} />
                        <span class="font-mono">Unique (•)</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary">
                        <Toggle size="xs" ariaLabel="Toggle Limited" checked={filters.isLimited} onchange={(e) => (filters.isLimited = (e.currentTarget as HTMLInputElement).checked)} />
                        <span class="font-mono">Limited (2+)</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary">
                        <Toggle size="xs" ariaLabel="Toggle Generic" checked={filters.isGeneric} onchange={(e) => (filters.isGeneric = (e.currentTarget as HTMLInputElement).checked)} />
                        <span class="font-mono">Generic</span>
                    </label>
                </div>
            </div>

            <label class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary">
                <Toggle size="xs" ariaLabel="Toggle Include Epic Only Content" checked={filters.includeEpic} onchange={(e) => (filters.includeEpic = (e.currentTarget as HTMLInputElement).checked)} />
                <span class="font-mono">Include epic only content</span>
            </label>

            {#if isPilotsTab}
                <div class="space-y-1">
                    <span class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase">Base Size</span>
                    <div class="flex items-center gap-4">
                        {#each ["S", "M", "L", "H"] as size}
                            <label class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary">
                                <Toggle size="xs" ariaLabel={`Toggle base size ${size}`} checked={filters.selectedBaseSizes.includes(size)} onchange={() => toggleBaseSize(size)} />
                                <span class="font-mono">{size}</span>
                            </label>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>

        <!-- Card 2: Traits & Loadout — only on Pilots tab (no empty filler on Upgrades) -->
        {#if isPilotsTab}
            <div class="space-y-3 rounded-xl border border-white/5 bg-black/15 p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80">Traits &amp; Loadout</span>
                <SlotCountFilter />
                <MultiSelectPills label="Keywords" options={KEYWORD_OPTIONS} bind:selected={filters.selectedKeywords} bind:mode={filters.keywordFilterMode} placeholder="Search keywords…" />
                <ActionPairFilter />
            </div>
        {/if}

        <!-- Stat ranges (cards) — in the hole (top-right col 3) — stacked with no Resources duplicate -->
        <div class="rounded-xl border border-white/5 bg-black/15 p-3.5 space-y-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] lg:col-span-2 2xl:col-span-1 2xl:col-start-3 2xl:row-start-1 self-start min-w-0">
            <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80">Stat ranges (cards)</span>
            <div class="flex flex-col gap-2.5">
                {#each [
                    { key: 'Lists', min: 'listsMin', max: 'listsMax' },
                    { key: 'Entries', min: 'entriesMin', max: 'entriesMax' },
                    { key: 'Games', min: 'gamesMin', max: 'gamesMax' },
                    { key: 'Win %', min: 'winRateMin', max: 'winRateMax' },
                ] as row}
                    <label class="flex items-center gap-2 min-w-0">
                        <span class="text-[10px] font-mono font-bold tracking-widest uppercase text-secondary/70 w-[3.8rem] shrink-0">{row.key}</span>
                        <span class="text-[10px] font-mono text-secondary shrink-0">from</span>
                        <input type="number" inputmode="numeric" placeholder="—" class="flex-1 min-w-0 bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" value={(filters as any)[row.min]} oninput={(e) => ((filters as any)[row.min] = (e.currentTarget as HTMLInputElement).value)} />
                        <span class="text-[10px] font-mono text-secondary shrink-0">to</span>
                        <input type="number" inputmode="numeric" placeholder="—" class="flex-1 min-w-0 bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" value={(filters as any)[row.max]} oninput={(e) => ((filters as any)[row.max] = (e.currentTarget as HTMLInputElement).value)} />
                    </label>
                {/each}
            </div>
        </div>

        <!-- Card 4: Stats — compact: two columns on xl — left: hull/agility+initiative/shields, right: Arcs -->
        {#if isPilotsTab}
            <div class="lg:col-span-2 2xl:col-span-3 rounded-xl border border-white/5 bg-black/15 p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] space-y-3">
                <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80">Stats</span>
                <div class="grid grid-cols-1 xl:grid-cols-2 gap-2">
                    <!-- Left: 6 capsules — Initiative/Hull/Shields/Agility/Charges/Force (equal height, equal gap) -->
                    <div class="grid grid-cols-1 gap-2 content-start auto-rows-fr">
                        {#each STAT_ROWS as row}
                            <label class="flex items-center gap-2 rounded-lg border border-white/5 bg-black/15 px-2 py-2 min-h-[36px]">
                                <span class="flex items-center gap-1.5 w-[6.2rem] shrink-0">
                                    {#if row.font}
                                        <i class="xwing-miniatures-font xwing-miniatures-font-{row.font} text-sm leading-none" style="color: {row.color};" aria-hidden="true"></i>
                                    {/if}
                                    <span class="text-[10px] font-bold font-mono uppercase tracking-wider" style="color: {row.color};">{row.label}</span>
                                </span>
                                <span class="text-[10px] font-mono text-secondary/70">from</span>
                                <input type="number" inputmode="numeric" placeholder="—" class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" bind:value={(filters as any)[row.min]} aria-label="{row.label} min" />
                                <span class="text-[10px] font-mono text-secondary/70">to</span>
                                <input type="number" inputmode="numeric" placeholder="—" class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" bind:value={(filters as any)[row.max]} aria-label="{row.label} max" />
                            </label>
                        {/each}
                        <label class="flex items-center gap-2 rounded-lg border border-white/5 bg-black/15 px-2 py-2 min-h-[36px]">
                            <span class="flex items-center gap-1.5 w-[6.2rem] shrink-0">
                                <i class="xwing-miniatures-font xwing-miniatures-font-charge text-sm leading-none" style="text-transform:none; color:#facc15" aria-hidden="true"></i>
                                <span class="text-[10px] font-bold font-mono uppercase tracking-wider" style="color:#facc15">Charges</span>
                            </span>
                            <span class="text-[10px] font-mono text-secondary/70">from</span>
                            <input type="number" inputmode="numeric" placeholder="—" class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" bind:value={filters.chargesMin} aria-label="Charges min" />
                            <span class="text-[10px] font-mono text-secondary/70">to</span>
                            <input type="number" inputmode="numeric" placeholder="—" class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" bind:value={filters.chargesMax} aria-label="Charges max" />
                        </label>
                        <label class="flex items-center gap-2 rounded-lg border border-white/5 bg-black/15 px-2 py-1.5 min-h-[36px]">
                            <span class="flex items-center gap-1.5 w-[6.2rem] shrink-0">
                                <i class="xwing-miniatures-font xwing-miniatures-font-forcecharge text-sm leading-none" style="text-transform:none; color:#a78bfa" aria-hidden="true"></i>
                                <span class="text-[10px] font-bold font-mono uppercase tracking-wider" style="color:#a78bfa">Force</span>
                            </span>
                            <span class="text-[10px] font-mono text-secondary/70">from</span>
                            <input type="number" inputmode="numeric" placeholder="—" class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" bind:value={filters.forceMin} aria-label="Force min" />
                            <span class="text-[10px] font-mono text-secondary/70">to</span>
                            <input type="number" inputmode="numeric" placeholder="—" class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" bind:value={filters.forceMax} aria-label="Force max" />
                        </label>
                    </div>
                    <!-- Right: 6 Arcs — same count/height/gap as left for equal vertical space -->
                    <div class="grid grid-cols-1 gap-2 content-start auto-rows-fr">
                        {#each ARCS as arc}
                            <label class="flex items-center gap-1.5 rounded-lg border border-white/5 bg-black/15 px-2 py-2 min-h-[36px]">
                                <span class="flex items-center gap-1.5 w-[6.2rem] shrink-0">
                                    <i class="xwing-miniatures-font xwing-miniatures-font-{arc.font} text-sm leading-none" style="color:#f87171" aria-hidden="true"></i>
                                    <span class="text-[10px] font-bold font-mono uppercase tracking-wider" style="color:#f87171">{arc.label}</span>
                                </span>
                                <span class="text-[10px] font-mono text-secondary/70">from</span>
                                <input type="number" inputmode="numeric" placeholder="—" class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" value={(filters as any)[arc.minKey]} oninput={(e) => ((filters as any)[arc.minKey] = (e.currentTarget as HTMLInputElement).value)} aria-label="{arc.label} min" />
                                <span class="text-[10px] font-mono text-secondary/70">to</span>
                                <input type="number" inputmode="numeric" placeholder="—" class="w-[48px] bg-black border border-border-dark rounded px-1.5 py-1 text-xs font-mono text-primary placeholder:text-secondary/40 focus:border-primary focus:outline-none" value={(filters as any)[arc.maxKey]} oninput={(e) => ((filters as any)[arc.maxKey] = (e.currentTarget as HTMLInputElement).value)} aria-label="{arc.label} max" />
                            </label>
                        {/each}
                    </div>
                </div>
            </div>
        {/if}

        <!-- Card 5: Upgrade Slots — only on Upgrades tab (no filler on Pilots) -->
        {#if !isPilotsTab}
            <div class="space-y-3 rounded-xl border border-white/5 bg-black/15 p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <span class="text-[10px] font-bold tracking-widest uppercase font-mono text-secondary/80">Upgrade Slots</span>
                <MultiSelectPills label="Used Slot" options={SLOT_OPTIONS} bind:selected={filters.selectedUsedSlots} bind:mode={filters.usedSlotFilterMode} placeholder="No slots selected" iconTypeFor={slotToIconType} />
                <MultiSelectPills label="Used Double-Slot" options={SLOT_OPTIONS} bind:selected={filters.selectedUsedDoubleSlots} bind:mode={filters.usedDoubleSlotFilterMode} placeholder="No slots selected" iconTypeFor={slotToIconType} />
                <label class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary pt-1">
                    <Toggle size="xs" ariaLabel="Toggle Only multi-slot" checked={filters.onlyMultiSlot} onchange={(e) => (filters.onlyMultiSlot = (e.currentTarget as HTMLInputElement).checked)} />
                    <span class="font-mono">Only upgrades requiring multiple slots</span>
                </label>
            </div>
        {/if}
    </div>
</div>
