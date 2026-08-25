<script lang="ts">
    /**
     * FilterSection — reusable, self-contained collapsible filter section.
     *
     * Not tied to FilterPanel: it can be mounted in ANY DOM region. It only
     * needs a stable `id` (used for persistence + aria-controls) and the
     * content passed as `children`. Collapse state is read/written through
     * the shared `filterSections` store so the desktop FilterPanel and the
     * mobile filter drawer persist and share one preference per section id.
     */
    import type { Snippet } from "svelte";
    import { filterSections } from "$lib/stores/filterSections.svelte";

    type Props = {
        id: string;
        label: string;
        description?: string;
        defaultOpen?: boolean;
        children: Snippet;
    };

    let {
        id,
        label,
        description,
        defaultOpen = true,
        children,
    }: Props = $props();

    // Load the persisted collapse preference into the shared store once, on
    // mount. `id`/`defaultOpen` are static per section, so capturing their
    // initial values is correct. The `$effect` is the only place this may
    // write to the store's reactive map — writing during a `$derived`
    // evaluation would trigger Svelte's `state_unsafe_mutation` guard.
    $effect(() => {
        filterSections.ensureLoaded(id, defaultOpen);
    });

    // Read-only lookup from the shared store: safe inside `$derived`.
    let open = $derived(!filterSections.isCollapsed(id));

    function handleToggle() {
        filterSections.toggle(id);
    }
</script>

<div class="w-full">
    <!-- Header row: label (toggle) + optional info tooltip on the left,
         rotating chevron on the right, following the accordion header
         visual language used across the filter sidebar. -->
    <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-2 min-w-0">
            <button
                type="button"
                onclick={handleToggle}
                aria-expanded={open}
                aria-controls={id}
                class="text-xs font-bold tracking-widest text-primary font-mono uppercase hover:text-white transition-colors"
            >
                {label}
            </button>

            {#if description}
                <button
                    type="button"
                    class="group relative inline-flex items-center justify-center w-4 h-4 rounded-full text-secondary hover:text-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    aria-label="More about {label}"
                >
                    <svg
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        aria-hidden="true"
                    >
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="16" x2="12" y2="12" />
                        <line x1="12" y1="8" x2="12.01" y2="8" />
                    </svg>
                    <div
                        class="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-72 max-w-[min(20rem,calc(100vw-2rem))] p-2.5 bg-terminal-panel border border-border-dark rounded-md text-[11px] font-mono leading-snug text-secondary opacity-0 invisible group-hover:opacity-100 group-hover:visible group-focus-within:opacity-100 group-focus-within:visible transition-opacity z-50 pointer-events-none shadow-lg"
                    >
                        {description}
                    </div>
                </button>
            {/if}
        </div>

        <!-- Decorative chevron; the label button above is the real toggle
             for keyboard/AT users. -->
        <button
            type="button"
            onclick={handleToggle}
            aria-hidden="true"
            tabindex="-1"
            class="shrink-0 flex items-center justify-center -m-1 p-1 text-secondary hover:text-primary transition-colors"
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
                class="transition-transform {open ? 'rotate-180' : ''}"
                ><path d="m6 9 6 6 6-6" /></svg
            >
        </button>
    </div>

    {#if open}
        <div id={id} class="mt-3">
            {@render children()}
        </div>
    {/if}
</div>
