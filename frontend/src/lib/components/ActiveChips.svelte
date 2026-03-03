<script lang="ts">
    import { filters } from "$lib/stores/filters.svelte";
</script>

{#if filters.activeChips.length > 0}
    <div class="flex flex-wrap gap-1.5 mb-4">
        {#each filters.activeChips as chip}
            <button
                class="flex items-center gap-1 px-2 py-0.5 bg-[#ffffff08] border border-border-dark rounded text-xs font-mono text-secondary hover:text-primary hover:border-primary/30 transition-colors"
                onclick={() => filters.removeChip(chip.key)}
            >
                <span>{chip.label}</span>
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="10"
                    height="10"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    ><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg
                >
            </button>
        {/each}
        <button
            class="px-2 py-0.5 text-xs font-mono text-secondary hover:text-red-400 transition-colors"
            onclick={() => filters.resetAll()}
        >
            Clear all
        </button>
    </div>
{/if}
