<script lang="ts">
    /**
     * CardHoverLink.svelte
     * --------------------
     * Inline clickable link wrapping a pilot or upgrade name with a
     * hover-tooltip preview of the real card image.
     *
     * The tooltip uses a named Tailwind group (`group/name`) so multiple
     * CardHoverLink instances can coexist on the same page without their
     * hover states interfering with each other or with parent `group`
     * classes on the surrounding cards.
     */
    import { xwingData } from "$lib/stores/xwingData.svelte";

    let {
        xws,
        type,
        name,
        href,
        className = "",
    }: {
        xws: string;
        type: "pilot" | "upgrade";
        name: string;
        href?: string;
        className?: string;
    } = $props();

    const defaultHref = $derived(
        href ?? (type === "pilot" ? `/pilot/${xws}` : `/upgrade/${xws}`),
    );

    // Resolve the card image for the tooltip. Pilots expose `image` at the
    // top level; upgrades keep it on the first side of their `sides` array.
    const cardImage = $derived.by(() => {
        if (type === "pilot") {
            const pilot = xwingData.getPilot(xws);
            return pilot?.image || null;
        } else {
            const upgrade = xwingData.getUpgrade(xws);
            return upgrade?.sides?.[0]?.image || null;
        }
    });
</script>

<a
    href={defaultHref}
    class="relative inline-flex items-center gap-1 group/name text-primary hover:text-accent transition-colors border-b border-transparent hover:border-accent/50 {className}"
>
    {name}
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="11"
        height="11"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="opacity-0 group-hover/name:opacity-70 transition-opacity shrink-0"
        aria-hidden="true"
    >
        <path d="M7 7h10v10" />
        <path d="M7 17 17 7" />
    </svg>
    {#if cardImage}
        <div
            class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-black/95 border border-border-dark rounded-md shadow-2xl opacity-0 group-hover/name:opacity-100 pointer-events-none transition-opacity z-50 w-48"
        >
            <img
                src={cardImage}
                alt={name}
                class="w-full h-auto"
                loading="lazy"
            />
        </div>
    {/if}
</a>
