<script lang="ts">
    import { getFormatFullLabel } from "$lib/data/formats";
    import { getSourceLabel } from "$lib/data/source";
    import BackLink from "$lib/components/BackLink.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";

    let { data } = $props();
    const t = $derived(data.detail?.tournament);
    const matches = $derived(data.detail?.matches ?? []);

    // Shape of a single match row from the backend. The tournament detail
    // endpoint is untyped JSON, so we declare it locally for the bits the
    // template actually reads. Note: the API does NOT expose per-player IDs
    // on the match row — only `player1` / `player2` name strings and a
    // `winner_id` that may come back as either a number or a string
    // depending on the data source. The original code did
    // `m.winner_id === m.player1_id`, which (a) was a no-op because
    // `player1_id` doesn't exist and (b) would have failed type-equality
    // for string vs number winner_id values. We now derive the winner from
    // the actual scores (type-safe, no ID comparison needed).
    type Match = {
        round: number;
        scenario?: string | null;
        player1: string;
        player2: string;
        score1: number;
        score2: number;
        winner_id?: number | string | null;
    };

    // Pick the dominant scenario for a round. Byes (matches with no scenario)
    // get bucketed with whatever scenarios are present; if the round has no
    // scenarios at all, returns null so the round header omits the separator.
    function dominantScenario(matchesInRound: Match[]): string | null {
        const scenarios = matchesInRound
            .map((m) => (m.scenario || "").trim())
            .filter((s) => s !== "");
        if (scenarios.length === 0) return null;
        const unique = [...new Set(scenarios)];
        if (unique.length === 1) return unique[0];
        return "MIXED SCENARIO";
    }

    // Convert an ALL_CAPS_SNAKE_CASE scenario name (as stored by the
    // backend) into a human-readable sentence-case label, e.g.
    //   "ASSAULT_AT_THE_SATELLITE_ARRAY" -> "Assault at the satellite array"
    // The `uppercase` class on the rendered span will style it back to
    // display caps, but the underlying text stays sentence-case so screen
    // readers don't shout the value at the user.
    function humanizeScenario(s: string | null | undefined): string {
        if (!s) return "";
        return s
            .replace(/_/g, " ")
            .toLowerCase()
            .replace(/^./, (c) => c.toUpperCase());
    }

    /**
     * Pick the winner of a match by score. The backend's `winner_id` field
     * can be unreliable across data types (number vs string depending on
     * source), so we fall back to the actual scores. Returns the *name* of
     * the winning player (so the template can compare it directly to
     * `m.player1` / `m.player2`), or null for ties / invalid matches.
     */
    function pickWinnerName(m: Match): string | null {
        if (m.score1 > m.score2) return m.player1;
        if (m.score2 > m.score1) return m.player2;
        return null;
    }

    // Group matches by round, sorted ascending by round number. The backend
    // already orders matches by round, but grouping defensively keeps the
    // UI correct even if that ever changes.
    const roundGroups = $derived.by(() => {
        const groups = new Map<number, Match[]>();
        for (const m of matches as Match[]) {
            const r = m.round;
            if (!groups.has(r)) groups.set(r, []);
            groups.get(r)!.push(m);
        }
        return Array.from(groups.entries()).sort((a, b) => a[0] - b[0]);
    });
</script>

<svelte:head>
    <title>{t ? t.name : "Tournament"} | M3taCron</title>
</svelte:head>

