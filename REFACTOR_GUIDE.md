# ListData Refactor Guide (Issue #90)

## Objective
Refactor `ListData` to minimize API payload. The goal is to remove fields that the frontend can derive (names, icons, win_rates) while keeping the unique `signature` and IDs needed for full XWS reconstruction.

## Key Constraints
- **PilotData Independence**: DO NOT remove `faction_xws` from `PilotData`. Each pilot must know its faction.
- **ListData Minimal Schema**:
    - **KEEP**: `name`, `signature`, `faction_xws`, `wins`, `games`, `points`, `original_points`, `total_loadout`, `pilots`.
    - **REMOVE**: Ridiculous fields like `faction` (label), `icon_char`, `win_rate` (calculate on FE), `faction_key`.
- **YASB Export**: The frontend must be able to rebuild a complete XWS JSON from the `ListData` structure.

## Technical Tasks
1. **Schemas**: Update `backend/api/schemas.py`.
2. **Aggregation**: Update `backend/analytics/lists.py` to use `get_list_signature` from `backend/utils/squadron.py` for grouping.
3. **Formatters**: Update `backend/api/formatters.py` to match the new schema.
4. **Frontend**:
    - Update the UI to lookup faction metadata from `$lib/data/factions.ts` using `faction_xws`.
    - Implement the "Recostruct XWS" utility for export/import.

## Verification
- Run `npm run dev` in the new worktree.
- Verify that the Dashboard still shows correct data and icons.
- Verify XWS export functionality.
