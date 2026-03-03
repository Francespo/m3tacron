<script lang="ts">
    import {
        getWinRateColor,
        getFactionColor,
        getFactionChar,
    } from "$lib/data/factions";
    import type { PageData } from "./$types";

    export let data: PageData;

    $: stats = data.stats;
    $: pilots = data.pilots;
    $: lists = data.lists;

    // Derived from signature (e.g., "bwing,rz1awing,t65xwing")
    // Note: signature is the raw sorted string of ship chassis keys
    $: shipsInSquadron = data.signature.split(",").map((s) => s.trim());
</script>

<div class="max-w-7xl mx-auto space-y-8">
    <!-- Back Button -->
    <a
        href="/squadrons"
        class="inline-flex items-center text-secondary hover:text-primary transition-colors text-xs font-mono uppercase tracking-wider mb-4"
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
            class="mr-2"><path d="m15 18-6-6 6-6" /></svg
        >
        Back to Squadrons
    </a>

    {#if !stats}
        <div class="text-center py-12">
            <h2 class="text-xl font-sans font-bold text-primary mb-2">
                Squadron Not Found
            </h2>
            <p class="text-secondary font-mono text-sm">
                We couldn't find data for this squadron combination (or it has
                no recorded games in the current filters).
            </p>
        </div>
    {:else}
        <!-- Header Section -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-xl p-6 md:p-8 flex flex-col md:flex-row gap-8 relative overflow-hidden"
        >
            <!-- Background Glow -->
            <div
                class="absolute -top-32 -right-32 w-96 h-96 rounded-full blur-[100px] pointer-events-none"
                style="background-color: {getFactionColor(stats.faction)}20;"
            ></div>

            <!-- Ship Icons Layout -->
            <div
                class="flex-shrink-0 flex items-center justify-center gap-2 flex-wrap max-w-sm bg-[#ffffff03] rounded-xl p-6 border border-border-dark relative"
            >
                <!-- Faction marker -->
                <span
                    class="absolute top-3 left-3 font-xwing text-lg opacity-40"
                    style="color: {getFactionColor(stats.faction)}"
                    >{getFactionChar(stats.faction)}</span
                >

                {#each shipsInSquadron as shipId}
                    <i
                        class="xwing-miniatures-ship xwing-miniatures-ship-{shipId}"
                        style="color: {getFactionColor(
                            stats.faction,
                        )}; font-size: 4rem;"
                    ></i>
                {/each}
            </div>

            <!-- Info / Stats -->
            <div class="flex flex-col justify-center gap-4 z-10">
                <h1
                    class="text-4xl lg:text-5xl font-sans font-bold text-primary capitalize flex items-center gap-3"
                >
                    Squadron Detail
                </h1>

                <!-- Squadron Ships Signature -->
                <p class="text-secondary font-mono text-sm">
                    {data.signature}
                </p>

                <!-- Key Metrics -->
                <div class="flex flex-wrap gap-4 mt-2">
                    <div
                        class="bg-[#ffffff05] border border-border-dark rounded px-3 py-2 flex flex-col"
                    >
                        <span
                            class="text-[10px] font-mono text-secondary uppercase tracking-wider"
                            >Total Games</span
                        >
                        <span class="text-lg font-mono text-primary font-bold"
                            >{stats.games}</span
                        >
                    </div>

                    <div
                        class="bg-[#ffffff05] border border-border-dark rounded px-3 py-2 flex flex-col"
                    >
                        <span
                            class="text-[10px] font-mono text-secondary uppercase tracking-wider"
                            >Popularity</span
                        >
                        <span class="text-lg font-mono text-primary font-bold"
                            >{stats.popularity}</span
                        >
                    </div>

                    <div
                        class="bg-[#ffffff05] border border-border-dark rounded px-3 py-2 flex flex-col"
                    >
                        <span
                            class="text-[10px] font-mono text-secondary uppercase tracking-wider"
                            >Win Rate</span
                        >
                        <span
                            class="text-lg font-mono font-bold"
                            style="color: {getWinRateColor(stats.win_rate)}"
                        >
                            {stats.win_rate.toFixed(1)}%
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Pilot Breakdown -->
        <h2
            class="text-xl font-sans font-bold text-primary mt-12 mb-4 uppercase tracking-wide border-b border-border-dark pb-2"
        >
            Pilot Composition
        </h2>

        {#if pilots.length > 0}
            <div
                class="bg-terminal-panel border border-border-dark rounded-xl overflow-hidden"
            >
                <div
                    class="grid grid-cols-[3fr_1fr_1fr_1fr_1.5fr_1fr] md:grid-cols-[4fr_1fr_1fr_1fr_2fr_1fr] gap-4 p-4 border-b border-border-dark bg-[#ffffff03] text-xs font-mono text-secondary uppercase tracking-wider"
                >
                    <div>Pilot</div>
                    <div class="text-center hidden sm:block">Ship</div>
                    <div class="text-right">Cost</div>
                    <div class="text-right">Games</div>
                    <div class="text-center">% of Squadron</div>
                    <div class="text-right">Win Rate</div>
                </div>

                <div class="divide-y divide-border-dark/50">
                    {#each pilots as p}
                        <a
                            href="/pilot/{p.pilot_xws}"
                            class="grid grid-cols-[3fr_1fr_1fr_1fr_1.5fr_1fr] md:grid-cols-[4fr_1fr_1fr_1fr_2fr_1fr] gap-4 p-4 hover:bg-[#ffffff05] transition-colors items-center cursor-pointer group"
                        >
                            <!-- Name -->
                            <div
                                class="font-sans font-bold text-primary group-hover:text-accent transition-colors truncate"
                            >
                                {p.name || p.pilot_xws}
                            </div>
                            <!-- Ship Icon -->
                            <div class="text-center opacity-60 hidden sm:block">
                                <i
                                    class="xwing-miniatures-ship xwing-miniatures-ship-{p.ship_xws} text-xl block"
                                ></i>
                            </div>
                            <!-- Cost -->
                            <div
                                class="text-right font-mono text-xs text-green-400"
                            >
                                {p.cost} PT
                            </div>
                            <!-- Games -->
                            <div
                                class="text-right font-mono text-xs text-secondary"
                            >
                                {p.games}
                            </div>
                            <!-- Percent Bar -->
                            <div class="flex items-center gap-2 justify-end">
                                <span class="font-mono text-xs text-secondary"
                                    >{p.percent_of_squadron.toFixed(1)}%</span
                                >
                                <div
                                    class="w-16 h-1 bg-[#ffffff10] rounded-full overflow-hidden hidden md:block"
                                >
                                    <div
                                        class="h-full bg-blue-500/50"
                                        style="width: {p.percent_of_squadron}%"
                                    ></div>
                                </div>
                            </div>
                            <!-- Win Rate -->
                            <div
                                class="text-right font-mono text-xs font-bold"
                                style="color: {getWinRateColor(p.win_rate)}"
                            >
                                {p.win_rate.toFixed(1)}%
                            </div>
                        </a>
                    {/each}
                </div>
            </div>
        {:else}
            <div
                class="bg-terminal-panel border border-border-dark rounded-xl p-8 text-center"
            >
                <p class="text-secondary font-mono text-sm">
                    No pilot breakdown data available.
                </p>
            </div>
        {/if}

        <!-- Top Performing Lists -->
        <h2
            class="text-xl font-sans font-bold text-primary mt-12 mb-4 uppercase tracking-wide border-b border-border-dark pb-2"
        >
            Top Performing Lists
        </h2>

        {#if lists.length > 0}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each lists.slice(0, 12) as list}
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-xl p-5 hover:border-secondary/40 transition-colors flex flex-col gap-4"
                    >
                        <div class="flex justify-between items-start gap-4">
                            <h3
                                class="font-sans font-bold text-primary text-sm line-clamp-2 leading-tight"
                            >
                                {list.name || "Untitled List"}
                            </h3>
                            <span
                                class="font-xwing text-lg opacity-60"
                                style="color: {getFactionColor(list.faction)}"
                            >
                                {getFactionChar(list.faction)}
                            </span>
                        </div>

                        <!-- List Quick Stats -->
                        <div
                            class="flex gap-4 border-b border-border-dark/50 pb-3"
                        >
                            <div class="flex flex-col">
                                <span
                                    class="text-[9px] font-mono text-secondary uppercase tracking-wider"
                                    >Win Rate</span
                                >
                                <span
                                    class="text-sm font-mono font-bold"
                                    style="color: {getWinRateColor(
                                        list.win_rate,
                                    )}">{list.win_rate.toFixed(1)}%</span
                                >
                            </div>
                            <div class="flex flex-col">
                                <span
                                    class="text-[9px] font-mono text-secondary uppercase tracking-wider"
                                    >Games</span
                                >
                                <span
                                    class="text-sm font-mono text-primary font-bold"
                                    >{list.games}</span
                                >
                            </div>
                            <div class="flex flex-col">
                                <span
                                    class="text-[9px] font-mono text-secondary uppercase tracking-wider"
                                    >Points</span
                                >
                                <span
                                    class="text-sm font-mono text-green-400 font-bold"
                                    >{list.points}</span
                                >
                            </div>
                        </div>

                        <!-- Pilot summary -->
                        <div class="flex-1 flex flex-col justify-end">
                            <div
                                class="text-xs font-mono text-secondary space-y-1"
                            >
                                {#each list.pilots || [] as pilot}
                                    <div
                                        class="flex items-center gap-2 truncate"
                                    >
                                        <i
                                            class="xwing-miniatures-ship xwing-miniatures-ship-{pilot.ship ||
                                                ''} text-[10px] opacity-70"
                                        ></i>
                                        <span class="truncate"
                                            >{pilot.name || pilot.id}</span
                                        >
                                    </div>
                                {/each}
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        {:else}
            <div
                class="bg-terminal-panel border border-border-dark rounded-xl p-8 text-center text-sm font-mono text-secondary mt-4"
            >
                No list data available for this squadron.
            </div>
        {/if}
    {/if}
</div>
