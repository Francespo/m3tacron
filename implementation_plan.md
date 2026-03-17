# Refactor Backend to Remove Presentation Metadata

This plan refactors the backend to remove all presentation-related metadata (`icon_char`, labels, names) from API schemas, analytics, and utility Enums, moving these concerns entirely to the frontend.

## Proposed Changes

### [Component Name] backend/data_structures

#### [MODIFY] [factions.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/data_structures/factions.py)
- **Delete** `get_faction_char` (if present) and remove it from exports/imports.
- **Ensure** `.label` property is removed from any related structures.

#### [MODIFY] [Enums in data_structures/](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/data_structures/)
- **Remove** `@property def label(self)` from the following files:
    - [formats.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/data_structures/formats.py)
    - [platforms.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/data_structures/platforms.py)
    - [upgrade_types.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/data_structures/upgrade_types.py)
    - [scenarios.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/data_structures/scenarios.py)
    - [round_types.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/data_structures/round_types.py)
    - [sorting_order.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/data_structures/sorting_order.py)
    - [data_source.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/data_structures/data_source.py)

### [Component Name] backend/api

#### [MODIFY] [schemas.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/api/schemas.py)
- **Remove** `icon_char: str`, `name: str`, `faction: str`, `faction_key: str` from `ListData`.
- **Remove** `format_label`, `platform_label` from `TournamentRow`.
- **Ensure** all schemas only pass XWS/Value identifiers.

#### [MODIFY] [formatters.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/api/formatters.py)
- **Remove** logic mapping to presentation fields in `enrich_list_data`.

### [Component Name] backend/analytics

#### [MODIFY] [core.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/analytics/core.py), [ships.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/analytics/ships.py), [lists.py](file:///c:/Users/franc/Documents/m3tacron-issue-86/backend/analytics/lists.py)
- **Strip** all calls to `get_faction_char`.
- **Remove** presentation fields (`name`, `icon_char`, `ship_name`, etc.) from aggregated result dictionaries.

## Verification Plan

### Automated Tests
- Run `pytest` to catch any regressions in logic that relied on `.label`.
- Verify API responses (`/api/meta/snapshot`) via `curl` or browser to ensure no presentation fields are leaked.

### Manual Verification
- Verify the frontend (once updated) correctly maps XWS IDs to labels and icons using its own internal data.
