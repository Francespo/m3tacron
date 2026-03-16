# Task List - Issue 86: Faction Consolidation

- [x] Research existing `Faction` usage and dependencies
- [x] Identify non-obsolete files in `backend/data_structures`
- [x] Revise implementation plan based on user feedback (No model changes, keep `Faction` location)
- [x] Consolidated Faction Logic Implementation (XWS-Only API)
    - [x] Strengthen `from_xws` in `factions.py` to normalize all inputs
    - [x] Remove label/UI logic from backend `factions.py` and `formatters.py`
    - [x] Update `analytics/factions.py` to use XWS identifiers
    - [/] Ensure frontend components use `factions.ts` for all mapping
    - [ ] Sync `frontend/src/lib/data/factions.ts` with official XWS IDs
- [ ] Verification
    - [ ] Validate analytics consistency
    - [ ] Validate API human-readable output
 X