<div class="p-6 md:p-8 max-w-[1400px] mx-auto">
    {#if t}
        <!-- Header -->
        <div class="border-b border-border-dark pb-6 mb-6">
            <div class="flex items-center gap-3 mb-2">
                <BackLink href="/tournaments" ariaLabel="Back to Tournaments" />
            </div>
            <h1 class="text-3xl font-sans font-bold text-primary mt-4 mb-6">{t.name}</h1>
        </div>

        <!-- Info Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Format</span
                >
                <span class="text-lg font-bold text-primary font-mono"
                    >{getFormatFullLabel(t.format)}</span
                >
            </div>
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Date</span
                >
                <span class="text-lg font-bold text-primary font-mono"
                    >{t.date}</span
                >
            </div>
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Players</span
                >
                <span class="text-lg font-bold text-primary font-mono"
                    >{t.players}</span
                >
            </div>
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-4 flex flex-col"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Source</span
                >
                <div class="flex items-center gap-2 min-w-0">
                    <span class="text-lg font-bold text-primary font-mono truncate"
                        >{getSourceLabel(t.source)}</span
                    >
                    {#if t.url}
                        <a
                            href={t.url}
                            target="_blank"
                            rel="noreferrer"
                            class="inline-flex items-center gap-1 text-[11px] font-mono text-primary hover:text-white transition-colors"
                            title="Open tournament on source"
                            aria-label="Open tournament on source"
                        >
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="13"
                                height="13"
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
                            <span>View on Source</span>
                        </a>
                    {/if}
                </div>
            </div>
        </div>

        <!-- Location -->
        <div
            class="bg-terminal-panel border border-border-dark rounded-lg p-4 mb-6"
        >
            <span class="text-xs text-secondary font-mono uppercase mb-1 block"
                >Location</span
            >
            <span class="text-base text-primary font-sans">{t.location}</span>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <div class="flex flex-col gap-6">
                <!-- Cut Standings -->
                {#if data.detail.players_cut && data.detail.players_cut.length > 0}
                    <div class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden">
                        <div class="bg-[rgba(255,255,255,0.02)] border-b border-border-dark p-3">
                            <h2 class="text-sm font-bold text-primary font-mono uppercase tracking-wider">CUT STANDINGS</h2>
                        </div>
                        <div class="flex flex-col">
                            {#each data.detail.players_cut as p}
                                <div class="flex items-center gap-3 p-3 border-b border-border-dark last:border-0 hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                                    <span class="w-8 h-8 rounded-full bg-[rgba(255,255,255,0.1)] flex items-center justify-center font-mono text-sm">{p.rank}</span>
                                    <FactionIcon faction={p.faction} size="md" />
                                    <div class="flex flex-col">
                                        <span class="font-mono text-primary font-medium">{p.name}</span>
                                        <span class="text-xs text-secondary">
                                            <span class="text-green-400 font-bold">{p.wins}W</span>
                                            <span class="mx-0.5">-</span>
                                            <span class="text-red-400 font-bold">{p.losses}L</span>
                                        </span>
                                    </div>
                                    <div class="flex-1"></div>
                                    {#if p.list_id}
                                        <a
                                            href="/list/{p.list_id}"
                                            class="px-3 py-1 border border-border-dark rounded-md text-xs font-mono hover:bg-[rgba(255,255,255,0.1)] text-primary no-underline"
                                            >LIST</a
                                        >
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- Swiss Standings -->
                <div class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden">
                    <div class="bg-[rgba(255,255,255,0.02)] border-b border-border-dark p-3">
                        <h2 class="text-sm font-bold text-primary font-mono uppercase tracking-wider">{data.detail.players_cut?.length > 0 ? "SWISS STANDINGS" : "STANDINGS"}</h2>
                    </div>
                    <div class="flex flex-col">
                            {#each (data.detail.players_swiss || []) as p}
                                <div class="flex items-center gap-3 p-3 border-b border-border-dark last:border-0 hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                                    <span class="w-8 h-8 rounded-full bg-[rgba(255,255,255,0.1)] flex items-center justify-center font-mono text-sm">{p.rank}</span>
                                    <FactionIcon faction={p.faction} size="md" />
                                    <div class="flex flex-col">
                                        <span class="font-mono text-primary font-medium">{p.name}</span>
                                        <span class="text-xs text-secondary">
                                            <span class="text-green-400 font-bold">{p.wins}W</span>
                                            <span class="mx-0.5">-</span>
                                            <span class="text-red-400 font-bold">{p.losses}L</span>
                                        </span>
                                    </div>
                                    <div class="flex-1"></div>
                                    {#if p.list_id}
                                        <a
                                            href="/list/{p.list_id}"
                                            class="px-3 py-1 border border-border-dark rounded-md text-xs font-mono hover:bg-[rgba(255,255,255,0.1)] text-primary no-underline"
                                            >LIST</a
                                        >
                                    {/if}
                                </div>
                            {/each}
                    </div>
                </div>
            </div>

            <!-- Matches -->
            {#if matches.length > 0}
                <div class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden">
                    <div class="bg-[rgba(255,255,255,0.02)] border-b border-border-dark p-3">
                        <h2 class="text-sm font-bold text-primary font-mono uppercase tracking-wider">MATCHES</h2>
                    </div>
                    <div class="flex flex-col gap-2 p-2">
                        {#each roundGroups as [roundNum, roundMatches]}
                            {@const dom = dominantScenario(roundMatches)}
                            <div class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden">
                                <div class="bg-[rgba(255,255,255,0.02)] border-b border-border-dark p-3 flex items-center gap-3">
                                    <h3 class="text-sm font-bold text-primary font-mono">ROUND {roundNum}</h3>
                                    {#if dom}
                                        <span class="text-xs font-mono text-secondary uppercase tracking-wider">· {humanizeScenario(dom)}</span>
                                    {/if}
                                </div>
                                <div class="flex flex-col divide-y divide-border-dark/50">
                                    {#each roundMatches as m}
                                        {@const winnerName = pickWinnerName(m)}
                                        <div class="flex items-center justify-between gap-3 p-2 mx-1 my-0.5 rounded-md bg-[rgba(255,255,255,0.02)] hover:bg-[rgba(255,255,255,0.04)] transition-colors">
                                            <span class="font-mono text-sm text-left flex-1 truncate pr-2 {winnerName === m.player1 ? 'text-green-400 font-bold' : winnerName === null ? 'text-secondary' : 'text-primary'}" title={m.player1}>{m.player1}</span>
                                            <div class="flex items-center justify-center gap-1 font-mono text-base w-14 font-bold">
                                                <span class={winnerName === m.player1 ? 'text-green-400 bg-green-500/15 px-2 py-0.5 rounded-md border border-green-500/30' : winnerName === null ? 'text-secondary' : 'text-red-400'}>{m.score1}</span>
                                                <span class="text-secondary">-</span>
                                                <span class={winnerName === m.player2 ? 'text-green-400 bg-green-500/15 px-2 py-0.5 rounded-md border border-green-500/30' : winnerName === null ? 'text-secondary' : 'text-red-400'}>{m.score2}</span>
                                            </div>
                                            <span class="font-mono text-sm text-right flex-1 truncate pl-2 {winnerName === m.player2 ? 'text-green-400 font-bold' : winnerName === null ? 'text-secondary' : 'text-primary'}" title={m.player2}>{m.player2}</span>
                                        </div>
                                    {/each}
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
                class="px-4 py-2 border border-border-dark rounded-md text-sm font-sans text-primary hover:bg-[rgba(255,255,255,0.05)] transition-colors"
            >
                ← Back to Tournaments
            </a>
        </div>
    {/if}
</div>
