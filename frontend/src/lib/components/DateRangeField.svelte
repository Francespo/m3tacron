<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
    import {
        getLatestPointsDate,
        getPointsEraGroups,
        getAllPointsEras,
        type PointsEra,
    } from "$lib/data/points-history";

    let {
        label = "Date Range",
        hideLabel = false,
        startDate = $bindable(filters.dateStart),
        endDate = $bindable(filters.dateEnd),
    }: {
        label?: string;
        hideLabel?: boolean;
        startDate?: string;
        endDate?: string;
    } = $props();

    let startRef: HTMLInputElement | undefined = $state();
    let endRef: HTMLInputElement | undefined = $state();

    let groups = $derived(
        getPointsEraGroups(filters.dataSource, filters.selectedFormats),
    );
    let allEras = $derived(
        getAllPointsEras(filters.dataSource, filters.selectedFormats),
    );
    let latestPointsDate = $derived(getLatestPointsDate(filters.dataSource));

    // Determine current preset ID or 'custom'
    let selectedPresetId = $derived.by(() => {
        const s = (startDate || "").trim();
        const e = (endDate || "").trim();
        if (!s && !e) return "all";
        if (s === latestPointsDate && !e) return "latest";
        const matched = allEras.find(
            (era) => era.startDate === s && (era.endDate || "") === e,
        );
        if (matched) return matched.id;
        return "custom";
    });

    function applyPreset(presetId: string) {
        if (presetId === "all") {
            startDate = "";
            endDate = "";
            return;
        }
        if (presetId === "latest") {
            startDate = latestPointsDate;
            endDate = "";
            return;
        }
        const era = allEras.find((x) => x.id === presetId);
        if (era) {
            startDate = era.startDate;
            endDate = era.endDate || "";
        }
    }

    function openPicker(el?: HTMLInputElement) {
        try {
            (el as any)?.showPicker?.();
        } catch {
            el?.focus();
            el?.click();
        }
    }
</script>

<div class="space-y-2.5">
    {#if !hideLabel}
        <div class="text-[11px] font-mono font-bold tracking-widest uppercase text-secondary">
            {label}
        </div>
    {/if}

    <!-- Quick Preset Buttons -->
    <div class="flex items-center gap-1.5 flex-wrap">
        <button
            type="button"
            class="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded border transition-colors {selectedPresetId === 'all' ? 'border-primary text-primary bg-primary/10 font-bold' : 'border-border-dark text-secondary hover:text-primary hover:border-white/20'}"
            onclick={() => applyPreset('all')}
        >
            All Time
        </button>

        <button
            type="button"
            class="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded border transition-colors inline-flex items-center gap-1 {selectedPresetId === 'latest' ? 'border-accent text-accent bg-accent/10 font-bold' : 'border-border-dark text-secondary hover:text-accent hover:border-accent/40'}"
            onclick={() => applyPreset('latest')}
            title="Since latest balance change ({latestPointsDate})"
        >
            <span class="text-accent">⚡</span> Latest Points
        </button>
    </div>

    <!-- Quick Selector Dropdown (Points Era Lineage) -->
    <div class="space-y-1">
        <label for="points-era-select" class="text-[10px] font-mono text-secondary uppercase tracking-wider block">
            Points Balance Era
        </label>
        <div class="relative">
            <select
                id="points-era-select"
                class="w-full bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary focus:border-primary focus:outline-none appearance-none cursor-pointer pr-6 truncate"
                value={selectedPresetId}
                onchange={(e) => applyPreset(e.currentTarget.value)}
                aria-label="Select points balance era"
            >
                <option value="all">All Time (No date filter)</option>
                <option value="latest">⚡ Since Latest Update ({latestPointsDate})</option>
                {#if selectedPresetId === "custom"}
                    <option value="custom" disabled>Custom Range ({startDate || 'Beginning'} → {endDate || 'Present'})</option>
                {/if}

                {#each groups as group}
                    <optgroup label="── {group.systemLabel} ──">
                        {#each group.eras as era}
                            <option value={era.id}>
                                {era.label}
                            </option>
                        {/each}
                    </optgroup>
                {/each}
            </select>
            <div class="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-secondary">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
            </div>
        </div>
    </div>

    <!-- Manual Date Inputs (From / To) -->
    <div class="grid grid-cols-1 gap-2 pt-0.5">
        <div class="flex items-center gap-1.5">
            <span class="text-[11px] font-mono text-secondary w-8 shrink-0">From</span>
            <div class="relative flex-1">
                <input
                    bind:this={startRef}
                    type="date"
                    class="w-full bg-black border border-border-dark rounded px-2 py-1.5 pr-8 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={startDate}
                    aria-label="Start date"
                />
                <button
                    type="button"
                    class="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 inline-flex items-center justify-center rounded text-secondary hover:text-primary hover:bg-white/10"
                    onclick={() => openPicker(startRef)}
                    aria-label="Open calendar for start date"
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
                </button>
            </div>
            {#if startDate}
                <button
                    type="button"
                    class="w-6 h-6 grid place-items-center rounded hover:bg-white/10 text-secondary hover:text-primary shrink-0"
                    onclick={() => (startDate = "")}
                    aria-label="Clear start date"
                >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="M6 6 12 12"/></svg>
                </button>
            {/if}
        </div>

        <div class="flex items-center gap-1.5">
            <span class="text-[11px] font-mono text-secondary w-8 shrink-0">To</span>
            <div class="relative flex-1">
                <input
                    bind:this={endRef}
                    type="date"
                    class="w-full bg-black border border-border-dark rounded px-2 py-1.5 pr-8 text-xs font-mono text-primary focus:border-primary focus:outline-none"
                    bind:value={endDate}
                    aria-label="End date"
                />
                <button
                    type="button"
                    class="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 inline-flex items-center justify-center rounded text-secondary hover:text-primary hover:bg-white/10"
                    onclick={() => openPicker(endRef)}
                    aria-label="Open calendar for end date"
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
                </button>
            </div>
            {#if endDate}
                <button
                    type="button"
                    class="w-6 h-6 grid place-items-center rounded hover:bg-white/10 text-secondary hover:text-primary shrink-0"
                    onclick={() => (endDate = "")}
                    aria-label="Clear end date"
                >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="M6 6 12 12"/></svg>
                </button>
            {/if}
        </div>
    </div>
</div>

