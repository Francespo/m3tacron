<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
    import Toggle from "./Toggle.svelte";
    import FactionIcon from "./FactionIcon.svelte";
    import { ALL_FACTIONS, getFactionLabel } from "$lib/data/factions";
    import {
        CARD_SLOT_TYPES,
        PILOT_KEYWORDS,
        PILOT_ACTIONS,
        PILOT_LINKED_ACTIONS,
        PILOT_ARC_ICONS,
    } from "$lib/data/cardFilters";
    import type { Snippet } from "svelte";

    let { isPilotsTab = true }: { isPilotsTab?: boolean } = $props();

    // ------------------------------------------------------------------
    // Collapsible group + dropdown state
    // ------------------------------------------------------------------
    // General is open by default; the deeper groups start collapsed so the
    // panel reads cleanly ("cleaner than YASB") with everything one click
    // away.
    let groupsOpen = $state<Record<string, boolean>>({
        General: true,
        "Ships & Pilots": false,
        Upgrades: false,
        Data: false,
    });

    function toggleGroup(name: string) {
        groupsOpen[name] = !groupsOpen[name];
    }

    // Only one multi-select dropdown open at a time.
    let openDropdown = $state<string | null>(null);

    function toggleDropdown(name: string) {
        openDropdown = openDropdown === name ? null : name;
    }

    function toggleIn(
        listName:
            | "selectedSlots"
            | "selectedKeywords"
            | "selectedActions"
            | "selectedLinkedActions"
            | "selectedArcs"
            | "selectedUpgradeTypes"
            | "selectedFactions",
        value: string,
    ) {
        const current = filters[listName] as unknown as string[];
        filters[listName] = current.includes(value)
            ? current.filter((v) => v !== value)
            : [...current, value];
    }

    function toggleBaseSize(size: string) {
        if (filters.selectedBaseSizes.includes(size)) {
            filters.selectedBaseSizes = filters.selectedBaseSizes.filter(
                (s) => s !== size,
            );
        } else {
            filters.selectedBaseSizes = [...filters.selectedBaseSizes, size];
        }
    }

    // ------------------------------------------------------------------
    // Range inputs — every stat range is clamped at 0 (stats never go
    // below zero; the input refuses/clears anything negative).
    // ------------------------------------------------------------------
    function clampNonNegative(e: Event): string {
        const input = e.currentTarget as HTMLInputElement;
        const raw = input.value.trim();
        if (raw === "") return "";
        const n = Number(raw);
        if (Number.isNaN(n)) {
            input.value = "";
            return "";
        }
        if (n < 0) {
            input.value = "0";
            return "0";
        }
        return raw;
    }
