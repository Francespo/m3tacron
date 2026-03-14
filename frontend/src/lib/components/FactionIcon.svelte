<script lang="ts">
    /**
     * FactionIcon.svelte
     * Purpose: Renders a faction icon using the X-Wing font.
     */
    import { getFactionColor, getFactionChar } from "$lib/data/factions";

    let {
        faction,
        size = "1em",
        className = "",
    }: {
        faction: string;
        size?: string;
        className?: string;
    } = $props();

    const char = $derived(getFactionChar(faction));
    const color = $derived(getFactionColor(faction));
</script>

{#if char}
    <i
        class="faction-icon {className}"
        style="font-size: {size}; color: {color};"
        aria-hidden="true"
    >
        {char}
    </i>
{/if}

<style>
    .faction-icon {
        font-family: "XWing";
        font-style: normal;
        font-weight: 400 !important;
        line-height: 1;
        display: inline-block;
        vertical-align: middle;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        filter: brightness(1.2);
    }
</style>
