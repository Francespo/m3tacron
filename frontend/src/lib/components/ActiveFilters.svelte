<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
</script>

{#if filters.activeChips.length > 0}
    <div class="w-full space-y-3 mb-6">
        <div class="flex items-center justify-between">
            <span
                class="text-xs font-bold tracking-widest text-primary font-mono"
            >
                ACTIVE FILTERS
            </span>
            <button
                class="min-h-10 px-2 text-xs text-red-500 hover:text-red-400 transition-colors"
                onclick={() => filters.resetAll()}
            >
                Reset All
            </button>
        </div>

        <div class="flex flex-wrap gap-2">
            {#each filters.activeChips as chip}
                <div
                    class="flex items-center gap-1.5 px-2 py-1 bg-border-dark rounded text-xs font-mono text-primary"
                >
                    <span>{chip.label}</span>
                    <button
                        class="min-h-8 min-w-8 inline-flex items-center justify-center text-secondary hover:text-white transition-colors"
                        onclick={() => filters.removeChip(chip.key)}
                        aria-label={`Remove filter ${chip.label}`}
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
                            ><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg
                        >
                    </button>
                </div>
            {/each}
        </div>
    </div>
{/if}
