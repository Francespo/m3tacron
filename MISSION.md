# Mission: FactionStat Refactor & Meta-Diversity Analytics

## Intent
The primary goal of this task is to evolve the `FactionStat` data structure from a heavy, redundant metadata container into a lean, analytics-focused schema. We want to separate **static metadata** (labels, icons) from **dynamic statistics** (wins, list counts) and introduce new metrics to measure meta-diversity.

## Rationale

### 1. Separation of Concerns (Logic vs. Presentation)
Currently, the backend calculates and sends strings like `name` ("Rebel Alliance") and `icon_char` ("!").
- **Why it's a problem:** These are static constants. If we want to change a faction color or icon, we shouldn't have to touch the backend analytics logic.
- **The Fix:** Move metadata lookup to the frontend. The backend only sends the `xws` identifier (the "source of truth").

### 2. Payload Optimization
By removing redundant strings and pre-calculated win rates from every faction entry, we reduce the API response size. While small for factions, this pattern is critical as the codebase scales to ships, pilots, and upgrades.

### 3. Introducing Meta-Diversity Metrics
`popularity` (renamed to `lists`) tells us how many people are playing a faction. But it doesn't tell us *how* they are playing.
- **New Metric: `different_lists`**: This counts unique list signatures.
- **The Value:** Comparison between `lists` and `different_lists` reveals meta health. 
    - *High Lists / Low Different Lists:* The faction is popular but "solved" or "stale" (everyone plays the same thing).
    - *High Lists / High Different Lists:* The faction is popular and "diverse" (multiple viable archetypes).

### 4. Logic Unification (List Signatures)
We currently have disparate ways of identifying a "squadron". We need a single, unified `calculate_list_signature` function that ensures a list is bucketed correctly whether we are looking at faction stats or individual list performance.

## Goals

1. **Schema Pruning:** Update `backend/api/schemas.py` to keep only `xws`, `wins`, `games`, `lists`, and `different_lists`.
2. **Signature Utility:** Implement a robust `calculate_list_signature(xws_dict)` in `backend/utils/squadron.py`.
3. **Analytics Update:**
    - Update `aggregate_faction_stats` in `backend/analytics/factions.py` to use the new signature for `different_lists` counting.
    - Ensure `lists` reflects the total count of squads.
4. **Frontend Integration:**
    - Calculate `win_rate` dynamically in `+page.svelte`.
    - Map `xws` to labels and icons using `$lib/data/factions.ts`.

## Context Links
- Issue: Closes #86
- Discussion: Initiated to clean up `MetaSnapshotResponse`.
