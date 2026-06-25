# backend/analytics/

## Responsibility
Aggregation/analytics layer that computes derived metrics from raw ORM data (tournament results, XWS squad lists). Produces faction win rates, ship/pilot/upgrade popularity, squad list distributions, usage history time series, and a 90-day meta snapshot.

## Design
- **SQL-first filtering, Python-side aggregation**: every aggregator runs a `SELECT PlayerStanding, Tournament` join, applies SQL-level filters via `filters.filter_query`, then streams rows and tallies counts in Python dicts keyed by signature/xws.
- **List deduplication via canonical signatures**: lists and squadrons are collapsed by sorting pilots/upgrades and hashing the JSON (or using `utils.list_keys.get_list_key`); `different_lists_count` is the size of the per-key signature set.
- **No external DataFrame libs**: pure `dict`/`set`/`defaultdict` aggregation; JSON used for canonical signatures.
- **Format/legality gating**: `filters.get_active_formats` + `apply_tournament_filters` handle Python-side filtering of tournament.format and Tournament.location (continent/country/city) that SQL can't express. Card-level `valid_in_standard`/`wildspace`/`epic` flags gate which cards are even initialised.
- **Module split mirrors output type**: one module per entity (factions, ships, squadrons, lists, core=pilots/upgrades, charts=time series). `new_lists.py` is a near-duplicate of `lists.py` with slightly different canonicalisation.
- **Result objects are dicts**, not Pydantic models — shaped to match `backend.api.schemas.PilotStats`/`UpgradeStats`/`FactionStats`/`ShipStats`/`ListData`/`MetaSnapshotResponse`.

## Flow
1. Caller in `backend/api/*` (e.g. `api/cards.py`, `api/ships.py`, `api/lists.py`, `api/squadrons.py`, `api/pilot_detail.py`, `api/ship_detail.py`, `api/squadron_detail.py`, `api/list_detail.py`) builds a `filters` dict and invokes an aggregator.
2. Function opens a `Session(engine)` against `backend.database`, runs `select(PlayerStanding, Tournament).where(...tournament_id == tournament.id)`.
3. `filters.filter_query` applies SQL WHERE clauses for `date_start`/`date_end`/`source`/`player_count_*`.
4. For each row: `apply_tournament_filters` (location), format check, then Python-side accumulation into a `{xws: {games_count, list_count, wins, _signatures: set}}` map.
5. Pilot/upgrade iteration walks `xws["pilots"]` → `p["upgrades"]`; per-list uniqueness is tracked with `set()` to avoid double-counting a pilot appearing twice in one list.
6. Final pass converts `_signatures` set into `different_lists_count` and sorts by `SortingCriteria`/`SortDirection`.
7. `get_meta_snapshot` is a composite that calls all aggregators with a 90-day `date_start` filter and bundles them into a `MetaSnapshotResponse` dict.

## Integration
- **Consumed by**:
  - `backend/api/cards.py` → `aggregate_card_stats`
  - `backend/api/ships.py` → `aggregate_ship_stats`
  - `backend/api/lists.py` → `aggregate_list_stats` (from `lists.py`)
  - `backend/api/squadrons.py` → `aggregate_squadron_stats`
  - `backend/api/pilot_detail.py` → `aggregate_card_stats`, `get_card_usage_history`
  - `backend/api/ship_detail.py` → `aggregate_ship_stats`, `aggregate_list_stats`, `aggregate_squadron_stats`, `aggregate_card_stats`
  - `backend/api/squadron_detail.py` → `aggregate_list_stats`, `filters.filter_query/get_active_formats`
  - `backend/api/list_detail.py` → `filters.filter_query/get_active_formats`
  - `backend/main.py` → `get_meta_snapshot` (homepage meta feed)
  - `backend/tests/performance/test_db_queries.py` → `get_meta_snapshot`
- **Depends on**:
  - `backend.database.engine` (SQLModel session)
  - `backend.models.{PlayerStanding, Tournament}`
  - `backend.data_structures.{factions.Faction, data_source.DataSource, sorting_order.{SortingCriteria,SortDirection}, formats.Format}`
  - `backend.utils.xwing_data.{pilots,upgrades}` (static card metadata)
  - `backend.utils.list_keys.get_list_key` (canonical list hashing)
  - `backend.api.schemas` (`ListData`, `PilotData`, `UpgradeData` — type hints only, in `new_lists.py`)
- **Exposes** (public surface re-exported from `__init__.py`):
  - `aggregate_card_stats(filters, sort_criteria, sort_direction, mode="pilots"|"upgrades", data_source)` — per-card games/list/wins/different_lists; mode toggles pilot vs upgrade aggregation.
  - `aggregate_faction_stats(filters, data_source)` — per-faction totals across the `Faction` enum.
  - `aggregate_ship_stats(filters, sort_criteria, sort_direction, data_source)` — per (ship_xws, faction) tuple.
  - `aggregate_squadron_stats(filters, sort_metric, sort_direction, data_source)` — per ship-composition signature.
  - `aggregate_list_stats(filters, limit, data_source)` — top-N canonical lists by games (lives in both `lists.py` and `new_lists.py`; the latter is the newer canonicaliser).
  - `get_meta_snapshot(data_source, allowed_formats)` — 90-day composite: factions + ships + lists + pilots + upgrades.
  - `get_card_usage_history(filters, main_card_xws, comparison_xws_list, is_upgrade)` — monthly time series for Recharts.
  - `filter_query(query, filters)` / `apply_tournament_filters(tournament, filters)` / `check_format_filter(tournament, format_selection)` / `get_active_formats(format_selection)` — filter helpers used directly by API modules.
