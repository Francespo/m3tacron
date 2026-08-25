<script lang="ts">
    import FactionIcon from "$lib/components/FactionIcon.svelte";

    export type Match = {
        round: number;
        type?: string | null;
        scenario?: string | null;
        player1: string;
        player2: string;
        score1: number;
        score2: number;
        winner_id?: number | string | null;
    };

    let {
        matches = [],
        playerMap = new Map<string, any>(),
    }: {
        matches: Match[];
        playerMap: Map<string, any>;
    } = $props();

    const COL_WIDTH = 220;
    const COL_GAP = 54;
    const COL_STEP = COL_WIDTH + COL_GAP;
    const CARD_HEIGHT = 76;
    const GAP_ROUND_0 = 20;
    const STEP_0 = CARD_HEIGHT + GAP_ROUND_0; // 96px
    const HEADER_HEIGHT = 44;

    function pickWinnerNameExt(m: Match | null, pMap: Map<string, any>): string | null {
        if (!m) return null;
        if ((m.player2 || "").trim().toLowerCase() === "bye") return m.player1;
        if ((m.player1 || "").trim().toLowerCase() === "bye") return m.player2;
        if (m.winner_id !== undefined && m.winner_id !== null) {
            const p1 = pMap.get(m.player1.trim().toLowerCase());
            const p2 = pMap.get(m.player2.trim().toLowerCase());
            if (p1 && String(p1.id) === String(m.winner_id)) return m.player1;
            if (p2 && String(p2.id) === String(m.winner_id)) return m.player2;
        }
        if (m.score1 > m.score2) return m.player1;
        if (m.score2 > m.score1) return m.player2;
        return null;
    }

    // Filter cut matches and build binary tree structure
    const bracketTreeData = $derived.by(() => {
        const cutMatches = matches.filter(
            (m) => (m.type || "").toLowerCase().trim() === "cut"
        );
        if (cutMatches.length === 0) return { rounds: [], roundKeys: [], canvasHeight: 400 };

        const roundMap = new Map<number, Match[]>();
        for (const m of cutMatches) {
            if (!roundMap.has(m.round)) {
                roundMap.set(m.round, []);
            }
            roundMap.get(m.round)!.push(m);
        }

        // Sort rounds by match count descending (earliest round has most matches)
        const sortedRoundKeys = Array.from(roundMap.keys()).sort((a, b) => {
            return roundMap.get(b)!.length - roundMap.get(a)!.length;
        });

        const K = sortedRoundKeys.length;
        const orderedRounds: (Match | null)[][] = Array.from({ length: K }, () => []);

        // Final round (index K-1)
        const finalRoundKey = sortedRoundKeys[K - 1];
        const finalMatches = roundMap.get(finalRoundKey) || [];
        orderedRounds[K - 1] = [finalMatches[0] || null];

        // Work backwards from K-2 down to 0
        for (let c = K - 2; c >= 0; c--) {
            const roundKey = sortedRoundKeys[c];
            const availableMatches = [...(roundMap.get(roundKey) || [])];
            const parentRound = orderedRounds[c + 1];

            const numExpectedMatches = parentRound.length * 2;
            const currentRoundOrdered: (Match | null)[] = Array.from(
                { length: numExpectedMatches },
                () => null
            );

            for (let j = 0; j < parentRound.length; j++) {
                const parentMatch = parentRound[j];
                if (!parentMatch) continue;

                const p1 = parentMatch.player1;
                const p2 = parentMatch.player2;

                let feeder1Idx = -1;
                if (p1 && p1.toLowerCase() !== "bye") {
                    feeder1Idx = availableMatches.findIndex((m) => {
                        const w = pickWinnerNameExt(m, playerMap);
                        return (
                            (w && w.toLowerCase() === p1.toLowerCase()) ||
                            (m.player1 && m.player1.toLowerCase() === p1.toLowerCase()) ||
                            (m.player2 && m.player2.toLowerCase() === p1.toLowerCase())
                        );
                    });
                }
                if (feeder1Idx !== -1) {
                    currentRoundOrdered[2 * j] = availableMatches[feeder1Idx];
                    availableMatches.splice(feeder1Idx, 1);
                }

                let feeder2Idx = -1;
                if (p2 && p2.toLowerCase() !== "bye") {
                    feeder2Idx = availableMatches.findIndex((m) => {
                        const w = pickWinnerNameExt(m, playerMap);
                        return (
                            (w && w.toLowerCase() === p2.toLowerCase()) ||
                            (m.player1 && m.player1.toLowerCase() === p1.toLowerCase()) ||
                            (m.player2 && m.player2.toLowerCase() === p1.toLowerCase())
                        );
                    });
                }
                if (feeder2Idx !== -1) {
                    currentRoundOrdered[2 * j + 1] = availableMatches[feeder2Idx];
                    availableMatches.splice(feeder2Idx, 1);
                }
            }

            // Fill remaining matches if any
            let emptyIdx = 0;
            for (const m of availableMatches) {
                while (emptyIdx < currentRoundOrdered.length && currentRoundOrdered[emptyIdx] !== null) {
                    emptyIdx++;
                }
                if (emptyIdx < currentRoundOrdered.length) {
                    currentRoundOrdered[emptyIdx] = m;
                } else {
                    currentRoundOrdered.push(m);
                }
            }

            orderedRounds[c] = currentRoundOrdered;
        }

        const numRound0Matches = Math.max(orderedRounds[0]?.length || 1, 1);
        const canvasHeight = numRound0Matches * STEP_0;

        return {
            rounds: orderedRounds,
            roundKeys: sortedRoundKeys,
            canvasHeight
        };
    });

    // Helper to compute Center Y coordinate of match (c, i)
    function getY(c: number, i: number, rounds: (Match | null)[][]): number {
        if (c === 0) {
            return GAP_ROUND_0 / 2 + CARD_HEIGHT / 2 + i * STEP_0;
        }
        const prevUpperY = getY(c - 1, 2 * i, rounds);
        const prevLowerY = getY(c - 1, 2 * i + 1, rounds);
        return (prevUpperY + prevLowerY) / 2;
    }

    function getColumnHeader(matchesCount: number, colIndex: number, totalCols: number): string {
        const distFromEnd = totalCols - 1 - colIndex;
        if (distFromEnd === 0) return "Finals";
        if (distFromEnd === 1) return "Semi-Finals";
        if (distFromEnd === 2) return "Quarter-Finals";
        if (distFromEnd === 3) return "Round of 16";
        if (distFromEnd === 4) return "Round of 32";
        if (distFromEnd === 5) return "Round of 64";
        if (distFromEnd === 6) return "Round of 128";
        return `Round ${colIndex + 1}`;
    }

    const championName = $derived.by(() => {
        const rounds = bracketTreeData.rounds;
        if (rounds.length === 0) return null;
        const finalsMatch = rounds[rounds.length - 1]?.[0];
        if (finalsMatch) {
            const w = pickWinnerNameExt(finalsMatch, playerMap);
            if (w) return w;
        }
        if (playerMap) {
            for (const [_, p] of playerMap.entries()) {
                if (p.rank === 1 || p.cut_rank === 1) {
                    return p.name;
                }
            }
        }
        return null;
    });

    // --- Drag-to-pan (hand tool) state ---
    let isDragging = $state(false);
    let dragStartX = $state(0);
    let dragStartY = $state(0);
    let dragScrollLeft = $state(0);
    let dragScrollTop = $state(0);
    let bracketEl: HTMLDivElement | null = $state(null);

    let hasDragged = $state(false);

    function onPointerDown(e: PointerEvent) {
        if (!bracketEl) return;
        // Don't hijack clicks on interactive elements (list links, etc.)
        if ((e.target as HTMLElement)?.closest?.("a, button")) return;
        isDragging = true;
        hasDragged = false;
        bracketEl.setPointerCapture(e.pointerId);
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        dragScrollLeft = bracketEl.scrollLeft;
        dragScrollTop = bracketEl.scrollTop;
        bracketEl.style.cursor = "grabbing";
        bracketEl.style.userSelect = "none";
    }

    function onPointerMove(e: PointerEvent) {
        if (!isDragging || !bracketEl) return;
        const dx = e.clientX - dragStartX;
        const dy = e.clientY - dragStartY;
        if (Math.abs(dx) > 3 || Math.abs(dy) > 3) hasDragged = true;
        bracketEl.scrollLeft = dragScrollLeft - dx;
        bracketEl.scrollTop = dragScrollTop - dy;
    }

    function onPointerUp(e: PointerEvent) {
        if (!bracketEl) return;
        isDragging = false;
        try { bracketEl.releasePointerCapture(e.pointerId); } catch {}
        bracketEl.style.cursor = "grab";
        bracketEl.style.userSelect = "";
        // Prevent click after a drag gesture
        if (hasDragged) {
            e.preventDefault();
            // delay reset so the next click is suppressed
            setTimeout(() => (hasDragged = false), 0);
        }
    }

    function onBracketClick(e: MouseEvent) {
        if (hasDragged) {
            e.preventDefault();
            e.stopPropagation();
        }
    }


