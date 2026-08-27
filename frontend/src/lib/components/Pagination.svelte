<script lang="ts">
    let {
        total = 0,
        page = 1,
        size = 20,
        onPrev,
        onNext,
    }: {
        total: number;
        page: number;
        size: number;
        onPrev: () => void;
        onNext: () => void;
    } = $props();

    const totalPages = $derived(Math.max(1, Math.ceil(Math.max(0, total) / Math.max(1, size))));
    const start = $derived(total === 0 ? 0 : (page - 1) * size + 1);
    const end = $derived(Math.min(page * size, total));
    const rangeLabel = $derived(total === 0 ? '0' : `${start}–${end}`);
</script>

<div
    class="flex flex-col sm:flex-row items-center justify-between gap-3 mt-6 pt-4 border-t border-border-dark"
>
    <div class="text-xs font-mono text-secondary text-center sm:text-left leading-tight">
        <span>Showing {rangeLabel} of {total}</span>
        <span class="mx-1.5 text-border-dark">·</span>
        <span>Page {page} of {totalPages}</span>
    </div>
    <div class="flex items-center gap-4">
        <button
            class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            onclick={onPrev}
            disabled={page <= 1}
        >
            ← Prev
        </button>
        <span class="text-xs font-mono text-secondary min-w-[92px] text-center">Page {page} of {totalPages}</span>
        <button
            class="px-3 py-1 text-xs font-mono border border-border-dark rounded-md hover:bg-[#ffffff08] text-secondary hover:text-primary active:bg-[#ffffff14] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            onclick={onNext}
            disabled={page * size >= total}
        >
            Next →
        </button>
    </div>
</div>
