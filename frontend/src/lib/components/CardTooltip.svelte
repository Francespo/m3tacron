<script lang="ts">
    /**
     * CardTooltip.svelte
     * ------------------
     * Generic hover tooltip for card images. Place it inside any element
     * with the `group` class (and `relative` positioning); the tooltip
     * appears above the trigger on hover.
     *
     * Fixed square frame (w-56 h-56) renders both portrait and landscape
     * card images via `object-contain`, so nothing is cropped or
     * distorted. Self-contained — no dependency on page-level stores.
     */
    let {
        image = "",
        name = "",
    }: {
        image?: string;
        name?: string;
    } = $props();
</script>

{#if image}
    <div
        class="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 hidden group-hover:block w-56 h-56 bg-terminal-panel border border-border-dark rounded-lg shadow-lg overflow-hidden"
    >
        <img
            src={image}
            alt={name}
            class="w-full h-full object-contain p-1.5"
            loading="lazy"
        />
    </div>
{:else}
    <div
        class="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 hidden group-hover:block w-56 h-56 bg-terminal-panel border border-border-dark rounded-lg shadow-lg flex items-center justify-center px-3"
    >
        <span class="text-xs font-mono text-secondary text-center">{name || "No image available"}</span>
    </div>
{/if}
