# Refactor FactionStat Schema and Analytics

This plan refactors the `FactionStat` schema to be more minimal, moving metadata logic to the frontend and adding `different_lists` to track unique squadron signatures.

## Proposed Changes

### Backend Analytics & Utils

#### [MODIFY] [squadron.py](file:///c:/Users/franc/Documents/m3tacron/backend/utils/squadron.py)
- Implement `calculate_list_signature` function for reuse in analytics.

#### [MODIFY] [factions.py](file:///c:/Users/franc/Documents/m3tacron/backend/analytics/factions.py)
- Update `aggregate_faction_stats` to calculate `different_lists` (count of unique list signatures).
- Rename `popularity` to `lists`.
- Remove redundant metadata calculation (`name`, `icon_char`, `win_rate`).

#### [MODIFY] [lists.py](file:///c:/Users/franc/Documents/m3tacron/backend/analytics/lists.py)
- Use `calculate_list_signature` from `backend.utils.squadron`.

### Backend API

#### [MODIFY] [schemas.py](file:///c:/Users/franc/Documents/m3tacron/backend/api/schemas.py)
- Update `FactionStat` schema fields: `xws`, `wins`, `games`, `lists`, `different_lists`.

### Frontend UI

#### [MODIFY] [+page.svelte](file:///c:/Users/franc/Documents/m3tacron/frontend/src/routes/+page.svelte)
- Implement client-side `win_rate` calculation.
- Use `$lib/data/factions.ts` for faction labels and icons.

## Verification Plan

### Automated Tests
- Run `pytest` to ensure backend analytics correctness.
- Validate `different_lists` logic with test cases.

### Manual Verification
- Verify homepage charts (Bar and Pie) display correctly.
