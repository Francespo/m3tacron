<script lang="ts">
    import { goto } from "$app/navigation";
    import { page } from "$app/stores";

    let { data } = $props();

    function switchTab(tab: string) {
        const url = new URL($page.url);
        url.searchParams.set("tab", tab);
        url.searchParams.set("page", "0");
        goto(url.toString());
    }

    function changePage(newPage: number) {
        if (newPage < 0 || newPage >= Math.ceil(data.total / data.size)) return;
        const url = new URL($page.url);
        url.searchParams.set("page", newPage.toString());
        goto(url.toString(), { keepFocus: true });
    }

    const totalPages = $derived(Math.ceil(data.total / data.size));
</script>

<svelte:head>
    <title>Cards | M3taCron</title>
</svelte:head>

<div class="flex flex-col md:flex-row h-[calc(100vh-60px)] md:h-screen">
    <!-- Filter Sidebar -->
    <div
        class="w-full md:w-[350px] border-b md:border-b-0 md:border-r border-[#ffffff14] p-6 overflow-y-auto shrink-0 bg-terminal-bg relative z-10"
    >
        <h2
            class="text-sm font-bold tracking-[1px] text-primary font-sans uppercase mb-6"
        >
            Card Filters
        </h2>

        <!-- Type Tabs -->
        <div class="flex flex-col gap-1 w-full mb-4">
            <span class="text-xs font-bold text-secondary font-mono">Type</span>
            <div class="flex gap-1">
                <button
                    onclick={() => switchTab("pilots")}
                    class="flex-1 py-2 rounded text-sm font-mono transition-colors {data.tab ===
                    'pilots'
                        ? 'bg-[rgba(255,255,255,0.08)] text-primary'
                        : 'bg-transparent text-secondary hover:text-primary'}"
                    >Pilots</button
                >
                <button
                    onclick={() => switchTab("upgrades")}
                    class="flex-1 py-2 rounded text-sm font-mono transition-colors {data.tab ===
                    'upgrades'
                        ? 'bg-[rgba(255,255,255,0.08)] text-primary'
                        : 'bg-transparent text-secondary hover:text-primary'}"
                    >Upgrades</button
                >
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 p-6 md:p-8 overflow-y-auto h-full relative z-10">
        <div class="border-b border-[#ffffff14] pb-6 mb-6">
            <h1 class="text-[32px] font-sans font-bold text-primary">Cards</h1>
        </div>

        <div class="flex w-full mb-4">
            <span class="text-sm text-secondary font-mono"
                >{data.total}
                {data.tab === "pilots" ? "Pilots" : "Upgrades"} Found</span
            >
        </div>

        {#if data.cards.length > 0}
            <div class="flex flex-col gap-1 w-full max-w-[1000px]">
                {#each data.cards as card, i (card.name + i)}
                    <div
                        class="flex items-center w-full min-h-[60px] p-3 border-b border-[#ffffff14] hover:bg-[rgba(255,255,255,0.02)] transition-colors"
                    >
                        <div class="flex flex-col flex-grow">
                            <span
                                class="text-sm font-bold text-primary font-sans"
                                >{card.name || "Unknown"}</span
                            >
                            {#if data.tab === "pilots" && card.ship}
                                <span class="text-xs text-secondary italic"
                                    >{card.ship}</span
                                >
                            {/if}
                            {#if data.tab === "upgrades" && card.type}
                                <span
                                    class="text-xs text-cyan-400 font-mono uppercase"
                                    >{card.type}</span
                                >
                            {/if}
                        </div>
                        <div class="flex items-center gap-4 shrink-0">
                            {#if card.popularity !== undefined}
                                <div class="flex flex-col items-end">
                                    <span
                                        class="text-base font-bold text-primary font-mono"
                                        >{card.popularity}</span
                                    >
                                    <span
                                        class="text-[10px] text-secondary font-mono"
                                        >LISTS</span
                                    >
                                </div>
                            {/if}
                            {#if card.win_rate !== undefined}
                                <div class="flex flex-col items-end">
                                    <span
                                        class="text-base font-bold text-primary font-mono"
                                        >{card.win_rate}%</span
                                    >
                                    <span
                                        class="text-[10px] text-secondary font-mono"
                                        >WR</span
                                    >
                                </div>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>

            {#if totalPages > 1}
                <div
                    class="flex justify-end items-center gap-2 mt-8 max-w-[1000px]"
                >
                    <button
                        disabled={data.page === 0}
                        onclick={() => changePage(data.page - 1)}
                        class="p-2 border border-[#ffffff14] rounded bg-transparent text-secondary hover:bg-[rgba(255,255,255,0.05)] hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"><path d="m15 18-6-6 6-6" /></svg
                        >
                    </button>
                    <span class="text-sm font-mono text-secondary px-2"
                        >{data.page + 1} / {totalPages}</span
                    >
                    <button
                        disabled={data.page >= totalPages - 1}
                        onclick={() => changePage(data.page + 1)}
                        class="p-2 border border-[#ffffff14] rounded bg-transparent text-secondary hover:bg-[rgba(255,255,255,0.05)] hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"><path d="m9 18 6-6-6-6" /></svg
                        >
                    </button>
                </div>
            {/if}
            <div class="h-[60px]"></div>
        {:else}
            <div
                class="w-full border border-[#ffffff14] rounded-lg p-12 flex flex-col items-center justify-center bg-[rgba(255,255,255,0.01)] mt-8"
            >
                <h3
                    class="text-base font-bold text-primary font-sans uppercase tracking-widest mb-2"
                >
                    No Cards Found
                </h3>
                <p
                    class="text-sm text-secondary font-sans text-center max-w-md"
                >
                    No data available.
                </p>
            </div>
        {/if}
    </div>
</div>
