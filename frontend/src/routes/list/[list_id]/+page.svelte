<script lang="ts">
    import {
        getWinRateColor,
        getFactionColor,
        getFactionChar,
    } from "$lib/data/factions";
    import type { PageData } from "./$types";

    export let data: PageData;

    $: stats = data.stats;
    $: winRate = stats ? (stats.games > 0 ? (stats.wins / stats.games) * 100 : 0) : 0;
</script>

<div class="max-w-4xl mx-auto space-y-8">
    <!-- Back Button -->
    <a
        href="/lists"
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
        Back to Lists
    </a>

    {#if !stats}
        <div class="text-center py-12">
            <h2 class="text-xl font-sans font-bold text-primary mb-2">
                List Not Found
            </h2>
            <p class="text-secondary font-mono text-sm">
                We couldn't find data for this list (or it has no recorded games
                in the current filters).
            </p>
        </div>
    {:else}
        <!-- Header Section -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-xl p-6 md:p-8 flex items-center justify-between gap-8 relative overflow-hidden"
        >
            <!-- Background Glow -->
            <div
                class="absolute -top-32 -right-32 w-96 h-96 rounded-full blur-[100px] pointer-events-none"
                style="background-color: {getFactionColor(stats.faction_xws)}20;"
            ></div>

            <!-- Info / Stats -->
            <div class="flex flex-col gap-4 z-10">
                <div class="flex items-center gap-4">
                    <span
                        class="font-xwing text-4xl opacity-80"
                        style="color: {getFactionColor(stats.faction_xws)}"
                    >
                        {getFactionChar(stats.faction_xws)}
                    </span>
                    <h1
                        class="text-3xl lg:text-4xl font-sans font-bold text-primary"
                    >
                        {stats.name || "Untitled List"}
                    </h1>
                </div>

                <!-- Key Metrics -->
                <div class="flex gap-4 mt-2">
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
                            >Win Rate</span
                        >
                        <span
                            class="text-lg font-mono font-bold"
                            style="color: {getWinRateColor(winRate)}"
                        >
                            {winRate.toFixed(1)}%
                        </span>
                    </div>

                    <div
                        class="bg-[#ffffff05] border border-border-dark rounded px-3 py-2 flex flex-col"
                    >
                        <span
                            class="text-[10px] font-mono text-secondary uppercase tracking-wider"
                            >Points</span
                        >
                        <span class="text-lg font-mono text-green-400 font-bold"
                            >{stats.points}</span
                        >
                    </div>
                </div>
            </div>
        </div>

        <!-- Pilots / Composition Section -->
        <h2
            class="text-xl font-sans font-bold text-primary mt-12 mb-4 uppercase tracking-wide border-b border-border-dark pb-2"
        >
            Composition
        </h2>

        <div class="flex flex-col gap-4">
            {#each stats.pilots || [] as pilot}
                <div
                    class="bg-terminal-panel border border-border-dark rounded-xl p-6 flex flex-col gap-4"
                >
                    <div class="flex items-center gap-4">
                        <i
                            class="xwing-miniatures-ship xwing-miniatures-ship-{pilot.ship ||
                                'unknown'} text-4xl opacity-80"
                            style="color: {getFactionColor(stats.faction_xws)}"
                        ></i>
                        <div>
                            <h3
                                class="text-xl font-sans font-bold text-primary flex items-center gap-2"
                            >
                                <a
                                    href="/pilot/{pilot.id || pilot.name}"
                                    class="hover:text-accent transition-colors"
                                >
                                    {pilot.name || pilot.id}
                                </a>
                                {#if pilot.initiative !== undefined}
                                    <span
                                        class="text-xs font-mono bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded border border-orange-500/30"
                                    >
                                        I{pilot.initiative}
                                    </span>
                                {/if}
                            </h3>
                            <p
                                class="text-xs font-mono text-secondary opacity-70 mt-1 capitalize"
                            >
                                {pilot.ship?.replace("-", " ")}
                            </p>
                        </div>
                        <div
                            class="ml-auto text-right font-mono text-sm text-green-400"
                        >
                            {pilot.points} PT
                        </div>
                    </div>

                    <!-- Upgrades -->
                    {#if pilot.upgrades && Object.keys(pilot.upgrades).length > 0}
                        <div class="bg-[#ffffff03] rounded-md p-4 mt-2">
                            <h4
                                class="text-[10px] font-mono text-secondary uppercase tracking-wider mb-3"
                            >
                                Upgrades
                            </h4>
                            <div class="flex flex-wrap gap-2">
                                {#each Object.entries(pilot.upgrades || {}) as [slot, upgradesList]}
                                    {#each upgradesList as any[] as upgrade}
                                        <div
                                            class="flex items-center gap-1.5 bg-[#ffffff05] border border-border-dark rounded px-2 py-1"
                                        >
                                            <span
                                                class="text-xs font-mono text-primary"
                                                >{upgrade}</span
                                            >
                                        </div>
                                    {/each}
                                {/each}
                            </div>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>
