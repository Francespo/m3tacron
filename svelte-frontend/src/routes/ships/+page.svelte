<script lang="ts">
    import { goto } from "$app/navigation";
    import { page } from "$app/stores";

    let { data } = $props();

    function changePage(newPage: number) {
        if (newPage < 0 || newPage >= Math.ceil(data.total / data.size)) return;
        const url = new URL($page.url);
        url.searchParams.set("page", newPage.toString());
        goto(url.toString(), { keepFocus: true });
    }

    const totalPages = $derived(Math.ceil(data.total / data.size));
</script>

<svelte:head>
    <title>Ships | M3taCron</title>
</svelte:head>

<div class="flex flex-col md:flex-row h-[calc(100vh-60px)] md:h-screen">
    <!-- Filter Sidebar -->
    <div
        class="w-full md:w-[350px] border-b md:border-b-0 md:border-r border-[#ffffff14] p-6 overflow-y-auto shrink-0 bg-terminal-bg relative z-10"
    >
        <h2
            class="text-sm font-bold tracking-[1px] text-primary font-sans uppercase mb-6"
        >
            Ship Filters
        </h2>
        <p class="text-xs text-secondary font-mono">Filters coming soon</p>
    </div>

    <!-- Main Content -->
    <div class="flex-1 p-6 md:p-8 overflow-y-auto h-full relative z-10">
        <div class="border-b border-[#ffffff14] pb-6 mb-6">
            <h1 class="text-[32px] font-sans font-bold text-primary">Ships</h1>
        </div>

        <div class="flex w-full mb-4">
            <span class="text-sm text-secondary font-mono"
                >{data.total} Ships Found</span
            >
        </div>

        {#if data.ships.length > 0}
            <div
                class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full"
            >
                {#each data.ships as ship, i (ship.ship_name + i)}
                    <div
                        class="bg-terminal-panel border border-[#ffffff14] rounded-lg p-4 hover:border-[#ffffff2e] transition-colors"
                    >
                        <div class="flex items-center justify-between mb-2">
                            <span
                                class="text-base font-bold text-primary font-sans truncate"
                                >{ship.ship_name || "Unknown Ship"}</span
                            >
                            <span
                                class="text-xs font-mono text-cyan-400 uppercase shrink-0 ml-2"
                                >{ship.faction_xws || ""}</span
                            >
                        </div>
                        <div class="flex items-center gap-4 mt-2">
                            {#if ship.games !== undefined}
                                <div class="flex flex-col">
                                    <span
                                        class="text-lg font-bold text-primary font-mono"
                                        >{ship.games}</span
                                    >
                                    <span
                                        class="text-[10px] text-secondary font-mono"
                                        >GAMES</span
                                    >
                                </div>
                            {/if}
                            {#if ship.win_rate !== undefined}
                                <div class="flex flex-col">
                                    <span
                                        class="text-lg font-bold text-primary font-mono"
                                        >{ship.win_rate}%</span
                                    >
                                    <span
                                        class="text-[10px] text-secondary font-mono"
                                        >WIN RATE</span
                                    >
                                </div>
                            {/if}
                            {#if ship.popularity !== undefined}
                                <div class="flex flex-col">
                                    <span
                                        class="text-lg font-bold text-primary font-mono"
                                        >{ship.popularity}</span
                                    >
                                    <span
                                        class="text-[10px] text-secondary font-mono"
                                        >LISTS</span
                                    >
                                </div>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>

            {#if totalPages > 1}
                <div class="flex justify-end items-center gap-2 mt-8">
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
                    0 Ships Found
                </h3>
                <p
                    class="text-sm text-secondary font-sans text-center max-w-md"
                >
                    No ships data available.
                </p>
            </div>
        {/if}
    </div>
</div>
