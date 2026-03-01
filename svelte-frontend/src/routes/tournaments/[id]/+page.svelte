<script lang="ts">
    let { data } = $props();
    const t = $derived(data.tournament);
</script>

<svelte:head>
    <title>{t ? t.name : "Tournament"} | M3taCron</title>
</svelte:head>

<div class="p-6 md:p-8 max-w-[1000px]">
    {#if t}
        <!-- Header -->
        <div class="border-b border-[#ffffff14] pb-6 mb-6">
            <div class="flex items-center gap-3 mb-2">
                <a
                    href="/tournaments"
                    class="text-secondary hover:text-primary transition-colors text-sm font-mono"
                    >← Back</a
                >
            </div>
            <h1 class="text-3xl font-sans font-bold text-primary">{t.name}</h1>
        </div>

        <!-- Info Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div
                class="bg-terminal-panel border border-[#ffffff14] rounded-lg p-4 flex flex-col"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Format</span
                >
                <span class="text-lg font-bold text-primary font-mono"
                    >{t.format_label}</span
                >
            </div>
            <div
                class="bg-terminal-panel border border-[#ffffff14] rounded-lg p-4 flex flex-col"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Date</span
                >
                <span class="text-lg font-bold text-primary font-mono"
                    >{t.date}</span
                >
            </div>
            <div
                class="bg-terminal-panel border border-[#ffffff14] rounded-lg p-4 flex flex-col"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Players</span
                >
                <span class="text-lg font-bold text-primary font-mono"
                    >{t.players}</span
                >
            </div>
            <div
                class="bg-terminal-panel border border-[#ffffff14] rounded-lg p-4 flex flex-col"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Platform</span
                >
                <span class="text-lg font-bold text-cyan-400 font-mono"
                    >{t.platform_label}</span
                >
            </div>
        </div>

        <!-- Location -->
        <div
            class="bg-terminal-panel border border-[#ffffff14] rounded-lg p-4 mb-6"
        >
            <span class="text-xs text-secondary font-mono uppercase mb-1 block"
                >Location</span
            >
            <span class="text-base text-primary font-sans">{t.location}</span>
        </div>

        <!-- External Link -->
        {#if t.url}
            <a
                href={t.url}
                target="_blank"
                rel="noreferrer"
                class="inline-flex items-center gap-2 px-4 py-2 border border-[#ffffff14] rounded-md text-sm font-sans text-primary hover:bg-[rgba(255,255,255,0.05)] transition-colors"
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
                    ><path
                        d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"
                    /><polyline points="15 3 21 3 21 9" /><line
                        x1="10"
                        y1="14"
                        x2="21"
                        y2="3"
                    /></svg
                >
                View on Source
            </a>
        {/if}
    {:else}
        <div class="flex flex-col items-center justify-center py-24">
            <h2 class="text-xl font-bold text-primary font-sans mb-4">
                Tournament Not Found
            </h2>
            <p class="text-secondary text-sm mb-6">
                Tournament #{data.id} was not found.
            </p>
            <a
                href="/tournaments"
                class="px-4 py-2 border border-[#ffffff14] rounded-md text-sm font-sans text-primary hover:bg-[rgba(255,255,255,0.05)] transition-colors"
            >
                ← Back to Tournaments
            </a>
        </div>
    {/if}
</div>
