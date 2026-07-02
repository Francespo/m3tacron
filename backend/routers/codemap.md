# backend/routers/

## Responsibility
HTTP route layer — FastAPI `APIRouter` modules exposing REST endpoints to the SvelteKit frontend. Each router groups related path operations around a resource (tournaments, lists, squadrons, ships, etc.) and is mounted on the FastAPI app.

## Design
- **APIRouter pattern**: one module per resource, each exporting a `router = APIRouter(...)` instance with optional `tags=[...]` for OpenAPI grouping.
- **Route registration**: `backend/main.py` calls `app.include_router(<name>_router)` for every router (no explicit `prefix=` is used; prefixes are baked into the path operations themselves).
- **Dependency injection**: handlers receive a SQLModel `Session` via the `get_db` dependency from `backend.database`, plus `Query`/`Path`/`Body` parameters validated by Pydantic.
- **Pydantic schemas**: request/response shapes come from `backend/api/schemas.py` (`MetaSnapshotResponse`, etc.); some routers return raw dicts/listings for simple lookups.
- **HTTP verbs used**: `GET` (reads — list/detail/snapshot endpoints), `POST` (writes — list create), and likely `PUT`/`DELETE` for admin-style operations where present.
- **CORS**: configured at the `app` level in `main.py` via `CORSMiddleware`, not per-router.

## Flow
1. HTTP request arrives at uvicorn.
2. uvicorn dispatches into the FastAPI `app` defined in `backend/main.py`.
3. FastAPI matches the path against every registered `APIRouter`'s path operations.
4. The path operation function runs; FastAPI resolves dependencies (`Depends(get_db)`, query/path/body params).
5. Handler executes business logic — typically querying the DB through SQLModel `Session`, or calling helpers in `backend/analytics/*`, `backend/api/*`, or `backend/utils/*`.
6. Return value is serialized through the Pydantic `response_model` (or returned as-is) into JSON.
7. `CORSMiddleware` adds the appropriate `Access-Control-*` headers before the response leaves uvicorn.

## Integration
- **Consumed by**: `backend/main.py` — `app.include_router(...)` for every module in this directory and the sibling `backend/api/` package.
- **Depends on**:
  - `backend.database` — `engine`, `create_db_and_tables`, `get_db` dependency
  - `backend.models` — SQLModel ORM models (`Tournament`, `PlayerStanding`, …)
  - `backend.api.schemas` — Pydantic response/request models
  - `backend.api.*` — sibling router modules re-exported via `from .api.X import router as X_router`
  - `backend.analytics.*` — meta-snapshot, faction, and stat aggregations
  - `backend.data_structures.data_source` — `DataSource` enum (`XWA` / `LEGACY`)
  - `backend.utils.xwing_data.*` — static game-data lookups (ships, pilots, upgrades)
- **Exposes**: REST API endpoints under URL prefixes registered by each router — e.g. `/ships` (this directory: `routers/ships.py`), plus the broader set from `backend/api/`: `/tournaments`, `/lists`, `/squadrons`, `/cards`, `/pilot-detail`, `/ship-detail`, `/squadron-detail`, `/list-detail`, `/support`, and the inline `/api/meta-snapshot` defined directly on `app`.
