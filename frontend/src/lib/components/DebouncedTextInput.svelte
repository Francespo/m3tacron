<script lang="ts">
    /**
     * DebouncedTextInput — a text <input> that only emits changes after
     * the user stops typing.
     *
     * Used for text inputs that drive URL state. The store mutation is
     * delayed by `debounceMs` so each keystroke doesn't fire a `goto()`.
     *
     * Usage:
     *   <DebouncedTextInput
     *       value={filters.searchName}
     *       onDebouncedChange={(v) => { filters.searchName = v; scheduleSync(0); }}
     *       placeholder="Search name..."
     *       ariaLabel="Search name"
     *   />
     */
    import { onDestroy, untrack } from "svelte";

    type Props = {
        value: string;
        onDebouncedChange: (v: string) => void;
        debounceMs?: number;
        placeholder?: string;
        class?: string;
        ariaLabel?: string;
        type?: "text" | "search" | "email" | "url";
        name?: string;
        id?: string;
        autocomplete?: string;
    };

    let {
        value,
        onDebouncedChange,
        debounceMs = 250,
        placeholder = "",
        class: className = "",
        ariaLabel,
        type = "search",
        name,
        id,
        autocomplete,
    }: Props = $props();

    // Local mirror of the bound value. Decouples UI typing from the
    // debounced emit, and lets the parent's `value` prop update `local`
    // via $effect without clobbering the user's in-flight keystrokes.
    // untrack(): we intentionally only want the initial value here; later
    // updates flow through the $effect below.
    let local = $state(untrack(() => value));
    let timer: ReturnType<typeof setTimeout> | null = null;

    function clearTimer() {
        if (timer !== null) {
            clearTimeout(timer);
            timer = null;
        }
    }

    function handleInput(e: Event) {
        const next = (e.currentTarget as HTMLInputElement).value;
        local = next;
        clearTimer();
        timer = setTimeout(() => {
            timer = null;
            onDebouncedChange(local);
        }, debounceMs);
    }

    // If the parent resets / external-syncs `value`, pick it up — but only
    // if the user isn't currently typing something that hasn't been emitted
    // yet. This avoids stomping an in-flight debounced change.
    $effect(() => {
        if (value !== local && timer === null) {
            local = value;
        }
    });

    onDestroy(clearTimer);
</script>

<input
    {type}
    {name}
    {id}
    {placeholder}
    value={local}
    aria-label={ariaLabel}
    autocomplete={autocomplete as any}
    oninput={handleInput}
    class="w-full min-h-11 bg-black border border-border-dark rounded px-2 py-1.5 text-xs font-mono text-primary placeholder:text-[#555] focus:border-primary focus:outline-none {className}"
/>
