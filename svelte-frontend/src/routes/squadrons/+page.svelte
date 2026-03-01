<script lang="ts">
    // Squadrons use the same data as Lists but grouped differently
    // For now, redirect to Lists browser
</script>

<svelte:head>
    <title>Squadrons | M3taCron</title>
</svelte:head>

<div class="p-6 md:p-8">
    <div class="border-b border-[#ffffff14] pb-6 mb-6">
        <h1 class="text-[32px] font-sans font-bold text-primary">Squadrons</h1>
    </div>

    <div class="flex flex-col items-center justify-center py-24">
        <p class="text-secondary text-sm font-sans mb-4">
            Squadrons are displayed in the List Browser with faction grouping.
        </p>
        <a
            href="/lists"
            class="px-4 py-2 border border-[#ffffff14] rounded-md text-sm font-sans text-primary hover:bg-[rgba(255,255,255,0.05)] transition-colors"
        >
            Go to List Browser →
        </a>
    </div>
</div>
