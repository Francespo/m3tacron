# backend/api/

## Responsibility
This directory is the FastAPI service layer. It exposes versioned REST routers that turn HTTP requests into queries against the analytics/data layer and return Pydantic-typed responses, without owning HTTP transport wiring (that is `backend/main.py`'s job).

## Design
- **Routers as thin controllers**: each module defines a single `APIRouter` with a versioned prefix (`/api/...`) and a tag. Endpoints are plain functions that parse `Query` parameters, build a `filters` dict, and delegate computation to `backend/analytics/*` aggregators.
- **Stateless module-level routers** — no service classes are used; "business logic" lives in the analytics package. Here it is mostly orchestration: filter shaping, pagination, sort-direction mapping, and response wrapping.
- **Transactional boundaries** for non-aggregated reads/writes: `tournaments.py`, `list_detail.py`, `squadron_detail.py`, `pilot_detail.py`, and `support.py` open explicit `with Session(engine) as session:` blocks; the webhook in `support.kofi_webhook` commits Supporter/Contribution writes transactionally.
- **Pydantic contracts** live in `schemas.py` (`ListData`, `PilotData`, `UpgradeData`, `TournamentData`, `PlayerStandingData`, `MatchData`, plus `Paginated*` and `FundStatusResponse` envelopes). Endpoints declare `response_model=` so FastAPI serializes ORM rows + raw dicts into typed shapes.
- **Enrichment seam**: `formatters.enrich_list_data` joins raw aggregate dicts with static game metadata from `backend/utils/xwing_data` (`get_pilot_info`, `get_upgrade_info`, `get_ship_icon_name`) and normalizes the faction key through `Faction.from_xws`. Used by `list_detail`, `ship_detail`, and `squadron_detail`.
- **Data source awareness**: nearly every endpoint normalizes the `data_source` query string to a `DataSource` enum (`XWA` | `LEGACY`) and threads it into both analytics aggregators and xwing-data lookups.
- **Inline filter builders**: `cards._build_filters` and similar local helpers translate HTTP query params into the dict shape `analytics.filters.filter_query` consumes.

## Flow
1. `backend/main.py` mounts the routers from each module (e.g. `from .api.tournaments import router as tournaments_router`).
2. A request hits an endpoint, which parses `Query` params into a `filters` dict plus pagination/sort tuples.
3. The endpoint either:
   - calls an analytics aggregator (`aggregate_card_stats`, `aggregate_list_stats`, `aggregate_ship_stats`, `aggregate_squadron_stats`, `get_card_usage_history`), OR
   - opens a `Session(engine)` and runs a `sqlmodel.select` over `Tournament` / `PlayerStanding` / `Match` / `Supporter` / `Contribution`, optionally narrowed by `analytics.filters.filter_query`.
4. Results are optionally passed through `formatters.enrich_list_data` to attach static pilot/upgrade/ship metadata.
5. The endpoint returns a `Paginated*Response` (or a detail object) from `schemas.py`; FastAPI handles serialization.

## Integration
- **Consumed by**: `backend/main.py` (imports `tournaments`, `lists`, `squadrons`, `cards`, `ships`, `pilot_detail`, `ship_detail`, `squadron_detail`, `list_detail`, `support` routers and `MetaSnapshotResponse` from `schemas`); `backend/analytics/new_lists.py` reuses `ListData`/`PilotData`/`UpgradeData` for type compatibility.
- **Depends on**:
  - `backend.analytics` — aggregators (`core`, `lists`, `ships`, `squadrons`, `charts`) and `filters.filter_query` / `get_active_formats`
  - `backend.models` — ORM tables `Tournament`, `PlayerStanding`, `Match`, `Supporter`, `Contribution`
  - `backend.database` — `engine`, `create_db_and_tables`
  - `backend.data_structures` — `DataSource`, `Faction`, `Format`, `Source`, `SortingCriteria`, `SortDirection`
  - `backend.utils.xwing_data` — `pilots`, `ships`, `upgrades` lookup helpers and `list_keys.get_list_key`
- **Exposes** (public routers/handlers):
  - `cards.get_pilots`, `cards.get_upgrades` — paginated pilot/upgrade analytics
  - `ships.get_ships`, `ships.get_all_ships` — paginated ship list and full chassis catalog
  - `lists.get_lists` — paginated list analytics
  - `squadrons.get_squadrons` — paginated squadron (chassis-combo) analytics
  - `pilot_detail.get_pilot_info` / `get_pilot_upgrades` / `get_pilot_chart` / `get_pilot_configurations`
  - `ship_detail.get_ship_info` / `get_ship_pilots` / `get_ship_lists` / `get_ship_squadrons`
  - `list_detail.get_list_stats` — full composition + aggregated record for a list signature
  - `squadron_detail.get_squadron_stats` / `get_squadron_pilots` / `get_squadron_lists`
  - `tournaments.get_tournaments` / `get_tournament_detail` / `get_locations`
  - `support.get_fund_status` / `get_supporters` / `support.kofi_webhook` (Ko-fi donation ingest)
  - `formatters.enrich_list_data` — shared enrichment helper
  - `schemas.*` — Pydantic response/request models
