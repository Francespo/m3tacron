<script lang="ts">
    import { goto } from "$app/navigation";
    import { page } from "$app/stores";

    let { data } = $props();

    // Local reactive state for search to avoid triggering navigation on every keystroke immediately
    let searchQuery = $state(data.search);
    let searchTimeout: ReturnType<typeof setTimeout>;

    function handleSearchInput() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const url = new URL($page.url);
            if (searchQuery) {
                url.searchParams.set("search", searchQuery);
            } else {
                url.searchParams.delete("search");
            }
            url.searchParams.set("page", "0"); // Reset page on new search
            goto(url.toString(), {
                keepFocus: true,
                noScroll: true,
                replaceState: true,
            });
        }, 300);
    }

    function changePage(newPage: number) {
        if (newPage < 0 || newPage >= Math.ceil(data.total / data.size)) return;
        const url = new URL($page.url);
        url.searchParams.set("page", newPage.toString());
        goto(url.toString(), { keepFocus: true, noScroll: false });
    }

    function resetFilters() {
        const url = new URL($page.url);
        url.search = ""; // Clear all search params
        goto(url.toString());
    }

    const totalPages = $derived(Math.ceil(data.total / data.size));
</script>

<svelte:head>
    <title>Tournaments | M3taCron</title>
</svelte:head>

<div class="flex flex-col md:flex-row h-[calc(100vh-60px)] md:h-screen">
    <!-- Filter Sidebar (Left Column) -->
    <div
        class="w-full md:w-[350px] border-b md:border-b-0 md:border-r border-[#ffffff14] p-6 overflow-y-auto shrink-0 bg-terminal-bg relative z-10 custom-scrollbar"
    >
        <div class="flex items-center justify-between mb-6">
            <h2
                class="text-sm font-bold tracking-[1px] text-primary font-sans uppercase"
            >
                Tournament Filters
            </h2>
            <button
                onclick={resetFilters}
                class="p-1.5 text-secondary hover:text-primary transition-colors bg-[rgba(255,255,255,0.03)] hover:bg-[rgba(255,255,255,0.08)] rounded"
                title="Reset Filters"
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
                        d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"
                    /><path d="M3 3v5h5" /></svg
                >
            </button>
        </div>

        <!-- Filters Placeholder Map -->
        <!-- In a full implementation, we would replicate `tournament_filters` sub-components here -->

        <!-- Search -->
        <div class="flex flex-col gap-1 w-full mb-6 mt-4">
            <span class="text-xs font-bold text-secondary font-mono"
                >Search Name</span
            >
            <input
                type="text"
                bind:value={searchQuery}
                oninput={handleSearchInput}
                placeholder="Search name..."
                class="bg-[rgba(255,255,255,0.03)] border border-[#ffffff14] rounded px-3 py-2 text-sm text-primary focus:outline-none focus:border-[#ffffff2e] focus:bg-[rgba(255,255,255,0.05)] transition-colors w-full font-sans"
            />
        </div>
    </div>

    <!-- Main Content Area (Right Column) -->
    <div
        class="flex-1 p-6 md:p-8 overflow-y-auto h-full relative z-10 custom-scrollbar"
    >
        <!-- Header -->
        <div class="border-b border-[#ffffff14] pb-6 mb-6">
            <h1 class="text-[32px] font-sans font-bold text-primary">
                Tournaments
            </h1>
        </div>

        <div class="flex w-full mb-4">
            <span class="text-sm text-secondary font-mono"
                >{data.total} Tournaments Found</span
            >
        </div>

        <!-- Render List or Empty State -->
        {#if data.tournaments.length > 0}
            <div
                class="flex flex-col w-full max-w-[1000px] animate-fade-in-up duration-300"
            >
                {#each data.tournaments as t (t.id)}
                    <a
                        href="/tournaments/{t.id}"
                        class="flex items-center w-full min-h-[80px] p-2.5 border-b border-[#ffffff14] hover:bg-[rgba(255,255,255,0.02)] transition-colors no-underline group block"
                    >
                        <!-- Format Badge -->
                        <div
                            class="w-[60px] h-[60px] bg-[rgba(255,255,255,0.05)] rounded-md border border-[#ffffff14] flex flex-col items-center justify-center shrink-0"
                        >
                            <span
                                class="text-[15px] font-bold text-primary leading-none"
                                >{t.badge_l1}</span
                            >
                            {#if t.badge_l2}
                                <span
                                    class="text-[10px] font-bold text-secondary leading-none mt-0.5"
                                    >{t.badge_l2}</span
                                >
                            {/if}
                        </div>

                        <!-- Info -->
                        <div
                            class="flex flex-col justify-center flex-grow px-3 max-w-[calc(100%-120px)]"
                        >
                            <span
                                class="text-base font-bold text-white font-sans group-hover:text-cyan-400 transition-colors truncate"
                                >{t.name}</span
                            >
                            <div class="flex items-center gap-2 mt-1 truncate">
                                <span
                                    class="text-[10px] text-cyan-400 font-mono uppercase shrink-0"
                                    >{t.platform_label}</span
                                >
                                <span
                                    class="text-[10px] text-secondary shrink-0"
                                    >•</span
                                >
                                <span
                                    class="text-[10px] text-secondary font-mono shrink-0"
                                    >{t.date}</span
                                >
                                <span
                                    class="text-[10px] text-secondary shrink-0"
                                    >•</span
                                >
                                <span
                                    class="text-[10px] text-secondary truncate"
                                    >{t.location}</span
                                >
                            </div>
                        </div>

                        <!-- Match Count -->
                        <div
                            class="flex gap-4 pr-3 shrink-0 items-center h-full"
                        >
                            <div class="flex flex-col items-end justify-center">
                                <span
                                    class="text-xl font-bold text-primary font-mono leading-none"
                                    >{t.players}</span
                                >
                                <span
                                    class="text-[10px] text-secondary font-mono mt-0.5"
                                    >PLY</span
                                >
                            </div>
                        </div>
                    </a>
                {/each}
            </div>

            <!-- Pagination -->
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
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            ><path d="m15 18-6-6 6-6" /></svg
                        >
                    </button>

                    <span class="text-sm font-mono text-secondary px-2">
                        {data.page + 1} / {totalPages}
                    </span>

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
            <!-- Padding bottom scroll -->
        {:else}
            <!-- Empty State -->
            <div
                class="w-full max-w-[1000px] border border-[#ffffff14] rounded-lg p-12 flex flex-col items-center justify-center bg-[rgba(255,255,255,0.01)] mt-8"
            >
                <div class="mb-4 text-secondary opacity-50">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="48"
                        height="48"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        ><ellipse cx="12" cy="5" rx="9" ry="3" /><path
                            d="M3 5V19A9 3 0 0 0 21 19V5"
                        /><path d="M3 12A9 3 0 0 0 21 12" /></svg
                    >
                </div>
                <h3
                    class="text-base font-bold text-primary font-sans uppercase tracking-widest mb-2"
                >
                    0 Tournaments Found
                </h3>
                <p
                    class="text-sm text-secondary font-sans text-center max-w-md mb-6"
                >
                    No tournaments match your current filters or search query.
                </p>
                <button
                    onclick={resetFilters}
                    class="px-4 py-2 border border-[#ffffff14] rounded-md text-sm font-sans text-primary hover:bg-[rgba(255,255,255,0.05)] transition-colors"
                >
                    Reset Filters
                </button>
            </div>
        {/if}
    </div>
</div>

<style>
    /* Custom Scrollbar to match Reflex aesthetic */
    .custom-scrollbar::-webkit-scrollbar {
        width: 8px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }
</style>
