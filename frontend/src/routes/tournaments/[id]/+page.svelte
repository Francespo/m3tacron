<script lang="ts">
    import { getFormatFullLabel } from "$lib/data/formats";
    import { getSourceLabel } from "$lib/data/source";
    import BackLink from "$lib/components/BackLink.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";
    import { invalidateAll } from "$app/navigation";

    let { data } = $props();

    // The loader streams the detail payload in via `detailPromise`
    // (non-blocking navigation). The {#await} block in the template gates
    // rendering on it; this state only feeds the document title (non-
    // rendering logic that needs the resolved payload).
    let detail = $state<any>(null);
    $effect(() => {
        let cancelled = false;
        data.detailPromise.then((d: any) => {
            if (!cancelled) detail = d;
        });
        return () => {
            cancelled = true;
        };
    });
    const headTournament = $derived(detail?.tournament);

    function retry() {
        invalidateAll();
    }

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
        type?: string | null;
        scenario?: string | null;
        player1: string;
        player2: string;
        score1: number;
        score2: number;
        winner_id?: number | string | null;
    };

    type RoundGroup = {
        key: string;
        roundNum: number;
        type: "swiss" | "cut";
        label: string;
        shortLabel: string;
        matches: Match[];
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

    function getCutStageLabel(matchCount: number, cutIndexFromEnd: number): string {
        if (matchCount === 1) return "Finals";
        if (matchCount === 2) return "Semi-Finals";
        if (matchCount >= 3 && matchCount <= 4) return "Quarter-Finals";
        if (matchCount >= 5 && matchCount <= 8) return "Round of 16";
        if (matchCount >= 9 && matchCount <= 16) return "Round of 32";
        if (matchCount >= 17 && matchCount <= 32) return "Round of 64";
        if (matchCount >= 33 && matchCount <= 64) return "Round of 128";

        if (cutIndexFromEnd === 0) return "Finals";
        if (cutIndexFromEnd === 1) return "Semi-Finals";
        if (cutIndexFromEnd === 2) return "Quarter-Finals";
        if (cutIndexFromEnd === 3) return "Round of 16";
        if (cutIndexFromEnd === 4) return "Round of 32";
        if (cutIndexFromEnd === 5) return "Round of 64";

        return "Cut Round";
    }

    // Group matches by type and round, distinguishing Swiss from Cut rounds.
    function groupRoundsByType(matches: Match[]): RoundGroup[] {
        const map = new Map<string, { roundNum: number; type: "swiss" | "cut"; matches: Match[] }>();

        for (const m of matches as Match[]) {
            const rawType = (m.type || "").toLowerCase().trim();
            const type: "swiss" | "cut" = rawType === "cut" ? "cut" : "swiss";
            const key = `${type}_${m.round}`;

            if (!map.has(key)) {
                map.set(key, { roundNum: m.round, type, matches: [] });
            }
            map.get(key)!.matches.push(m);
        }

        const entries = Array.from(map.values());
        const swissRounds = entries.filter((e) => e.type === "swiss").sort((a, b) => a.roundNum - b.roundNum);
        // Knockout stages run from the largest bracket to the final, so order
        // cut rounds by match count descending (most matches = earliest stage).
        // round_number semantics vary by source (Top-N size vs sequential), so
        // match count is the reliable ordering signal.
        const cutRounds = entries
            .filter((e) => e.type === "cut")
            .sort((a, b) => b.matches.length - a.matches.length);

        const result: RoundGroup[] = [];

        swissRounds.forEach((s) => {
            result.push({
                key: `swiss_${s.roundNum}`,
                roundNum: s.roundNum,
                type: "swiss",
                label: `SWISS · ROUND ${s.roundNum}`,
                shortLabel: `S${s.roundNum}`,
                matches: s.matches,
            });
        });

        const totalCut = cutRounds.length;
        cutRounds.forEach((c, idx) => {
            const indexFromEnd = totalCut - 1 - idx;
            const stage = getCutStageLabel(c.matches.length, indexFromEnd);
            result.push({
                key: `cut_${c.roundNum}`,
                roundNum: c.roundNum,
                type: "cut",
                label: `CUT · ${stage.toUpperCase()}`,
                shortLabel: stage,
                matches: c.matches,
            });
        });

        return result;
    }

    // --- Match round carousel state ---
    let currentRoundIndex = $state(0);

    // Derived round groups for clamping/navigation (reacts to streamed detail)
    const detailMatches = $derived(detail?.matches ?? []);
    const roundGroupsDerived = $derived(groupRoundsByType(detailMatches));

    $effect(() => {
        const max = roundGroupsDerived.length - 1;
        if (currentRoundIndex > max) currentRoundIndex = max;
        if (currentRoundIndex < 0) currentRoundIndex = 0;
    });

    function prevRound() {
        if (currentRoundIndex > 0) currentRoundIndex--;
    }
    function nextRound() {
        if (currentRoundIndex < roundGroupsDerived.length - 1) currentRoundIndex++;
    }

    // --- Standings pagination ---
    const STANDINGS_PER_PAGE = 10;
    let swissPage = $state(0);
    let cutPage = $state(0);

    const swissTotalPages = $derived(
        Math.ceil((detail?.players_swiss?.length ?? 0) / STANDINGS_PER_PAGE)
    );
    const cutTotalPages = $derived(
        Math.ceil((detail?.players_cut?.length ?? 0) / STANDINGS_PER_PAGE)
    );

    // --- Standings tab toggle ---
    const hasCut = $derived((detail?.players_cut?.length ?? 0) > 0);
    const hasSwiss = $derived((detail?.players_swiss?.length ?? 0) > 0);
    let standingsTab = $state<"swiss" | "cut">("swiss");

    // Reset pagination and tab when tournament changes
    $effect(() => {
        void data.detailPromise;
        void detail;
        swissPage = 0;
        cutPage = 0;
        standingsTab = "swiss";
        currentRoundIndex = 0;
    });

    // Active standings based on tab
    const activeStandings = $derived(
        standingsTab === "cut"
            ? (detail?.players_cut ?? [])
            : (detail?.players_swiss ?? [])
    );
    const activeTotalPages = $derived(
        standingsTab === "cut" ? cutTotalPages : swissTotalPages
    );
    const activePage = $derived(
        standingsTab === "cut" ? cutPage : swissPage
    );
    // Page slice — the list renders this, not the full array
    const activePageItems = $derived(
        activeStandings.slice(
            activePage * STANDINGS_PER_PAGE,
            (activePage + 1) * STANDINGS_PER_PAGE
        )
    );
    function prevPage() {
        if (standingsTab === "cut") cutPage--;
        else swissPage--;
    }
    function nextPage() {
        if (standingsTab === "cut") cutPage++;
        else swissPage++;
    }

    // --- Knockout placement detection ---
    // Canonical standings have unique sequential ranks (1, 2, 3, ...).
    // Knockout brackets share ranks: everyone eliminated at the same stage
    // gets the bracket size as rank (1=winner, 2=runner-up, 4=semi-final,
    // 8=quarter-final, 16=round of 16, ...). When that pattern is present we
    // render a compact "reached this stage" view instead of a standings table.
    const cutIsKnockout = $derived.by(() => {
        const players: { rank: number }[] = detail?.players_cut ?? [];
        if (players.length < 2) return false;
        const ranks = players.map((p) => p.rank);
        const counts = new Map<number, number>();
        for (const r of ranks) counts.set(r, (counts.get(r) ?? 0) + 1);
        const shared = [...counts.values()].filter((c) => c > 1).reduce((a, b) => a + b, 0);
        const allPowersOfTwo = ranks.every((r) => r > 0 && (r & (r - 1)) === 0);
        return shared / players.length > 0.5 || (allPowersOfTwo && shared > 0);
    });

    function cutStageLabel(rank: number): string {
        if (rank === 1) return "Winner";
        if (rank === 2) return "Runner-Up";
        if (rank === 4) return "Semi-Finals";
        if (rank === 8) return "Quarter-Finals";
        if (rank === 16) return "Round of 16";
        if (rank === 32) return "Round of 32";
        if (rank === 64) return "Round of 64";
        if (rank === 128) return "Round of 128";
        return `Place ${rank}`;
    }

    // Group the current cut page by bracket rank (knockout view only)
    const cutTierGroups = $derived.by(() => {
        const groups = new Map<number, { rank: number; players: typeof activePageItems }>();
        for (const p of activePageItems) {
            const pr = (p as any).rank as number;
            if (!groups.has(pr)) groups.set(pr, { rank: pr, players: [] as any });
            (groups.get(pr)!.players as any).push(p);
        }
        return Array.from(groups.values()).sort((a, b) => a.rank - b.rank);
    });
</script>

<svelte:head>
    <title>{headTournament ? headTournament.name : "Tournament"} | M3taCron</title>
</svelte:head>

<div class="p-6 md:p-8 max-w-[1400px] mx-auto">
    {#await data.detailPromise}
        <p class="text-secondary font-mono text-sm mb-6">Loading…</p>

        <!-- Loading Skeleton (matches detail layout: title row, info grid,
             location card, standings list) -->
        <div class="space-y-6">
            <div
                class="animate-pulse bg-[#ffffff06] rounded-lg h-10 w-72 max-w-full"
            ></div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                {#each Array(4) as _}
                    <div
                        class="animate-pulse bg-[#ffffff06] rounded-lg h-20"
                    ></div>
                {/each}
            </div>
            <div
                class="animate-pulse bg-[#ffffff06] rounded-lg h-12"
            ></div>
            <div class="space-y-2">
                {#each Array(6) as _}
                    <div
                        class="animate-pulse bg-[#ffffff06] rounded-md h-10"
                    ></div>
                {/each}
            </div>
        </div>
    {:then detail}
        {#if detail?.tournament}
            {@const t = detail.tournament}
            {@const matches = detail.matches ?? []}
            {@const roundGroups = groupRoundsByType(matches)}
            {@const hasCutTpl = (detail.players_cut?.length ?? 0) > 0}
            {@const hasSwissTpl = (detail.players_swiss?.length ?? 0) > 0}
            {@const activeStandingsTpl = standingsTab === 'cut' ? (detail.players_cut ?? []) : (detail.players_swiss ?? [])}
            {@const activeTotalPagesTpl = Math.ceil(activeStandingsTpl.length / STANDINGS_PER_PAGE)}
            {@const activePageTpl = standingsTab === 'cut' ? cutPage : swissPage}
            {@const activePageItemsTpl = activeStandingsTpl.slice(activePageTpl * STANDINGS_PER_PAGE, (activePageTpl + 1) * STANDINGS_PER_PAGE)}
            {@const cutIsKnockoutTpl = (() => { const players = (detail.players_cut ?? []) as { rank: number }[]; if (players.length < 2) return false; const ranks = players.map((p) => p.rank); const counts = new Map<number, number>(); for (const r of ranks) counts.set(r, (counts.get(r) ?? 0) + 1); const shared = [...counts.values()].filter((c) => c > 1).reduce((a, b) => a + b, 0); const allPow = ranks.every((r) => r > 0 && (r & (r - 1)) === 0); return shared / players.length > 0.5 || (allPow && shared > 0); })()}
            {@const cutTierGroupsTpl = (() => { const groups = new Map<number, { rank: number; players: typeof activePageItemsTpl }>(); for (const p of activePageItemsTpl) { const pr = (p as any).rank as number; if (!groups.has(pr)) groups.set(pr, { rank: pr, players: [] as any }); (groups.get(pr)!.players as any).push(p); } return Array.from(groups.values()).sort((a, b) => a.rank - b.rank); })()}
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
                <!-- Standings (toggleable when both Cut + Swiss exist) -->
                {#if hasCutTpl || hasSwissTpl}
                    <div class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden">
                        <div class="bg-[rgba(255,255,255,0.02)] border-b border-border-dark p-3 flex items-center justify-between gap-3">
                            {#if hasCutTpl && hasSwissTpl}
                                <div class="flex items-center bg-[rgba(255,255,255,0.05)] rounded-md p-0.5">
                                    <button
                                        class="px-3 py-1 rounded-md text-xs font-mono font-bold uppercase tracking-wider transition-colors {standingsTab === 'swiss' ? 'bg-[rgba(255,255,255,0.1)] text-primary' : 'text-secondary hover:text-primary'}"
                                        onclick={() => { standingsTab = 'swiss'; }}
                                    >Swiss</button>
                                    <button
                                        class="px-3 py-1 rounded-md text-xs font-mono font-bold uppercase tracking-wider transition-colors {standingsTab === 'cut' ? 'bg-[rgba(255,255,255,0.1)] text-primary' : 'text-secondary hover:text-primary'}"
                                        onclick={() => { standingsTab = 'cut'; }}
                                    >Cut</button>
                                </div>
                            {:else}
                                <h2 class="text-sm font-bold text-primary font-mono uppercase tracking-wider">{hasCutTpl ? "CUT STANDINGS" : "STANDINGS"}</h2>
                            {/if}

                            <!-- Standings Pagination Controls in Top Header -->
                            <div class="flex items-center gap-3">
                                {#if activeTotalPagesTpl > 1}
                                    <span class="text-xs font-mono text-secondary">
                                        Page {activePageTpl + 1} / {activeTotalPagesTpl}
                                    </span>
                                    <div class="flex items-center gap-1">
                                        <button
                                            class="p-1.5 rounded-md border border-border-dark text-primary hover:bg-[rgba(255,255,255,0.1)] transition-colors disabled:opacity-30 disabled:cursor-default"
                                            disabled={activePageTpl === 0}
                                            onclick={prevPage}
                                            aria-label="Previous page"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                                        </button>
                                        <button
                                            class="p-1.5 rounded-md border border-border-dark text-primary hover:bg-[rgba(255,255,255,0.1)] transition-colors disabled:opacity-30 disabled:cursor-default"
                                            disabled={activePageTpl >= activeTotalPagesTpl - 1}
                                            onclick={nextPage}
                                            aria-label="Next page"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                                        </button>
                                    </div>
                                {/if}
                            </div>
                        </div>

                        <!-- Standings Player List -->
                        {#if standingsTab === 'cut' && cutIsKnockoutTpl}
                            <!-- Knockout placement: group by reached stage, compact -->
                            <div class="flex flex-col">
                                {#each cutTierGroupsTpl as g}
                                    <div class="flex items-center gap-3 p-2.5 border-b border-border-dark last:border-0">
                                        <span class="w-20 shrink-0 text-[10px] font-mono uppercase tracking-wide text-right leading-tight {g.rank <= 2 ? 'text-green-400 font-bold' : 'text-amber-300'}">{cutStageLabel(g.rank)}</span>
                                        <div class="flex flex-wrap items-center gap-x-3 gap-y-1 min-w-0">
                                            {#each g.players as p}
                                                <span class="inline-flex items-center gap-1.5 min-w-0">
                                                    <FactionIcon faction={p.faction} size="sm" />
                                                    <span class="font-mono text-sm text-primary truncate max-w-[160px]" title={p.name}>{p.name}</span>
                                                </span>
                                            {/each}
                                        </div>
                                    </div>
                                {/each}
                            </div>
                        {:else}
                        <div class="flex flex-col">
                            {#each activePageItemsTpl as p}
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
                        {/if}
                    </div>
                {/if}
            </div>

            <!-- Matches (round carousel) -->
            {#if roundGroups.length > 0}
                {@const group = roundGroups[currentRoundIndex]}
                {@const dom = dominantScenario(group.matches)}
                <div class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden flex flex-col" style="max-height: calc(100vh - 120px);">
                    <div class="bg-[rgba(255,255,255,0.02)] border-b border-border-dark p-3 flex items-center justify-between gap-3 shrink-0">
                        <div class="flex flex-col min-w-0">
                            <div class="flex items-center gap-2">
                                <h2 class="text-sm font-bold text-primary font-mono uppercase tracking-wider">
                                    {group.label}
                                </h2>
                                <span class="px-1.5 py-0.5 text-[10px] font-mono rounded font-semibold uppercase {group.type === 'cut' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'}">
                                    {group.type === 'cut' ? 'Knockout' : 'Swiss'}
                                </span>
                            </div>
                            {#if dom}
                                <span class="text-[11px] font-mono text-secondary uppercase tracking-wider truncate">{humanizeScenario(dom)}</span>
                            {/if}
                        </div>

                        <!-- Matches Round Controls in Top Header -->
                        <div class="flex items-center gap-3 shrink-0">
                            {#if roundGroups.length > 1}
                                <span class="text-xs font-mono text-secondary">
                                    Round {currentRoundIndex + 1} / {roundGroups.length}
                                </span>
                                <div class="flex items-center gap-1">
                                    <button
                                        class="p-1.5 rounded-md border border-border-dark text-primary hover:bg-[rgba(255,255,255,0.1)] transition-colors disabled:opacity-30 disabled:cursor-default"
                                        disabled={currentRoundIndex === 0}
                                        onclick={prevRound}
                                        aria-label="Previous round"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                                    </button>
                                    <button
                                        class="p-1.5 rounded-md border border-border-dark text-primary hover:bg-[rgba(255,255,255,0.1)] transition-colors disabled:opacity-30 disabled:cursor-default"
                                        disabled={currentRoundIndex >= roundGroups.length - 1}
                                        onclick={nextRound}
                                        aria-label="Next round"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                                    </button>
                                </div>
                            {/if}
                        </div>
                    </div>

                    <!-- Matches List -->
                    <div class="flex flex-col divide-y divide-border-dark/50 overflow-y-auto p-2">
                        {#each group.matches as m}
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

                    <!-- Quick Jump Round Bar -->
                    {#if roundGroups.length > 1}
                        <div class="flex items-center justify-center gap-1.5 p-2 border-t border-border-dark shrink-0 overflow-x-auto">
                            {#each roundGroups as rg, i}
                                <button
                                    class="px-2 py-0.5 text-[11px] font-mono rounded transition-colors {i === currentRoundIndex ? (rg.type === 'cut' ? 'bg-amber-500/30 text-amber-200 border border-amber-500/40' : 'bg-primary/20 text-primary border border-primary/30') : 'text-secondary hover:text-primary hover:bg-[rgba(255,255,255,0.05)]'}"
                                    onclick={() => currentRoundIndex = i}
                                >{rg.shortLabel}</button>
                            {/each}
                        </div>
                    {/if}
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
            <div class="flex items-center gap-3">
                <a
                    href="/tournaments"
                    class="px-4 py-2 border border-border-dark rounded-md text-sm font-sans text-primary hover:bg-[rgba(255,255,255,0.05)] active:bg-[rgba(255,255,255,0.1)] transition-colors"
                >
                    ← Back to Tournaments
                </a>
                <button
                    type="button"
                    onclick={retry}
                    class="px-4 py-2 border border-border-dark rounded-md text-sm font-sans text-primary hover:bg-[rgba(255,255,255,0.05)] active:bg-[rgba(255,255,255,0.1)] transition-colors"
                >
                    Try again
                </button>
            </div>
        </div>
        {/if}
    {/await}
</div>
