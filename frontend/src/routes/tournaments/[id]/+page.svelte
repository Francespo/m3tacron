<script lang="ts">
    import {
        getDisplayFormatFullLabel,
        resolveDisplayFormat,
        getFormatColor,
    } from "$lib/data/formats";
    import { getSourceLabel } from "$lib/data/source";
    import BackLink from "$lib/components/BackLink.svelte";
    import ErrorPanel from "$lib/components/ErrorPanel.svelte";
    import FactionIcon from "$lib/components/FactionIcon.svelte";
    import BracketView from "./BracketView.svelte";
    import { invalidateAll } from "$app/navigation";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    // The loader streams the detail payload in via `detailPromise`
    // (non-blocking navigation). The {#await} block in the template gates
    // rendering on it; this state only feeds the document title (non-
    // rendering logic that needs the resolved payload).
    let detail = $state<any>(null);
    $effect(() => {
        let cancelled = false;
        if (data?.detailPromise) {
            data.detailPromise.then((d: any) => {
                if (!cancelled) detail = d;
            });
        }
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
        if ((m.player2 || "").trim().toLowerCase() === "bye") return m.player1;
        if ((m.player1 || "").trim().toLowerCase() === "bye") return m.player2;
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

    function tieBreakerLabel(format: string): string {
        if (["ffg", "legacy_x2po", "legacy_xlc", "legacy_pandorum"].includes(format)) {
            return "Margin / Tie Breaker";
        }
        return "Victory Points";
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

    function prevRound() {
        if (currentRoundIndex > 0) currentRoundIndex--;
    }
    function nextRound() {
        currentRoundIndex++;
    }

    // --- Standings pagination ---
    const STANDINGS_PER_PAGE = 10;
    let swissPage = $state(0);
    let swissStandingsHeight = $state(0);

    const playerMap = $derived.by(() => {
        const map = new Map<string, any>();
        if (detail?.players_cut) {
            for (const p of detail.players_cut) {
                if (p.name) map.set(p.name.trim().toLowerCase(), p);
            }
        }
        if (detail?.players_swiss) {
            for (const p of detail.players_swiss) {
                if (p.name && !map.has(p.name.trim().toLowerCase())) {
                    map.set(p.name.trim().toLowerCase(), p);
                }
            }
        }
        return map;
    });

    // Reset pagination when tournament ID changes
    let prevTournamentId: string | undefined = undefined;
    $effect(() => {
        const curId = data?.id;
        if (curId && curId !== prevTournamentId) {
            prevTournamentId = curId;
            swissPage = 0;
            currentRoundIndex = 0;
        }
    });
</script>

<svelte:head>
    <title>{headTournament ? headTournament.name : "Tournament"} | M3taCron</title>
</svelte:head>

<div class="p-6 md:p-8 max-w-[1400px] mx-auto">
    {#await data?.detailPromise}
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
            <!-- Header -->
        <div class="border-b border-border-dark pb-6 mb-6">
            <div class="flex items-center gap-3 mb-2">
                <BackLink href="/tournaments" ariaLabel="Back to Tournaments" />
            </div>
            <h1 class="text-3xl font-sans font-bold text-primary mt-4 mb-6">{t.name}</h1>
        </div>

        <!-- Info Grid — 5 capsules on one row (desktop), Location shares the row -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-3 flex flex-col min-w-0"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Format</span
                >
                <span class="text-base font-bold font-mono truncate" style="color: {getFormatColor(getDisplayFormatFullLabel(t.format, t.date) === 'Unknown' ? 'other' : resolveDisplayFormat(t.format, t.date))};"
                    >{getDisplayFormatFullLabel(t.format, t.date)}</span
                >
            </div>
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-3 flex flex-col min-w-0"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Date</span
                >
                <span class="text-base font-bold text-primary font-mono truncate"
                    >{t.date}</span
                >
            </div>
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-3 flex flex-col min-w-0"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Players</span
                >
                <span class="text-base font-bold text-primary font-mono"
                    >{t.players}</span
                >
            </div>
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-3 flex flex-col min-w-0"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Source</span
                >
                {#if t.url}
                    <a
                        href={t.url}
                        target="_blank"
                        rel="noreferrer"
                        class="inline-flex items-center gap-1.5 text-base font-bold text-primary font-mono truncate hover:text-white transition-colors underline decoration-dotted decoration-white/20 underline-offset-4 hover:decoration-white/50"
                        title="Open tournament on {getSourceLabel(t.source)}"
                        aria-label="Open tournament on {getSourceLabel(t.source)}"
                    >
                        <span class="truncate">{getSourceLabel(t.source)}</span>
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="12"
                            height="12"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            class="shrink-0 opacity-60"
                            ><path
                                d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"
                            /><polyline points="15 3 21 3 21 9" /><line
                                x1="10"
                                y1="14"
                                x2="21"
                                y2="3"
                            /></svg
                        >
                    </a>
                {:else}
                    <span class="text-base font-bold text-primary font-mono truncate"
                        >{getSourceLabel(t.source)}</span
                    >
                {/if}
            </div>
            <div
                class="bg-terminal-panel border border-border-dark rounded-lg p-3 flex flex-col min-w-0"
            >
                <span class="text-xs text-secondary font-mono uppercase mb-1"
                    >Location</span
                >
                <span class="text-sm text-primary font-sans truncate" title={t.location}>{t.location}</span>
            </div>
        </div>

        {@const hasCut = (detail.players_cut?.length ?? 0) > 0}
        {@const swissGroups = roundGroups.filter((g: RoundGroup) => g.type === 'swiss')}
        {@const cutGroups = roundGroups.filter((g: RoundGroup) => g.type === 'cut')}
        {@const hasCutMatches = cutGroups.length > 0}
        {@const isKnockoutCut = hasCutMatches && (() => {
            const firstCutRound = cutGroups[0]?.matches ?? [];
            if (firstCutRound.length <= 1) return true;
            // if first cut round has many matches and next rounds have fewer, it's knockout
            return cutGroups.every((g, idx) => idx === 0 || g.matches.length <= cutGroups[idx - 1].matches.length);
        })()}

        <!-- Swiss Section: matched-height standings + rounds -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start mb-6">
            <div class="flex flex-col">
                <!-- Swiss Standings (or fallback when no cut exists) -->
                {#if hasSwissTpl || (!hasCut && !hasCutMatches)}
                    <div bind:clientHeight={swissStandingsHeight} class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden">
                        <div class="bg-[rgba(255,255,255,0.02)] border-b border-border-dark p-3 flex items-center justify-between gap-3">
                            <h2 class="text-sm font-bold text-primary font-mono uppercase tracking-wider">SWISS STANDINGS</h2>
                            <div class="flex items-center gap-3">
                                {#if Math.ceil((detail.players_swiss?.length ?? 0) / STANDINGS_PER_PAGE) > 1}
                                    <span class="text-xs font-mono text-secondary">
                                        Page {swissPage + 1} / {Math.ceil((detail.players_swiss?.length ?? 0) / STANDINGS_PER_PAGE)}
                                    </span>
                                    <div class="flex items-center gap-1">
                                        <button
                                            class="p-1.5 rounded-md border border-border-dark text-primary hover:bg-[rgba(255,255,255,0.1)] transition-colors disabled:opacity-30 disabled:cursor-default"
                                            disabled={swissPage === 0}
                                            onclick={() => { if (swissPage > 0) swissPage--; }}
                                            aria-label="Previous page"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                                        </button>
                                        <button
                                            class="p-1.5 rounded-md border border-border-dark text-primary hover:bg-[rgba(255,255,255,0.1)] transition-colors disabled:opacity-30 disabled:cursor-default"
                                            disabled={swissPage >= Math.ceil((detail.players_swiss?.length ?? 0) / STANDINGS_PER_PAGE) - 1}
                                            onclick={() => swissPage++}
                                            aria-label="Next page"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                                        </button>
                                    </div>
                                {/if}
                            </div>
                        </div>
                        <div class="flex flex-col">
                            {#each (detail.players_swiss ?? []).slice(swissPage * STANDINGS_PER_PAGE, (swissPage + 1) * STANDINGS_PER_PAGE) as p}
                                <div class="flex items-center gap-3 p-3 border-b border-border-dark last:border-0 hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                                    <span class="w-8 h-8 rounded-full bg-[rgba(255,255,255,0.1)] flex items-center justify-center font-mono text-sm">{p.rank}</span>
                                    <FactionIcon faction={p.faction} size="md" />
                                    <div class="flex flex-col">
                                        <span class="font-mono text-primary font-medium">{p.name}</span>
                                        <span class="text-xs text-secondary font-mono">
                                            <span class="text-green-400 font-bold">{p.wins}W</span><span class="mx-0.5">-</span><span class="text-red-400 font-bold">{p.losses}L</span>{#if p.draws > 0}<span> - {p.draws}D</span>{/if}{#if p.event_points != null}<span class="mx-1.5 text-secondary/40">|</span><span title="Tournament Points">{p.event_points} TP</span>{/if}{#if p.tie_breaker_points != null}<span class="mx-1.5 text-secondary/40">·</span><span title={tieBreakerLabel(t.format)}>{p.tie_breaker_points} {t.format === "amg" || t.format === "xwa" ? "VP" : "TB"}</span>{/if}
                                        </span>
                                    </div>
                                    <div class="flex-1"></div>
                                    {#if p.list_id}
                                        <a href="/list/{p.list_id}" class="inline-flex items-center justify-center w-7 h-7 shrink-0 rounded-md border border-border-dark bg-[rgba(255,255,255,0.04)] text-secondary hover:text-primary hover:border-primary/30 hover:bg-white/5 transition-colors" title="View list" aria-label="View list">
                                            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
                                        </a>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>

            <!-- Matches: Swiss-only carousel — capped to standings height, never taller -->
            {#if swissGroups.length > 0}
                {@const swissIdx = Math.min(currentRoundIndex, swissGroups.length - 1)}
                {@const swissGroup = swissGroups[swissIdx]}
                {@const swissDom = dominantScenario(swissGroup.matches)}
                <div class="bg-terminal-panel border border-border-dark rounded-lg overflow-hidden flex flex-col" style="{swissStandingsHeight ? `max-height: ${swissStandingsHeight}px;` : ''}">
                    <div class="bg-[rgba(255,255,255,0.02)] border-b border-border-dark p-3 flex items-center justify-between gap-3 shrink-0">
                        <div class="flex flex-col min-w-0">
                            <h2 class="text-sm font-bold text-primary font-mono uppercase tracking-wider">{swissGroup.label}</h2>
                            {#if swissDom}
                                <span class="text-[11px] font-mono text-secondary uppercase tracking-wider truncate">{humanizeScenario(swissDom)}</span>
                            {/if}
                        </div>
                        <div class="flex items-center gap-3 shrink-0">
                            {#if swissGroups.length > 1}
                                <span class="text-xs font-mono text-secondary">
                                    Round {swissIdx + 1} / {swissGroups.length}
                                </span>
                                <div class="flex items-center gap-1">
                                    <button
                                        class="p-1.5 rounded-md border border-border-dark text-primary hover:bg-[rgba(255,255,255,0.1)] transition-colors disabled:opacity-30 disabled:cursor-default"
                                        disabled={swissIdx === 0}
                                        onclick={() => { if (currentRoundIndex > 0) currentRoundIndex--; }}
                                        aria-label="Previous round"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                                    </button>
                                    <button
                                        class="p-1.5 rounded-md border border-border-dark text-primary hover:bg-[rgba(255,255,255,0.1)] transition-colors disabled:opacity-30 disabled:cursor-default"
                                        disabled={swissIdx >= swissGroups.length - 1}
                                        onclick={() => { if (currentRoundIndex < swissGroups.length - 1) currentRoundIndex++; }}
                                        aria-label="Next round"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                                    </button>
                                </div>
                            {/if}
                        </div>
                    </div>
                    <div class="flex flex-col divide-y divide-border-dark/50 overflow-y-auto p-2">
                        {#each swissGroup.matches as m}
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
                    {#if swissGroups.length > 1}
                        <div class="flex items-center justify-center gap-1.5 p-2 border-t border-border-dark shrink-0 overflow-x-auto">
                            {#each swissGroups as rg, i}
                                <button class="px-2 py-0.5 text-[11px] font-mono rounded transition-colors {i === swissIdx ? 'bg-primary/20 text-primary border border-primary/30' : 'text-secondary hover:text-primary hover:bg-[rgba(255,255,255,0.05)]'}" onclick={() => currentRoundIndex = i}>{rg.shortLabel}</button>
                            {/each}
                        </div>
                    {/if}
                </div>
            {/if}
        </div>

        <!-- Playoff Bracket (single-elimination cut) — below Swiss; non-knockout cuts fall back to tabular rounds -->
        {#if hasCutMatches}
            <div class="mb-8">
                <div class="bg-terminal-panel border border-border-dark rounded-xl p-4 md:p-6 shadow-xl">
                    <div class="flex items-center gap-3 border-b border-border-dark pb-4 mb-6">
                        <div class="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
                            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
                                <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
                                <path d="M4 22h16"></path>
                                <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path>
                                <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path>
                                <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>
                            </svg>
                        </div>
                        <div>
                            <h2 class="text-lg font-bold text-primary font-mono tracking-wide uppercase">Knockout Phase</h2>
                        </div>
                    </div>
                    {#if isKnockoutCut}
                        <BracketView matches={detail.matches ?? []} {playerMap} />
                    {:else}
                        <!-- Cut is not single-elimination (e.g. secondary Swiss); fall back to tabular cut rounds -->
                        <div class="flex flex-col gap-4">
                            {#each cutGroups as group}
                                <div class="border border-border-dark/60 rounded-lg overflow-hidden bg-[#090d16]">
                                    <div class="bg-[rgba(255,255,255,0.03)] border-b border-border-dark/60 p-3 flex items-center justify-between">
                                        <span class="font-mono text-sm font-bold text-amber-300 uppercase tracking-wider">{group.label}</span>
                                        <span class="text-xs font-mono text-secondary">{group.matches.length} Match{group.matches.length === 1 ? '' : 'es'}</span>
                                    </div>
                                    <div class="divide-y divide-border-dark/40">
                                        {#each group.matches as m}
                                            {@const winnerName = pickWinnerName(m)}
                                            <div class="flex items-center justify-between gap-4 p-3 hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                                                <span class="font-mono text-sm flex-1 truncate text-right {winnerName === m.player1 ? 'text-green-400 font-bold' : winnerName === null ? 'text-secondary' : 'text-primary'}" title={m.player1}>{m.player1}</span>
                                                <div class="flex items-center justify-center gap-1.5 font-mono text-sm px-3 py-1 rounded bg-[rgba(255,255,255,0.04)] border border-border-dark shrink-0 font-bold">
                                                    <span class={winnerName === m.player1 ? 'text-green-400' : 'text-secondary'}>{m.score1}</span><span class="text-secondary/60">-</span><span class={winnerName === m.player2 ? 'text-green-400' : 'text-secondary'}>{m.score2}</span>
                                                </div>
                                                <span class="font-mono text-sm flex-1 truncate text-left {winnerName === m.player2 ? 'text-green-400 font-bold' : winnerName === null ? 'text-secondary' : 'text-primary'}" title={m.player2}>{m.player2}</span>
                                            </div>
                                        {/each}
                                    </div>
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>
        {/if}
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
    {:catch error}
        <div class="py-12">
            <ErrorPanel message={error?.message || "Failed to load tournament detail"} onRetry={retry} />
        </div>
    {/await}
</div>
