<script lang="ts">
    let { data } = $props();
    const t = $derived(data.detail?.tournament);
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
                class="inline-flex items-center gap-2 px-4 py-2 border border-[#ffffff14] rounded-md text-sm mb-8 font-sans text-primary hover:bg-[rgba(255,255,255,0.05)] transition-colors"
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

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <div class="flex flex-col gap-6">
                <!-- Cut Standings -->
                {#if data.detail.players_cut && data.detail.players_cut.length > 0}
                    <div class="bg-terminal-panel border border-[#ffffff14] rounded-lg overflow-hidden">
                        <div class="bg-[rgba(255,255,255,0.02)] border-b border-[#ffffff14] p-3">
                            <h2 class="text-sm font-bold text-primary font-mono">CUT STANDINGS</h2>
                        </div>
                        <div class="flex flex-col">
                            {#each data.detail.players_cut as p}
                                <div class="flex items-center gap-4 p-3 border-b border-[#ffffff14] last:border-0 hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                                    <span class="w-8 h-8 rounded-full bg-[rgba(255,255,255,0.1)] flex items-center justify-center font-mono text-sm">{p.rank}</span>
                                    <div class="flex flex-col">
                                        <span class="font-mono text-primary font-medium">{p.name}</span>
                                        <span class="text-xs text-secondary">{p.faction} • {p.wins}W - {p.losses}L</span>
                                    </div>
                                    <div class="flex-1"></div>
                                    {#if p.has_list}
                                        <button class="px-3 py-1 border border-[#ffffff14] rounded text-xs font-mono hover:bg-[rgba(255,255,255,0.1)] text-primary">LIST</button>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- Swiss Standings -->
                <div class="bg-terminal-panel border border-[#ffffff14] rounded-lg overflow-hidden">
                    <div class="bg-[rgba(255,255,255,0.02)] border-b border-[#ffffff14] p-3">
                        <h2 class="text-sm font-bold text-primary font-mono">{data.detail.players_cut?.length > 0 ? "SWISS STANDINGS" : "STANDINGS"}</h2>
                    </div>
                    <div class="flex flex-col">
                        {#each (data.detail.players_swiss || []) as p}
                            <div class="flex items-center gap-4 p-3 border-b border-[#ffffff14] last:border-0 hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                                <span class="w-8 h-8 rounded-full bg-[rgba(255,255,255,0.1)] flex items-center justify-center font-mono text-sm">{p.rank}</span>
                                <div class="flex flex-col">
                                    <span class="font-mono text-primary font-medium">{p.name}</span>
                                    <span class="text-xs text-secondary">{p.faction} • {p.wins}W - {p.losses}L</span>
                                </div>
                                <div class="flex-1"></div>
                                {#if p.has_list}
                                    <button class="px-3 py-1 border border-[#ffffff14] rounded text-xs font-mono hover:bg-[rgba(255,255,255,0.1)] text-primary">LIST</button>
                                {/if}
                            </div>
                        {/each}
                    </div>
                </div>
            </div>

            <!-- Matches -->
            {#if data.detail.matches && data.detail.matches.length > 0}
                <div class="bg-terminal-panel border border-[#ffffff14] rounded-lg overflow-hidden">
                    <div class="bg-[rgba(255,255,255,0.02)] border-b border-[#ffffff14] p-3">
                        <h2 class="text-sm font-bold text-primary font-mono">MATCHES</h2>
                    </div>
                    <div class="flex flex-col">
                        {#each data.detail.matches as m}
                            <div class="flex items-center gap-3 p-3 border-b border-[#ffffff14] last:border-0 hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                                <span class="text-xs font-mono text-secondary w-6 text-center">{m.round}</span>
                                {#if m.scenario}
                                    <span class="px-2 py-1 bg-[rgba(255,255,255,0.05)] border border-[#ffffff14] rounded text-[10px] uppercase font-mono text-secondary truncate max-w-[80px]" title={m.scenario}>{m.scenario}</span>
                                {:else}
                                    <div class="w-[80px]"></div>
                                {/if}
                                <div class="flex-1 flex items-center justify-between bg-[rgba(255,255,255,0.02)] rounded p-2">
                                    <span class="font-mono text-sm text-left flex-1 truncate pr-2 {m.winner_id === m.player1_id ? 'text-green-400 font-bold' : 'text-primary'}" title={m.player1}>{m.player1}</span>
                                    <div class="flex items-center justify-center gap-1 font-mono text-sm w-12 font-bold">
                                        <span class={m.winner_id === m.player1_id ? 'text-green-400' : 'text-red-400'}>{m.score1}</span>
                                        <span class="text-secondary">-</span>
                                        <span class={m.winner_id === m.player2_id ? 'text-green-400' : 'text-red-400'}>{m.score2}</span>
                                    </div>
                                    <span class="font-mono text-sm text-right flex-1 truncate pl-2 {m.winner_id === m.player2_id ? 'text-green-400 font-bold' : 'text-primary'}" title={m.player2}>{m.player2}</span>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    {:else}
        <div class="flex flex-col items-center justify-center py-24">
            <h2 class="text-xl font-bold text-primary font-sans mb-4">
                Tournament Not Found
            </h2>
            <p class="text-secondary text-sm mb-6">
                Tournament detail was not found.
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