</script>

<div class="flex flex-col w-full">
    <!-- Draggable Bracket Map Container (hand-tool panning, no scrollbars) -->
    <div
        bind:this={bracketEl}
        id="bracket-scroll-container"
        class="bracket-scroll w-full overflow-auto max-h-[750px] border border-border-dark rounded-xl bg-terminal-panel p-4 relative select-none"
        style="cursor: grab; scrollbar-width: none;"
        onclickcapture={onBracketClick}
        onpointerdown={onPointerDown}
        onpointermove={onPointerMove}
        onpointerup={onPointerUp}
        onpointerleave={onPointerUp}
        role="region"
        aria-label="Knockout bracket map — drag to pan"

    >
        {#if bracketTreeData.rounds.length === 0}
            <div class="py-12 text-center text-secondary font-mono text-sm">
                No cut matches recorded for this tournament.
            </div>
        {:else}
            {@const K = bracketTreeData.rounds.length}
            {@const totalWidth = (K + 1) * COL_STEP - COL_GAP}
            {@const totalHeight = bracketTreeData.canvasHeight + HEADER_HEIGHT + 20}

            <div
                class="relative"
                style="width: {totalWidth}px; height: {totalHeight}px;"
            >
                <!-- 1. Column Headers -->
                {#each Array.from({ length: K }) as _, c}
                    {@const label = getColumnHeader(bracketTreeData.rounds[c].length, c, K)}
                    <div
                        class="absolute top-0 flex items-center justify-between px-3 py-2 bg-terminal-panel/90 border border-border-dark rounded-md text-xs font-mono font-bold uppercase tracking-wider text-primary shadow-sm"
                        style="left: {c * COL_STEP}px; width: {COL_WIDTH}px; height: {HEADER_HEIGHT - 8}px;"
                    >
                        <span>{label}</span>
                        <span class="text-[10px] text-secondary font-normal">
                            {bracketTreeData.rounds[c].filter(Boolean).length} match{bracketTreeData.rounds[c].filter(Boolean).length === 1 ? '' : 'es'}
                        </span>
                    </div>
                {/each}

                <!-- Champion Header -->
                <div
                    class="absolute top-0 flex items-center justify-center px-3 py-2 bg-green-500/10 border border-green-500/30 rounded-md text-xs font-mono font-bold uppercase tracking-wider text-green-400 shadow-sm"
                    style="left: {K * COL_STEP}px; width: {COL_WIDTH}px; height: {HEADER_HEIGHT - 8}px;"
                >
                    Champion
                </div>

                <!-- 2. SVG Connector Lines Layer -->
                <svg
                    class="absolute pointer-events-none"
                    style="top: {HEADER_HEIGHT}px; left: 0; width: {totalWidth}px; height: {bracketTreeData.canvasHeight}px;"
                >
                    <defs>
                        <filter id="green-glow" x="-20%" y="-20%" width="140%" height="140%">
                            <feGaussianBlur stdDeviation="2" result="blur" />
                            <feComposite in="SourceGraphic" in2="blur" operator="over" />
                        </filter>
                    </defs>

                    {#each Array.from({ length: K - 1 }) as _, c}
                        {@const roundMatches = bracketTreeData.rounds[c]}
                        {@const nextRoundMatches = bracketTreeData.rounds[c + 1]}

                        {#each nextRoundMatches as nextMatch, i}
                            {#if nextMatch !== undefined}
                                {@const targetY = getY(c + 1, i, bracketTreeData.rounds)}
                                {@const targetX = (c + 1) * COL_STEP}
                                {@const feeder1 = roundMatches[2 * i]}
                                {@const feeder2 = roundMatches[2 * i + 1]}
                                {@const midX = c * COL_STEP + COL_WIDTH + COL_GAP / 2}

                                {#if feeder1}
                                    {@const y1 = getY(c, 2 * i, bracketTreeData.rounds)}
                                    {@const x1 = c * COL_STEP + COL_WIDTH}
                                    {@const w1 = pickWinnerNameExt(feeder1, playerMap)}
                                    {@const isFeeder1Active = w1 && (w1.toLowerCase() === nextMatch?.player1?.toLowerCase() || w1.toLowerCase() === nextMatch?.player2?.toLowerCase())}
                                    {@const d1 = `M ${x1} ${y1} H ${midX} V ${targetY} H ${targetX}`}
                                    
                                    {#if isFeeder1Active}
                                        <path
                                            d={d1}
                                            stroke="#4ade80"
                                            stroke-width="2.5"
                                            fill="none"
                                            filter="url(#green-glow)"
                                        />
                                    {:else}
                                        <path
                                            d={d1}
                                            stroke="rgba(255, 255, 255, 0.12)"
                                            stroke-width="1.5"
                                            fill="none"
                                        />
                                    {/if}
                                {/if}

                                {#if feeder2}
                                    {@const y2 = getY(c, 2 * i + 1, bracketTreeData.rounds)}
                                    {@const x2 = c * COL_STEP + COL_WIDTH}
                                    {@const w2 = pickWinnerNameExt(feeder2, playerMap)}
                                    {@const isFeeder2Active = w2 && (w2.toLowerCase() === nextMatch?.player1?.toLowerCase() || w2.toLowerCase() === nextMatch?.player2?.toLowerCase())}
                                    {@const d2 = `M ${x2} ${y2} H ${midX} V ${targetY} H ${targetX}`}
                                    
                                    {#if isFeeder2Active}
                                        <path
                                            d={d2}
                                            stroke="#4ade80"
                                            stroke-width="2.5"
                                            fill="none"
                                            filter="url(#green-glow)"
                                        />
                                    {:else}
                                        <path
                                            d={d2}
                                            stroke="rgba(255, 255, 255, 0.12)"
                                            stroke-width="1.5"
                                            fill="none"
                                        />
                                    {/if}
                                {/if}
                            {/if}
                        {/each}
                    {/each}

                    <!-- Final connector to Champion box -->
                    {#if K > 0}
                        {@const finalsMatch = bracketTreeData.rounds[K - 1]?.[0]}
                        {@const finalsY = getY(K - 1, 0, bracketTreeData.rounds)}
                        {@const finalsX = (K - 1) * COL_STEP + COL_WIDTH}
                        {@const champX = K * COL_STEP}
                        {@const finalWinner = finalsMatch ? pickWinnerNameExt(finalsMatch, playerMap) : null}

                        <path
                            d="M {finalsX} {finalsY} H {champX}"
                            stroke={finalWinner ? "#4ade80" : "rgba(255, 255, 255, 0.12)"}
                            stroke-width={finalWinner ? "2.5" : "1.5"}
                            fill="none"
                            filter={finalWinner ? "url(#green-glow)" : undefined}
                        />
                    {/if}
                </svg>

                <!-- 3. Match Cards Layer -->
                {#each bracketTreeData.rounds as roundList, c}
                    {#each roundList as m, i}
                        {@const centerY = getY(c, i, bracketTreeData.rounds)}
                        {@const top = HEADER_HEIGHT + centerY - CARD_HEIGHT / 2}
                        {@const left = c * COL_STEP}

                        {#if m}
                            {@const winnerName = pickWinnerNameExt(m, playerMap)}
                            {@const p1Winner = winnerName !== null && winnerName.toLowerCase() === m.player1.toLowerCase()}
                            {@const p2Winner = winnerName !== null && winnerName.toLowerCase() === m.player2.toLowerCase()}
                            {@const p1Info = playerMap.get(m.player1.trim().toLowerCase())}
                            {@const p2Info = playerMap.get(m.player2.trim().toLowerCase())}

                            <div
                                class="absolute flex flex-col justify-between bg-terminal-panel border rounded-lg overflow-hidden shadow-lg {p1Winner || p2Winner ? 'border-border-dark' : 'border-border-dark/60'}"
                                style="left: {left}px; top: {top}px; width: {COL_WIDTH}px; height: {CARD_HEIGHT}px;"
                            >
                                <!-- Player 1 Row -->
                                <div class="flex items-center justify-between px-2.5 py-1.5 h-1/2 relative min-w-0 {p1Winner ? 'bg-green-500/10' : ''}">
                                    {#if p1Winner}
                                        <div class="absolute left-0 top-0 bottom-0 w-[3px] bg-green-400"></div>
                                    {/if}
                                    <div class="flex items-center gap-1.5 min-w-0 flex-1 pr-1">
                                        {#if p1Info?.faction}
                                            <FactionIcon faction={p1Info.faction} size="xs" />
                                        {/if}
                                        <span class="font-mono text-xs truncate max-w-[125px] {p1Winner ? 'text-green-400 font-bold' : p2Winner ? 'text-secondary/70' : 'text-primary'}" title={m.player1}>
                                            {m.player1}
                                        </span>
                                        {#if p1Info?.list_id}
                                            <a href="/list/{p1Info.list_id}" class="inline-flex items-center justify-center w-6 h-6 shrink-0 rounded-md border border-border-dark bg-[rgba(255,255,255,0.03)] text-secondary hover:text-primary hover:border-primary/30 hover:bg-white/5 transition-colors ml-0.5" title="View list" aria-label="View list">
                                                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
                                            </a>
                                        {/if}
                                    </div>
                                    <div class="font-mono text-xs shrink-0 pl-1">
                                        <span class={p1Winner ? 'text-green-400 font-bold bg-green-500/20 px-1.5 py-0.5 rounded border border-green-500/30' : p2Winner ? 'text-secondary/60' : 'text-primary font-semibold'}>
                                            {m.score1}
                                        </span>
                                    </div>
                                </div>

                                <div class="border-t border-border-dark/50"></div>

                                <!-- Player 2 Row -->
                                <div class="flex items-center justify-between px-2.5 py-1.5 h-1/2 relative min-w-0 {p2Winner ? 'bg-green-500/10' : ''}">
                                    {#if p2Winner}
                                        <div class="absolute left-0 top-0 bottom-0 w-[3px] bg-green-400"></div>
                                    {/if}
                                    <div class="flex items-center gap-1.5 min-w-0 flex-1 pr-1">
                                        {#if p2Info?.faction}
                                            <FactionIcon faction={p2Info.faction} size="xs" />
                                        {/if}
                                        <span class="font-mono text-xs truncate max-w-[125px] {p2Winner ? 'text-green-400 font-bold' : p1Winner ? 'text-secondary/70' : 'text-primary'}" title={m.player2}>
                                            {m.player2}
                                        </span>
                                        {#if p2Info?.list_id}
                                            <a href="/list/{p2Info.list_id}" class="inline-flex items-center justify-center w-6 h-6 shrink-0 rounded-md border border-border-dark bg-[rgba(255,255,255,0.03)] text-secondary hover:text-primary hover:border-primary/30 hover:bg-white/5 transition-colors ml-0.5" title="View list" aria-label="View list">
                                                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
                                            </a>
                                        {/if}
                                    </div>
                                    <div class="font-mono text-xs shrink-0 pl-1">
                                        <span class={p2Winner ? 'text-green-400 font-bold bg-green-500/20 px-1.5 py-0.5 rounded border border-green-500/30' : p1Winner ? 'text-secondary/60' : 'text-primary font-semibold'}>
                                            {m.score2}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        {:else}
                            <!-- Placeholder / BYE slot -->
                            <div
                                class="absolute flex flex-col justify-center items-center bg-terminal-panel/20 border border-dashed border-border-dark/40 rounded-lg overflow-hidden"
                                style="left: {left}px; top: {top}px; width: {COL_WIDTH}px; height: {CARD_HEIGHT}px;"
                            >
                                <span class="font-mono text-[10px] text-secondary/50 uppercase tracking-widest font-semibold">BYE / TBD</span>
                            </div>
                        {/if}
                    {/each}
                {/each}

                <!-- 4. Champion Card Layer (trophy / victory yellow) -->
                {#if championName}
                    {@const champInfo = playerMap.get(championName.toLowerCase())}
                    {@const finalsY = getY(K - 1, 0, bracketTreeData.rounds)}
                    {@const champTop = HEADER_HEIGHT + finalsY - 45}

                    <div
                        class="absolute flex flex-col items-center justify-center bg-gradient-to-b from-[#2a2410] to-[#121008] border-2 border-amber-400/60 rounded-xl p-3 text-center shadow-[0_0_25px_rgba(251,191,36,0.28)]"
                        style="left: {K * COL_STEP}px; top: {champTop}px; width: {COL_WIDTH}px; height: 90px;"
                    >
                        <div class="flex items-center gap-1.5 text-amber-400 mb-1">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
                                <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
                                <path d="M4 22h16"></path>
                                <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path>
                                <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path>
                                <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>
                            </svg>
                            <span class="font-mono text-[10px] uppercase tracking-widest font-extrabold text-amber-300">CHAMPION</span>
                        </div>
                        <div class="flex items-center gap-2 min-w-0 justify-center">
                            {#if champInfo?.faction}
                                <FactionIcon faction={champInfo.faction} size="sm" />
                            {/if}
                            <span class="font-mono text-sm font-bold text-amber-200 truncate max-w-[130px]" title={championName}>
                                {championName}
                            </span>
                        </div>
                        {#if champInfo?.list_id}
                            <a
                                href="/list/{champInfo.list_id}"
                                class="mt-1.5 inline-flex items-center justify-center w-7 h-7 rounded-md border border-amber-400/40 bg-amber-500/10 hover:bg-amber-500/20 text-amber-200 hover:text-amber-100 transition-colors"
                                aria-label="View list"
                                title="View list"
                            >
                                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
                            </a>
                        {/if}
                    </div>
                {/if}
            </div>
        {/if}
    </div>
</div>

<style>
    /* Draggable map: hide native scrollbars, keep scrolling via pointer drag + wheel */
    .bracket-scroll::-webkit-scrollbar {
        display: none;
    }
    .bracket-scroll {
        -ms-overflow-style: none;
        scrollbar-width: none;
    }
    .bracket-scroll:active {
        cursor: grabbing !important;
    }
</style>
