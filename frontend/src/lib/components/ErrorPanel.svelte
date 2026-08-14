<script lang="ts">
    /**
     * ErrorPanel — visible failure state with an optional retry.
     *
     * Rendered when a data fetch fails so the user always sees a message
     * (no silent failures). `onRetry` typically calls `invalidateAll()`
     * to re-run the route loaders; the retry button is only shown when a
     * handler is provided.
     */
    let {
        title = "Failed to load data",
        message,
        onRetry,
        retryLabel = "Try again",
    }: {
        title?: string;
        message?: string;
        onRetry?: () => void;
        retryLabel?: string;
    } = $props();
</script>

<div
    class="bg-red-950/30 border border-red-500/30 rounded-lg p-6 text-center space-y-3"
    role="alert"
>
    <p class="text-red-400 font-sans font-bold text-base tracking-wide">
        {title}
    </p>
    {#if message}
        <p class="text-red-300/80 font-mono text-sm break-words">{message}</p>
    {/if}
    {#if onRetry}
        <button
            type="button"
            onclick={onRetry}
            class="px-4 py-1.5 text-xs font-mono border border-red-500/40 text-red-300 rounded-md hover:bg-red-500/10 active:bg-red-500/20 transition-colors"
        >
            {retryLabel}
        </button>
    {/if}
</div>
