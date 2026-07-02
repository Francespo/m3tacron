<script lang="ts">
    /**
     * Icon-only "back" link used at the top of detail pages.
     * Renders a chevron-left SVG inside a square button; the visible label is
     * exposed to assistive tech via `aria-label`.
     *
     * Navigation behaviour:
     * - If the user has in-app browser history (came from somewhere on the
     *   same origin) AND `useHistory` is true, a plain left-click on the
     *   button calls `history.back()` so the user returns to the previous
     *   page (e.g. from a list card → detail, back goes to the list).
     * - If the user opened the detail page in a fresh tab (no history) the
     *   `href` fallback fires so the link still works.
     * - Middle-click, cmd/ctrl-click, shift-click, and right-click are left
     *   alone so "open in new tab", "open in new window", etc. behave the
     *   way users expect.
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
    class="inline-flex items-center justify-center w-9 h-9 rounded-md text-secondary hover:text-primary hover:bg-[#ffffff08] transition-colors border border-border-dark"
>
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
    >
        <path d="m15 18-6-6 6-6" />
    </svg>
</a>