</script>

    // ------------------------------------------------------------------
    // Reusable snippets
    // ------------------------------------------------------------------
    {#snippet group(title: string, children: Snippet)}
        <div class="border border-border-dark rounded-md overflow-hidden">
            <button
                class="flex items-center justify-between w-full px-3 py-2 text-secondary hover:text-primary transition-colors"
                onclick={() => toggleGroup(title)}
                aria-expanded={groupsOpen[title]}
            >
                <span
                    class="text-[10px] font-bold text-primary font-mono tracking-wider uppercase"
                    >{title}</span
                >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="transition-transform {groupsOpen[title]
                        ? 'rotate-180'
                        : ''}"
                    ><path d="m6 9 6 6 6-6" /></svg
                >
            </button>
            {#if groupsOpen[title]}
                <div class="px-3 pb-3 space-y-3">
                    {@render children()}
                </div>
            {/if}
        </div>
    {/snippet}

    {#snippet rangeRow(label: string, minVal: string, onMin: (v: string) => void, maxVal: string, onMax: (v: string) => void)}
        <div class="flex items-center gap-2 w-full">
            <span
                class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase w-24 flex-shrink-0"
                >{label}:</span
            >
            <input
                type="number"
                min="0"
                value={minVal}
                oninput={(e) => onMin(clampNonNegative(e))}
                class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
            />
            <span class="text-xs text-secondary font-mono">to</span>
            <input
                type="number"
                min="0"
                value={maxVal}
                oninput={(e) => onMax(clampNonNegative(e))}
                class="w-[50px] bg-black border border-border-dark rounded px-2 py-1 text-xs font-mono text-primary focus:border-primary focus:outline-none"
            />
        </div>
    {/snippet}

    {#snippet multiSelect(label: string, options: string[], selected: string[], onToggle: (opt: string) => void)}
        <div class="space-y-1">
            <button
                class="flex items-center justify-between w-full py-1 text-secondary hover:text-primary transition-colors"
                onclick={() => toggleDropdown(label)}
                aria-expanded={openDropdown === label}
            >
                <span
                    class="text-[10px] font-bold text-primary font-mono tracking-wider uppercase opacity-70"
                    >{label}</span
                >
                {#if selected.length > 0}
                    <span
                        class="text-[10px] bg-white/10 text-secondary px-1.5 rounded-full font-mono"
                        >{selected.length}</span
                    >
                {/if}
            </button>
            {#if openDropdown === label}
                <div
                    class="space-y-1 max-h-[180px] overflow-y-auto custom-scrollbar pl-2"
                >
                    {#each options as opt}
                        <label
                            class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                        >
                            <Toggle
                                size="xs"
                                ariaLabel={`Toggle ${label} ${opt}`}
                                checked={selected.includes(opt)}
                                onchange={() => onToggle(opt)}
                            />
                            <span class="font-mono">{opt}</span>
                        </label>
                    {/each}
                </div>
            {/if}
        </div>
    {/snippet}

    {#snippet generalBody()}
        <!-- Faction multi-select -->
        <div class="space-y-1">
            <button
                class="flex items-center justify-between w-full py-1 text-secondary hover:text-primary transition-colors"
                onclick={() => toggleDropdown("Faction")}
                aria-expanded={openDropdown === "Faction"}
            >
                <span
                    class="text-[10px] font-bold text-primary font-mono tracking-wider uppercase opacity-70"
                    >Faction</span
                >
                {#if filters.selectedFactions.length > 0}
                    <span
                        class="text-[10px] bg-white/10 text-secondary px-1.5 rounded-full font-mono"
                        >{filters.selectedFactions.length}</span
                    >
                {/if}
            </button>
            {#if openDropdown === "Faction"}
                <div
                    class="space-y-1 max-h-[180px] overflow-y-auto custom-scrollbar pl-2"
                >
                    {#each ALL_FACTIONS as f}
                        <label
                            class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
                        >
                            <Toggle
                                size="xs"
                                ariaLabel={`Toggle faction ${getFactionLabel(f)}`}
                                checked={filters.selectedFactions.includes(f)}
                                onchange={() => toggleIn("selectedFactions", f)}
                            />
                            <FactionIcon faction={f} size="sm" />
                            <span class="font-mono">{getFactionLabel(f)}</span>
                        </label>
                    {/each}
                </div>
            {/if}
        </div>

        <!-- Point Costs (Range) -->
        {@render rangeRow(
            "Point Cost",
            filters.pointsMin,
            (v) => (filters.pointsMin = v),
            filters.pointsMax,
            (v) => (filters.pointsMax = v),
        )}

        <!-- Loadout Value (XWA Pilots Only) -->
        {#if isPilotsTab && filters.dataSource === "xwa"}
            {@render rangeRow(
                "Loadout",
                filters.loadoutMin,
                (v) => (filters.loadoutMin = v),
                filters.loadoutMax,
                (v) => (filters.loadoutMax = v),
            )}
        {/if}

        <!-- Unique / Limited / Standard-legal toggles -->
        <div class="space-y-1">
            <span
                class="text-[10px] font-bold text-primary font-mono tracking-wider opacity-70 uppercase"
                >Legality</span
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
                        ariaLabel="Toggle Standard-legal"
                        checked={filters.isStandardLegal}
                        onchange={(e) => (filters.isStandardLegal = (e.currentTarget as HTMLInputElement).checked)}
                    />
                    <span class="font-mono">Standard-legal</span>
                </label>
            </div>
        </div>
    {/snippet}

    {#snippet shipsPilotsBody()}
        {@render multiSelect(
            "Slots",
            CARD_SLOT_TYPES,
            filters.selectedSlots,
            (opt) => toggleIn("selectedSlots", opt),
        )}
        {@render multiSelect(
            "Keywords",
            PILOT_KEYWORDS,
            filters.selectedKeywords,
            (opt) => toggleIn("selectedKeywords", opt),
        )}
        {@render multiSelect(
            "Actions",
            PILOT_ACTIONS,
            filters.selectedActions,
            (opt) => toggleIn("selectedActions", opt),
        )}
        {@render multiSelect(
            "Linked Actions",
            PILOT_LINKED_ACTIONS,
            filters.selectedLinkedActions,
            (opt) => toggleIn("selectedLinkedActions", opt),
        )}

        <!-- Stat ranges -->
        {@render rangeRow(
            "Initiative",
            filters.initMin,
            (v) => (filters.initMin = v),
            filters.initMax,
            (v) => (filters.initMax = v),
        )}
        {@render rangeRow(
            "Hull",
            filters.hullMin,
            (v) => (filters.hullMin = v),
            filters.hullMax,
            (v) => (filters.hullMax = v),
        )}
        {@render rangeRow(
            "Shields",
            filters.shieldsMin,
            (v) => (filters.shieldsMin = v),
            filters.shieldsMax,
            (v) => (filters.shieldsMax = v),
        )}
        {@render rangeRow(
            "Agility",
            filters.agilityMin,
            (v) => (filters.agilityMin = v),
            filters.agilityMax,
            (v) => (filters.agilityMax = v),
        )}

        <!-- Base Size -->
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

        <!-- Arc icons -->
        {@render multiSelect(
            "Arc Icons",
            PILOT_ARC_ICONS,
            filters.selectedArcs,
            (opt) => toggleIn("selectedArcs", opt),
        )}
    {/snippet}

    {#snippet upgradesBody()}
        {@render multiSelect(
            "Used Slot",
            CARD_SLOT_TYPES,
            filters.selectedUpgradeTypes,
            (opt) => toggleIn("selectedUpgradeTypes", opt),
        )}

        <div class="space-y-1">
            <label
                class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
            >
                <Toggle
                    size="xs"
                    ariaLabel="Toggle double-slot"
                    checked={filters.isDoubleSlot}
                    onchange={(e) => (filters.isDoubleSlot = (e.currentTarget as HTMLInputElement).checked)}
                />
                <span class="font-mono">Double-slot</span>
            </label>
        </div>

        {@render rangeRow(
            "Charges",
            filters.chargesMin,
            (v) => (filters.chargesMin = v),
            filters.chargesMax,
            (v) => (filters.chargesMax = v),
        )}

        <div class="space-y-1">
            <label
                class="flex items-center gap-2 cursor-pointer text-xs text-secondary hover:text-primary"
            >
                <Toggle
                    size="xs"
                    ariaLabel="Toggle recurring charges"
                    checked={filters.isRecurring}
                    onchange={(e) => (filters.isRecurring = (e.currentTarget as HTMLInputElement).checked)}
                />
                <span class="font-mono">Recurring charges</span>
            </label>
        </div>

        {@render rangeRow(
            "Force",
            filters.forceMin,
            (v) => (filters.forceMin = v),
            filters.forceMax,
            (v) => (filters.forceMax = v),
        )}
    {/snippet}

    {#snippet dataBody()}
        {@render rangeRow(
            "Games",
            filters.gamesMin,
            (v) => (filters.gamesMin = v),
            filters.gamesMax,
            (v) => (filters.gamesMax = v),
        )}
        {@render rangeRow(
            "Lists",
            filters.listsMin,
            (v) => (filters.listsMin = v),
            filters.listsMax,
            (v) => (filters.listsMax = v),
        )}
        {@render rangeRow(
            "Unique Lists",
            filters.uniqueListsMin,
            (v) => (filters.uniqueListsMin = v),
            filters.uniqueListsMax,
            (v) => (filters.uniqueListsMax = v),
        )}
        {@render rangeRow(
            "Win Rate %",
            filters.winRateMin,
            (v) => (filters.winRateMin = v),
            filters.winRateMax,
            (v) => (filters.winRateMax = v),
        )}
    {/snippet}

<div class="w-full space-y-4">
    <div class="flex items-center justify-between">
        <span
            class="text-xs font-bold tracking-widest text-primary font-mono uppercase"
        >
            Advanced Filters
        </span>
    </div>

    <!-- GENERAL -->
    {@render group("General", generalBody)}

    <!-- SHIPS & PILOTS (pilots tab) -->
    {#if isPilotsTab}
        {@render group("Ships & Pilots", shipsPilotsBody)}
    {/if}

    <!-- UPGRADES (upgrades tab) -->
    {#if !isPilotsTab}
        {@render group("Upgrades", upgradesBody)}
    {/if}

    <!-- DATA (both tabs) -->
    {@render group("Data", dataBody)}
</div>
