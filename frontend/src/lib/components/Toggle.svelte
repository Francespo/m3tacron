<!--
    Toggle — Canonical squared, black-bg, white-check custom checkbox.

    API:
      • checked     – boolean (or expression evaluating to a boolean).
      • onchange    – optional Event handler. Works with `bind:checked` OR
                      one-way `checked={...} onchange={...}` patterns.
      • ariaLabel   – label announced by screen readers.
      • size        – "xs" (12px, tight lists) or "sm" (14px, default).

    The real `<input type="checkbox">` lives inside the `<label>` with
    `class="sr-only"`, preserving keyboard + a11y while giving us a
    consistent visual.
-->
<script lang="ts">
    let {
        checked = false,
        onchange,
        ariaLabel = "Toggle",
        size = "sm",
    }: {
        checked?: boolean;
        onchange?: (e: Event) => void;
        ariaLabel?: string;
        size?: "xs" | "sm";
    } = $props();
</script>

<label
    class="inline-flex items-center justify-center rounded-[2px] border bg-black cursor-pointer transition-colors
        {size === 'xs' ? 'w-3 h-3' : 'w-3.5 h-3.5'}
        {checked ? 'border-primary' : 'border-border-dark hover:border-primary/50'}"
    aria-label={ariaLabel}
>
    {#if checked}
        <svg
            width={size === 'xs' ? 8 : 10}
            height={size === 'xs' ? 8 : 10}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="3.5"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="text-primary"
        >
            <path d="M20 6 9 17l-5-5" />
        </svg>
    {/if}
    <input
        type="checkbox"
        {checked}
        {onchange}
        class="sr-only"
        aria-label={ariaLabel}
        tabindex="0"
    />
</label>
