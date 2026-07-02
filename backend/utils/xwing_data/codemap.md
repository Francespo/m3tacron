# backend/utils/xwing_data/

## Responsibility
Thin Python wrapper over the vendored `external_data/xwing-data2` and `external_data/xwing-data2-legacy` JSON datasets, providing canonical lookups for X-Wing Miniatures game entities (factions, ships, pilots, upgrades). It exists so the rest of the backend never touches raw JSON or XWS IDs directly.

## Design
- **Source switching via `DataSource` enum** (`XWA` default, `LEGACY`): every loader accepts a `source: DataSource` and resolves it to a directory through `core.get_data_dir`.
- **Cached bulk loaders** in `core.py`, `pilots.py`, `ships.py`, `upgrades.py` use `@lru_cache(maxsize=4)` so each (XWA/Legacy) dataset is parsed at most once per process.
- **Loaders return `dict[xws_id -> entity_dict]`** — flat lookup tables keyed by the stable XWS identifier, with human-readable fields denormalized (ship name/icon/stats lifted out of nested `ship` blocks; slot category inferred from JSON filename in `upgrades.py`).
- **Scenario pilot patches** in `pilots.load_all_pilots` backfill missing entries like `longshot-evacuationofdqar` and `fennrau-armedanddangerous` that the upstream dataset omits.
- **Format flags** (`standard/extended/wildspace/epic`) and **ship combat stats** (hull/shields/agility/attack) are flattened onto pilot dicts to support filtering and analytics.
- **Parser layer** (`parser.py`) composes the lookups into a single rich `parse_xws(xws_dict)` call that hydrates a raw XWS roster into readable names; `normalize_faction` routes through `data_structures.factions.Faction.from_xws`.
- **Icon helper** `get_ship_icon_name` mirrors the frontend `components/icons.py` slug logic for backend string assembly.

## Flow
1. Caller imports from a submodule (e.g. `from ..utils.xwing_data.pilots import get_pilot_info`).
2. Lookup helper calls the corresponding `load_all_*` function, which on first call reads `external_data/xwing-data2/data/{pilots|upgrades}/...` JSON via `get_data_dir` and caches the aggregated dict.
3. Helper returns the canonical entity dict (or a derived string like name/icon/slot).
4. For roster hydration, `parse_xws` walks the XWS JSON, calling `normalize_faction` → `get_faction_name`, then `get_pilot_info` per pilot and `get_upgrade_name` per upgrade, producing a denormalized summary.

## Integration
- **Consumed by**:
  - `backend/api/formatters.py` — `get_pilot_info`, `get_upgrade_info`, `get_upgrade_slot`, `get_ship_icon_name` (enrichment seam for list/ship/squadron detail responses).
  - `backend/api/ships.py`, `backend/api/ship_detail.py`, `backend/api/squadrons.py`, `backend/api/pilot_detail.py` — `load_all_ships`, `load_all_pilots`, `load_all_upgrades` for filtered/detail endpoints.
  - `backend/api/tournaments.py` — `parser.normalize_faction` to canonicalize raw faction strings.
  - `backend/analytics/core.py`, `backend/analytics/ships.py` — bulk `load_all_pilots` / `load_all_upgrades` for aggregation.
  - `backend/utils/squadron.py` — `get_pilot_info` for squadron normalization.
  - `backend/routers/ships.py` — `get_filtered_ships` for the ships router.
- **Depends on**: `json`, `pathlib`, `functools.lru_cache`; `backend.data_structures.data_source.DataSource` (StrEnum with XWA/LEGACY) and `backend.data_structures.factions.Faction`; the vendored JSON trees under `external_data/xwing-data2/data/` and `external_data/xwing-data2-legacy/data/`.
- **Exposes**:
  - `core.get_data_dir`, `core.load_factions`, `core.get_faction_name`
  - `pilots.load_all_pilots`, `pilots.get_pilot_info`, `pilots.get_pilot_name`, `pilots.get_pilot_image`, `pilots.search_pilot`
  - `ships.load_all_ships`, `ships.get_ship_info`, `ships.get_ship_icon_name`, `ships.get_filtered_ships`
  - `upgrades.load_all_upgrades`, `upgrades.get_upgrade_info`, `upgrades.get_upgrade_name`, `upgrades.get_upgrade_slot`
  - `parser.normalize_faction`, `parser.parse_xws`
