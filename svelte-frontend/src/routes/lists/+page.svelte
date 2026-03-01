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

    function toggleSortDirection() {
        const url = new URL($page.url);
        url.searchParams.set(
            "sort_direction",
            data.sort_direction === "desc" ? "asc" : "desc",
        );
        url.searchParams.set("page", "0");
        goto(url.toString());
    }

    function setSortMetric(metric: string) {
        const url = new URL($page.url);
        url.searchParams.set("sort_metric", metric);
        url.searchParams.set("page", "0");
        goto(url.toString());
    }

    const totalPages = $derived(Math.ceil(data.total / data.size));
</script>

<svelte:head>
    <title>List Browser | M3taCron</title>
</svelte:head>

<div class="flex flex-col md:flex-row h-[calc(100vh-60px)] md:h-screen">
    <!-- Filter Sidebar -->
    <div
        class="w-full md:w-[350px] border-b md:border-b-0 md:border-r border-[#ffffff14] p-6 overflow-y-auto shrink-0 bg-terminal-bg relative z-10"
    >
        <h2
            class="text-sm font-bold tracking-[1px] text-primary font-sans uppercase mb-6"
        >
            List Filters
        </h2>

        <!-- Sort -->
        <div class="flex flex-col gap-1 w-full mb-4">
            <span class="text-xs font-bold text-secondary font-mono"
                >Sort By</span
            >
            <div class="flex gap-2 items-center">
                <select
                    value={data.sort_metric}
                    onchange={(e) =>
                        setSortMetric((e.target as HTMLSelectElement).value)}
                    class="flex-1 bg-[rgba(255,255,255,0.03)] border border-[#ffffff14] rounded px-3 py-2 text-sm text-primary focus:outline-none focus:border-[#ffffff2e] transition-colors font-sans"
                >
                    <option value="Games">Games</option>
                    <option value="Win Rate">Win Rate</option>
                    <option value="Points Cost">Points Cost</option>
                </select>
                <button
                    onclick={toggleSortDirection}
                    class="p-2 border border-[#ffffff14] rounded bg-transparent text-secondary hover:text-primary transition-colors shrink-0"
                >
                    {#if data.sort_direction === "desc"}
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            ><path d="m3 16 4 4 4-4" /><path d="M7 20V4" /><path
                                d="M11 4h4"
                            /><path d="M11 8h7" /><path d="M11 12h10" /></svg
                        >
                    {:else}
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            ><path d="m3 8 4-4 4 4" /><path d="M7 4v16" /><path
                                d="M11 12h4"
                            /><path d="M11 16h7" /><path d="M11 20h10" /></svg
                        >
                    {/if}
                </button>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 p-6 md:p-8 overflow-y-auto h-full relative z-10">
        <div class="border-b border-[#ffffff14] pb-6 mb-6">
            <h1 class="text-[32px] font-sans font-bold text-primary">
                List Browser
            </h1>
        </div>

        <div class="flex w-full justify-between items-center mb-4">
            <span class="text-sm text-secondary font-mono"
                >{data.total} LISTS FOUND</span
            >
        </div>

        {#if data.lists.length > 0}
            <div class="flex flex-col gap-2 w-full">
                {#each data.lists as list, i (list.signature + i)}
                    <div
                        class="bg-terminal-panel border border-[#ffffff14] rounded-lg p-4 hover:border-[#ffffff2e] transition-colors"
                    >
                        <!-- Header Row -->
                        <div class="flex items-center justify-between mb-3">
                            <div class="flex items-center gap-2">
                                <span
                                    class="text-xs font-mono text-cyan-400 uppercase"
                                    >{list.faction}</span
                                >
                                <span class="text-xs text-secondary">•</span>
                                <span class="text-xs text-secondary font-mono"
                                    >{list.points}pts</span
                                >
                            </div>
                            <div class="flex items-center gap-4">
                                <div class="flex flex-col items-end">
                                    <span
                                        class="text-base font-bold text-primary font-mono"
                                        >{list.win_rate}%</span
                                    >
                                    <span
                                        class="text-[10px] text-secondary font-mono"
                                        >WIN RATE</span
                                    >
                                </div>
                                <div class="flex flex-col items-end">
                                    <span
                                        class="text-base font-bold text-primary font-mono"
                                        >{list.games}</span
                                    >
                                    <span
                                        class="text-[10px] text-secondary font-mono"
                                        >GAMES</span
                                    >
                                </div>
                                <div class="flex flex-col items-end">
                                    <span
                                        class="text-base font-bold text-primary font-mono"
                                        >{list.count}</span
                                    >
                                    <span
                                        class="text-[10px] text-secondary font-mono"
                                        >LISTS</span
                                    >
                                </div>
                            </div>
                        </div>

                        <!-- Pilots -->
                        <div class="flex flex-col gap-1">
                            {#each list.pilots as pilot}
                                <div class="flex items-center gap-2 text-sm">
                                    <span
                                        class="text-primary font-bold font-sans"
                                        >{pilot.name}</span
                                    >
                                    <span class="text-xs text-secondary italic"
                                        >{pilot.ship_name}</span
                                    >
                                    {#if pilot.upgrades.length > 0}
                                        <span
                                            class="text-[10px] text-secondary font-mono"
                                            >({pilot.upgrades
                                                .map((u: any) => u.name)
                                                .join(", ")})</span
                                        >
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    </div>
                {/each}
            </div>

            <!-- Pagination -->
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
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            ><path d="m15 18-6-6 6-6" /></svg
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
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            ><path d="m9 18 6-6-6-6" /></svg
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
                    0 Lists Found
                </h3>
                <p
                    class="text-sm text-secondary font-sans text-center max-w-md"
                >
                    No lists match your current filters.
                </p>
            </div>
        {/if}
    </div>
</div>
