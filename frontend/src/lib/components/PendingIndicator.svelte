<script lang="ts">
    /**
     * PendingIndicator — quiet "query started" cue for slow data loads.
     *
     * The browser must feel responsive even when the backend is slow. This
     * component renders the two signals that cover that:
     *
     *   - mode="bar" (default): a 2px indeterminate sweep bar meant to sit at
     *     the top of the panel whose data is refreshing. Place it inside a
     *     `relative` container. It is absolutely positioned and
     *     pointer-events-none, so it never blocks interaction (filters,
     *     pagination, sorting stay usable) and never shifts the layout.
     *   - mode="tag": a small monochrome blinking-dot + label chip for
     *     inline use next to result counts / headers.
     *
     * Terminal aesthetic: muted track, thin neutral sweep, monospace label.
     * No flashy animation — just enough motion to say "your input was
     * received and the query has started".
     */
    let {
        active = false,
        label = "Updating…",
        mode = "bar",
    }: {
        active?: boolean;
        label?: string;
        mode?: "bar" | "tag";
    } = $props();
</script>

{#if active}
    {#if mode === "bar"}
        <div class="pending-bar" role="status" aria-label={label}>
            <div class="pending-bar__fill" aria-hidden="true"></div>
        </div>
    {:else}
        <span
            class="inline-flex items-center gap-1.5 border border-border-dark bg-[#ffffff05] rounded-md px-2 py-0.5 font-mono text-xs text-secondary"
            role="status"
        >
            <span class="pending-dot" aria-hidden="true"></span>
            {label}
        </span>
    {/if}
{/if}

<style>
    /* Thin overlay bar: absolute, non-interactive, zero layout cost. */
    .pending-bar {
        position: absolute;
        top: 0;
        right: 0;
        left: 0;
        height: 2px;
        overflow: hidden;
        background: rgba(255, 255, 255, 0.04);
        pointer-events: none;
        z-index: 10;
    }
    .pending-bar__fill {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: 40%;
        background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.7) 50%,
            transparent 100%
        );
        animation: pending-sweep 1.1s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    @keyframes pending-sweep {
        0% {
            transform: translateX(-120%);
        }
        100% {
            transform: translateX(360%);
        }
    }

    .pending-dot {
        width: 7px;
        height: 7px;
        border-radius: 9999px;
        background: rgba(255, 255, 255, 0.65);
        box-shadow: 0 0 6px rgba(255, 255, 255, 0.3);
        animation: pending-blink 1.1s steps(2, jump-none) infinite;
    }
    @keyframes pending-blink {
        0%,
        45% {
            opacity: 1;
        }
        50%,
        100% {
            opacity: 0.25;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .pending-bar__fill,
        .pending-dot {
            animation: none;
        }
        .pending-bar__fill {
            width: 30%;
        }
    }
</style>
