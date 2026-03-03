<script lang="ts">
    let { data } = $props();
</script>

<svelte:head>
    <title>Pilot Detail | M3taCron</title>
</svelte:head>

<div class="p-6 md:p-8 max-w-[1000px]">
    <div class="flex items-center gap-3 mb-6">
        <a
            href="/cards"
            class="text-secondary hover:text-primary transition-colors text-sm font-mono"
            >← Back to Cards</a
        >
    </div>
    <div class="border-b border-[#ffffff14] pb-6 mb-6">
        <h1 class="text-3xl font-sans font-bold text-primary">Pilot Detail</h1>
        <p class="text-secondary font-mono text-sm mt-2">
            Pilot statistics and charts will load here.
        </p>
    </div>
    <div
        class="bg-terminal-panel border border-[#ffffff14] rounded-lg p-8 flex items-center justify-center min-h-[300px]"
    >
        <p class="text-secondary font-mono text-sm">
            Pilot detail view - coming in the next iteration.
        </p>
    </div>
</div>
