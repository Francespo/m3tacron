<script lang="ts">
    let { data } = $props();
    let info = $derived(data.info);
    let stats = $derived(data.stats);
    let pilots = $derived(data.pilots);
    let lists = $derived(data.lists);
    let squadrons = $derived(data.squadrons);

    function getFactionColor(factions: string[]): string {
        if (!factions || factions.length === 0) return "#666666";
        const faction = factions[0].toLowerCase().replace(/[\s-]/g, "");
        const colors: Record<string, string> = {
            rebelalliance: "#FF3333",
            galacticempire: "#2979FF",
            scumandvillainy: "#006400",
            resistance: "#FF8C00",
            firstorder: "#800020",
            galacticrepublic: "#E6D690",
            separatistalliance: "#607D8B",
        };
        return colors[faction] || "#666666";
    }

    function wrColor(wr: number): string {
        if (wr >= 55) return "#22c55e";
        if (wr >= 50) return "#84cc16";
        if (wr >= 45) return "#eab308";
        return "#ef4444";
    }
</script>

<svelte:head>
    <title>{info?.name || data.shipXws} — Ship Detail | M3taCron</title>
</svelte:head>

<div class="min-h-screen p-6 md:p-8 font-sans">
    <!-- Back link -->
    <a
        href="/ships"
        class="inline-flex items-center gap-2 text-secondary hover:text-primary transition-colors text-sm font-mono mb-6"
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
            stroke-linejoin="round"><path d="m15 18-6-6 6-6" /></svg
        >
        BACK TO SHIPS
    </a>

    <!-- Header Section -->
    <div
        class="flex flex-col md:flex-row gap-8 mb-10 items-center justify-between bg-terminal-panel border border-border-dark rounded-xl p-8 shadow-lg relative overflow-hidden"
    >
        <!-- Backdrop Huge Icon -->
        <i
            class="xwing-miniatures-ship xwing-miniatures-ship-{data.shipXws} absolute -right-10 -bottom-10 text-[300px] opacity-5 pointer-events-none"
            style="color: {getFactionColor(info.factions)};"
        ></i>

        <div class="flex items-center gap-6 z-10 w-full">
            <!-- Main Huge Icon -->
            <div
                class="flex-shrink-0 w-32 h-32 flex items-center justify-center bg-black/40 rounded-xl border border-white/5 drop-shadow-xl"
            >
                <i
                    class="xwing-miniatures-ship xwing-miniatures-ship-{data.shipXws} text-8xl"
                    style="color: {getFactionColor(info.factions)};"
                ></i>
            </div>

            <!-- Ship Info -->
            <div class="flex-1">
                <div class="flex items-center gap-3 flex-wrap">
                    <h1 class="text-4xl font-sans font-bold text-primary">
                        {info?.name || data.shipXws}
                    </h1>
                    {#if info?.factions}
                        <div
                            class="flex gap-1 border border-border-dark p-1 rounded bg-black/50"
                        >
                            {#each info.factions as faction}
                                <div
                                    class="w-2 h-2 rounded-full mt-2 mx-1"
                                    style="background-color: {getFactionColor([
                                        faction,
                                    ])};"
                                    title={faction}
                                ></div>
                            {/each}
                        </div>
                    {/if}
                </div>
                <div class="flex flex-wrap gap-4 mt-4">
                    <div
                        class="bg-black/50 px-3 py-1.5 rounded border border-border-dark"
                    >
                        <span class="text-xs font-mono text-secondary mr-2"
                            >TOTAL GAMES</span
                        >
                        <span class="text-sm font-bold text-primary"
                            >{stats.games ?? 0}</span
                        >
                    </div>
                    <div
                        class="bg-black/50 px-3 py-1.5 rounded border border-border-dark"
                    >
                        <span class="text-xs font-mono text-secondary mr-2"
                            >POPULARITY</span
                        >
                        <span class="text-sm font-bold text-secondary"
                            >{(stats.popularity ?? 0).toFixed(2)}%</span
                        >
                    </div>
                    {#if stats.win_rate != null}
                        <div
                            class="bg-black/50 px-3 py-1.5 rounded border border-border-dark"
                        >
                            <span class="text-xs font-mono text-secondary mr-2"
                                >WIN RATE</span
                            >
                            <span
                                class="text-sm font-bold"
                                style="color: {wrColor(
                                    parseFloat(stats.win_rate),
                                )}">{stats.win_rate}%</span
                            >
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    </div>

    <!-- Pilot Breakdown Table -->
    <section class="mb-12">
        <h2
            class="text-xl font-sans font-bold text-primary mb-4 uppercase tracking-wider relative inline-block"
        >
            Pilot Breakdown
            <span class="absolute -bottom-1 left-0 w-1/2 h-0.5 bg-primary/30"
            ></span>
        </h2>

        <div
            class="bg-[#0a0a0a] border border-border-dark rounded-lg overflow-hidden shadow-[0_4px_12px_rgba(0,0,0,0.5)]"
        >
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-border-dark bg-[#111]">
                            <th
                                class="px-4 py-3 text-xs font-mono text-secondary font-semibold uppercase tracking-wider"
                                >Pilot</th
                            >
                            <th
                                class="px-4 py-3 text-xs font-mono text-secondary font-semibold uppercase tracking-wider text-right w-24"
                                >Init</th
                            >
                            <th
                                class="px-4 py-3 text-xs font-mono text-secondary font-semibold uppercase tracking-wider text-right w-24"
                                >Cost</th
                            >
                            <th
                                class="px-4 py-3 text-xs font-mono text-secondary font-semibold uppercase tracking-wider text-right w-24"
                                >Games</th
                            >
                            <th
                                class="px-4 py-3 text-xs font-mono text-secondary font-semibold uppercase tracking-wider text-right w-32"
                                >% of Chassis</th
                            >
                            <th
                                class="px-4 py-3 text-xs font-mono text-secondary font-semibold uppercase tracking-wider text-right w-24"
                                >Win Rate</th
                            >
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-border-dark/50">
                        {#each pilots as pilot}
                            {@const pctOfChassis = stats.games
                                ? (
                                      ((pilot.games || 0) / stats.games) *
                                      100
                                  ).toFixed(1)
                                : 0}
                            <tr
                                class="hover:bg-[#ffffff05] transition-colors group cursor-pointer"
                                onclick={() =>
                                    (window.location.href = `/pilot/${pilot.xws}`)}
                            >
                                <td class="px-4 py-3">
                                    <div class="flex items-center gap-3">
                                        <a
                                            href="/pilot/{pilot.xws}"
                                            class="text-sm font-sans font-bold text-primary hover:underline"
                                            >{pilot.name}</a
                                        >
                                        {#if pilot.type}
                                            <span
                                                class="px-1.5 py-0.5 text-[9px] font-mono rounded bg-white/5 text-secondary"
                                                >{pilot.type}</span
                                            >
                                        {/if}
                                    </div>
                                </td>
                                <td class="px-4 py-2 text-right">
                                    <span
                                        class="px-2 py-0.5 text-xs font-mono rounded bg-amber-500/10 text-amber-400"
                                        >I{pilot.initiative || "?"}</span
                                    >
                                </td>
                                <td class="px-4 py-2 text-right">
                                    <span
                                        class="px-2 py-0.5 text-xs font-mono rounded bg-emerald-500/10 text-emerald-400"
                                        >{pilot.cost || "?"} PT</span
                                    >
                                </td>
                                <td
                                    class="px-4 py-2 text-right font-mono text-sm text-secondary"
                                >
                                    {pilot.games || 0}
                                </td>
                                <td class="px-4 py-2 text-right">
                                    <div
                                        class="flex items-center justify-end gap-2"
                                    >
                                        <span
                                            class="text-xs font-mono text-secondary"
                                            >{pctOfChassis}%</span
                                        >
                                        <div
                                            class="w-12 h-1.5 bg-black rounded-full overflow-hidden border border-white/5"
                                        >
                                            <div
                                                class="h-full bg-blue-500/50"
                                                style="width: {pctOfChassis}%"
                                            ></div>
                                        </div>
                                    </div>
                                </td>
                                <td class="px-4 py-2 text-right">
                                    {#if pilot.win_rate && pilot.win_rate !== "NA"}
                                        <span
                                            class="px-2 py-0.5 text-xs font-mono rounded font-bold"
                                            style="background: {wrColor(
                                                parseFloat(pilot.win_rate),
                                            )}15; color: {wrColor(
                                                parseFloat(pilot.win_rate),
                                            )};"
                                        >
                                            {parseFloat(pilot.win_rate).toFixed(
                                                1,
                                            )}%
                                        </span>
                                    {:else}
                                        <span
                                            class="text-xs font-mono text-secondary"
                                            >-</span
                                        >
                                    {/if}
                                </td>
                            </tr>
                        {:else}
                            <tr
                                ><td
                                    colspan="6"
                                    class="text-center py-6 text-sm font-mono text-secondary"
                                    >No pilot data available.</td
                                ></tr
                            >
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    </section>

    <!-- Top Lists -->
    <section class="mb-12">
        <h2
            class="text-xl font-sans font-bold text-primary mb-4 uppercase tracking-wider relative inline-block"
        >
            Top Performing Lists
            <span class="absolute -bottom-1 left-0 w-1/2 h-0.5 bg-primary/30"
            ></span>
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {#each lists as list}
                <a href="/list/{list.signature}" class="block group h-full">
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-sm hover:border-primary/30 hover:scale-[1.01] transition-all h-full flex flex-col justify-between"
                    >
                        <div
                            class="mb-3 flex items-start gap-2 flex-wrap text-sm font-sans font-bold text-primary"
                        >
                            {#each list.ship_array || [] as sip}
                                <span>{sip}</span>
                            {/each}
                        </div>
                        <div
                            class="flex flex-wrap items-center gap-2 border-t border-border-dark pt-3"
                        >
                            <span
                                class="px-2 py-0.5 text-xs font-mono rounded bg-white/5 text-secondary"
                                >{list.games || 0} GAMES</span
                            >
                            {#if list.games}
                                <span
                                    class="px-2 py-0.5 text-xs font-mono rounded font-bold"
                                    style="color: {wrColor(
                                        (list.wins / list.games) * 100,
                                    )}; background: {wrColor(
                                        (list.wins / list.games) * 100,
                                    )}15"
                                >
                                    {((list.wins / list.games) * 100).toFixed(
                                        1,
                                    )}% WR
                                </span>
                            {/if}
                            <span
                                class="ml-auto text-xs font-mono text-secondary opacity-60 group-hover:opacity-100 group-hover:text-primary transition-opacity"
                                >View List &rarr;</span
                            >
                        </div>
                    </div>
                </a>
            {:else}
                <div
                    class="col-span-full py-8 text-center text-sm font-mono text-secondary bg-terminal-panel border border-border-dark rounded-lg"
                >
                    No list data available for this ship.
                </div>
            {/each}
        </div>
    </section>

    <!-- Top Squadrons -->
    <section>
        <h2
            class="text-xl font-sans font-bold text-primary mb-4 uppercase tracking-wider relative inline-block"
        >
            Top Squadrons
            <span class="absolute -bottom-1 left-0 w-1/2 h-0.5 bg-primary/30"
            ></span>
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {#each squadrons as squad}
                <a
                    href="/squadron/{squad.signature}"
                    class="block group h-full"
                >
                    <div
                        class="bg-terminal-panel border border-border-dark rounded-lg p-4 shadow-sm hover:border-primary/30 hover:scale-[1.01] transition-all h-full flex flex-col justify-between"
                    >
                        <div
                            class="mb-3 text-sm font-sans font-bold text-primary break-all"
                        >
                            {squad.signature}
                        </div>
                        <div
                            class="flex flex-wrap items-center gap-2 border-t border-border-dark pt-3"
                        >
                            <span
                                class="px-2 py-0.5 text-xs font-mono rounded bg-white/5 text-secondary"
                                >{squad.count || squad.games || 0} GAMES</span
                            >
                            {#if squad.win_rate}
                                <span
                                    class="px-2 py-0.5 text-xs font-mono rounded font-bold"
                                    style="color: {wrColor(
                                        parseFloat(squad.win_rate),
                                    )}; background: {wrColor(
                                        parseFloat(squad.win_rate),
                                    )}15"
                                >
                                    {squad.win_rate}% WR
                                </span>
                            {/if}
                            <span
                                class="ml-auto text-xs font-mono text-secondary opacity-60 group-hover:opacity-100 group-hover:text-primary transition-opacity"
                                >View Squad &rarr;</span
                            >
                        </div>
                    </div>
                </a>
            {:else}
                <div
                    class="col-span-full py-8 text-center text-sm font-mono text-secondary bg-terminal-panel border border-border-dark rounded-lg"
                >
                    No squadron data available for this ship.
                </div>
            {/each}
        </div>
    </section>
</div>
