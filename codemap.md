# Repository Atlas: m3tacron

## Project Responsibility
M3taCron is a full-stack X-Wing Miniatures tournament analytics platform. The FastAPI backend ingests tournament data from ListFortress, Longshanks, Rollbetter, and YASB; normalizes squads via XWS; and exposes derived analytics (faction win rates, ship/pilot/upgrade popularity, list distributions, meta snapshots) over a REST API. The SvelteKit frontend provides a dashboard, browseable pilot/ship/upgrade/squadron/list views, a deep pilot detail UI, and a public supporter page, all backed by a vendored xwing-data2 game-data manifest.

## System Entry Points
- `backend/main.py` — FastAPI `app` factory, CORS, retried `create_db_and_tables()` startup, 10 sub-routers under `backend/api.*`.
- `backend/database.py` — SQLAlchemy engine (SQLite WAL / Postgres via `DATABASE_URL`), schema bootstrap.
- `backend/models.py` — SQLModel ORM tables (`Tournament`, `PlayerStanding`, `Match`, `TeamStanding`, `TeamMatch`, `Supporter`, `Contribution`).
- `backend/scripts/scrape_tournaments.py` — primary multi-platform scraper entry (also wrapped by `scrape_tournaments_sqlite.py` for CI).
- `frontend/src/routes/+layout.svelte` — SvelteKit layout shell, mounts `Sidebar` and global state.
- `frontend/src/lib/api.ts` — `API_BASE` resolver for the FastAPI backend.
- `frontend/src/routes/api/[...path]/+server.js` — server-side GET proxy to the FastAPI service.
- `pyproject.toml` — Python project + tooling config.
- `docker-compose.yml` (and `dev/local/perf/prod` variants) — multi-environment stack orchestration.
- `scripts/local_dev/`, `scripts/perf/` — shell tooling for dev, perf, and reporting.

## Directory Map (Aggregated)

| Directory | Responsibility Summary | Detailed Map |
|-----------|------------------------|--------------|
| `backend/` | FastAPI app factory, SQLAlchemy engine, SQLModel ORM, retried DB-init startup, CORS, router registration. | [View Map](backend/codemap.md) |
| `backend/routers/` | Thin placeholder for FastAPI `APIRouter` modules (only `ships.py` lives here today; bulk of routes are in `backend/api/`). | [View Map](backend/routers/codemap.md) |
| `backend/api/` | FastAPI service layer: 10 versioned routers, Pydantic schemas, transactional detail reads, Ko-fi webhook, list-enrichment seam. | [View Map](backend/api/codemap.md) |
| `backend/scrapers/` | External data ingestion from ListFortress / Longshanks / Rollbetter / YASB; `BaseScraper` + Playwright + httpx; XWS export from YASB. | [View Map](backend/scrapers/codemap.md) |
| `backend/data/` | Persistent on-disk store: single `geocoding_cache.json` write-through cache for venue resolution. | [View Map](backend/data/codemap.md) |
| `backend/data_structures/` | Canonical vocabulary (`Faction`, `Format`, `Source`, `Scenario`, `RoundType`, `UpgradeType`, `SortingCriteria`, `SortDirection`, `ViewMode`, `DataSource`) and the `Location` / `LocationType` Pydantic+JSON value object. | [View Map](backend/data_structures/codemap.md) |
| `backend/analytics/` | SQL-first filtering + Python-side aggregation: `aggregate_card_stats`, `aggregate_ship_stats`, `aggregate_list_stats`, `aggregate_squadron_stats`, `get_meta_snapshot`, `get_card_usage_history`. | [View Map](backend/analytics/codemap.md) |
| `backend/utils/` | Cross-cutting helpers: throttled Nominatim geocoding, XWS canonicalization (`get_list_key`, squadron signatures), cross-platform `DedupService`, YASB URL builders, location hierarchy. | [View Map](backend/utils/codemap.md) |
| `backend/utils/xwing_data/` | Cached wrapper over vendored xwing-data2 / xwing-data2-legacy JSON; `load_all_pilots`/`ships`/`upgrades`, `parse_xws`, `normalize_faction`, `get_ship_icon_name`. | [View Map](backend/utils/xwing_data/codemap.md) |
| `backend/scripts/` | Operational scripts: multi-platform scraper, dedup runner, team-name migration, SQLite→Postgres importer, shared dedup helper. | [View Map](backend/scripts/codemap.md) |
| `frontend/` | SvelteKit 2 + Svelte 5 runes app: dashboard, tournaments/squadrons/lists/ships/pilots/upgrades browse and detail, supporter page, Tailwind "terminal" theme, Chart.js, SvelteKit server proxy. | [View Map](frontend/codemap.md) |

## Cross-Cutting Data Flow
1. `backend/scripts/scrape_tournaments.py` (or its SQLite wrapper) instantiates `BaseScraper` subclasses per platform.
2. Scraper fetches tournament lists → runs `get_participants` (XWS for format inference) → `get_tournament_data` → `get_matches`; maps to ORM rows.
3. `utils.geocoding.resolve_location` and `utils.deduplication.DedupService.find_duplicate` normalize and dedupe.
4. ORM rows are persisted via `database.engine`; `data_structures.Format` / `Faction` / `Location` normalize typed columns.
5. `backend/api/*` endpoints parse `Query` params into filter dicts, call `backend/analytics/*` aggregators or run direct `Session(engine)` reads, and shape responses into Pydantic schemas in `backend/api/schemas.py`.
6. The SvelteKit frontend loads each route via `+page.ts` `load`, calling `API_BASE/<endpoint>` (or its own server proxy under `routes/api/[...path]/+server.js`).
7. The shared `filters` store and `xwingData` reactive manifest store drive dashboard, list, and detail reactivity.

## Integration Points
- **Frontend → Backend**: REST under `/api/*`; CORS or same-origin via the SvelteKit server proxy.
- **Backend → External**: ListFortress REST, Longshanks Playwright, Rollbetter REST + Playwright, YASB UI via Playwright, Nominatim for geocoding, Ko-fi webhook for supporter ingest.
- **CI**: `.github/workflows/scrape_tournaments.yml` invokes `backend/scripts/scrape_tournaments_sqlite.py`, commits the updated `backend/data/geocoding_cache.json`.
- **Container**: `docker-compose.yml` mounts `backend/data/` as a `data` volume so the geocoding cache persists across restarts.
- **External data**: Vendored `external_data/xwing-data2/` and `external_data/xwing-data2-legacy/` JSON trees feed `backend/utils/xwing_data/` and the prebuilt manifests under `frontend/static/data-{xwa,legacy}/`.
