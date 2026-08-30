<script lang="ts">
    /**
     * Compact inline "back" affordance for detail pages.
     *
     * Visually it is a text link with a small chevron — no boxed button
     * chrome — so it doesn't steal vertical space and doesn't look like a
     * random square button. The label is visible (not aria-only) and
     * derived from `ariaLabel` (e.g. "Back to Ships" -> "Ships").
     *
     * Navigation behaviour is unchanged:
     * - Plain left-click tries `history.back()` when there is in-app history
     *   and `useHistory` is true.
     * - Fresh tab / no history falls back to `href`.
     * - Modified clicks are left alone for "open in new tab" etc.
     */
    let {
        href,
        ariaLabel,
        useHistory = true,
    }: {
        href: string;
        ariaLabel: string;
        useHistory?: boolean;
    } = $props();

    let label = $derived(
        ariaLabel.replace(/^Back to\s+/i, "").trim() || ariaLabel,
    );

    function handleClick(e: MouseEvent) {
        if (
            useHistory &&
            e.button === 0 &&
            !e.metaKey &&
            !e.ctrlKey &&
            !e.shiftKey &&
            !e.altKey &&
            history.length > 1
        ) {
            e.preventDefault();
            history.back();
        }
    }
</script>

<a
    {href}
    aria-label={ariaLabel}
    onclick={handleClick}
    class="inline-flex items-center gap-1.5 text-xs font-mono text-secondary hover:text-primary transition-colors group focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2 rounded-sm"
>
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
        class="shrink-0 transition-transform group-hover:-translate-x-0.5"
    >
        <path d="m15 18-6-6 6-6" />
    </svg>
    <span
        class="tracking-wide underline decoration-transparent group-hover:decoration-primary/60 underline-offset-4"
        >{label}</span
    >
</a>
