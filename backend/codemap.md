# backend/

## Responsibility
The top-level package of the M3taCron FastAPI service: it constructs the ASGI `app`, configures CORS, registers API routers, owns the SQLAlchemy engine/ORM metadata, and performs a retried DB-init on startup. `main.py`, `database.py`, and `models.py` are the three entry-point modules that the rest of the package builds on.

## Design
- **FastAPI application object** in `main.py`: `app = FastAPI(title="M3taCron Backend", version="1.0.0")` — the Uvicorn/ASGI target.
- **CORS middleware** added with origins pulled from the `ALLOWED_ORIGINS` env var (defaults to `"*"`); credentials and origin lists are toggled together to stay spec-compliant.
- **Router registration**: `app.include_router(...)` is called for 10 sub-routers under `backend.api.*` (tournaments, lists, squadrons, cards, ships, pilot_detail, ship_detail, squadron_detail, list_detail, support). The `backend.routers/` package is effectively a legacy/placeholder (only `ships.py`); all current routes live in `backend/api/`.
- **Direct-engine session pattern** (no FastAPI `Depends`): routers import `from ..database import engine` and open sessions via `with Session(engine) as session:`. There is no `get_db` dependency and no `SessionLocal` factory.
- **SQLAlchemy engine** in `database.py`: `engine = create_engine(DATABASE_URL, connect_args=..., pool_pre_ping=True, pool_recycle=300)`. URL resolves from `DATABASE_URL` env (with `dotenv` loaded) and falls back to a local SQLite file at `<repo>/test.db`; `postgres://` is rewritten to `postgresql://`.
- **SQLite hardening** via a `@event.listens_for(engine, "connect")` hook that runs `PRAGMA journal_mode=WAL;`, plus a 30s connect `timeout`, to support parallel scraper writers.
- **Schema bootstrap**: `create_db_and_tables()` calls `SQLModel.metadata.create_all(engine)`. `database.py` eagerly imports the ORM models from `models.py` so the metadata is populated before the function runs.
- **Startup event** in `main.py`: `@app.on_event("startup")` retries `create_db_and_tables()` up to `DB_STARTUP_RETRIES` (default 20) times with `DB_STARTUP_DELAY_SECONDS` (default 3s) between attempts, then raises `RuntimeError` — used to wait for Postgres/Supabase readiness in containerized deploys.
- **ORM models** in `models.py` (all `SQLModel, table=True`): `Tournament`, `TeamStanding`, `PlayerStanding`, `Match`, `TeamMatch`, `Supporter`, `Contribution`. `Tournament` ↔ `PlayerStanding`/`TeamStanding` are wired with `Relationship(back_populates=...)`; `Match.player1_id`/`player2_id` FK to `playerstanding.id`; `TeamMatch.team1_id`/`team2_id` FK to `teamstanding.id`. Custom SQLAlchemy `Column` types are used for `JSON` (`list_json`) and for the composite `LocationType` (stored via `data_structures.location.Location`).
- **Domain enums** are imported from `backend.data_structures` (`Format`, `Source`, `Scenario`, `RoundType`, `Location`, `LocationType`) and persisted as `String` columns rather than native SQL enums.

## Flow
1. Uvicorn loads `main:app`; CORS middleware is wrapped around all routes.
2. On startup, `on_startup()` loops, calling `create_db_and_tables()` until the DB is reachable, then `SQLModel.metadata.create_all(engine)` materializes tables from `SQLModel.metadata` (populated by importing `models.py` at the top of `database.py`).
3. A client request hits a path under one of the included `APIRouter`s (e.g., `/api/tournaments/...`).
4. The route handler opens a session directly: `with Session(engine) as session:`, runs `select(...)`/`func.count(...)` over ORM models, and commits implicitly on context exit.
5. The handler returns either a `dict` or a Pydantic response model from `api.schemas` (e.g., `PaginatedTournamentsResponse`, `MetaSnapshotResponse`); FastAPI serializes it to JSON.
6. The health endpoint `GET /` returns `{"status": "Backend is running"}`; `GET /api/meta-snapshot` is defined inline in `main.py` and composes `analytics.factions.get_meta_snapshot()` with a DB count of tournaments/players over the last 90 days, returning a `MetaSnapshotResponse`.

## Integration
- **Consumed by**: Uvicorn / ASGI server (e.g., the `Dockerfile` entrypoint references `main:app`); the frontend hits the `/api/*` surface.
- **Depends on**:
  - `backend.database` — `engine`, `create_db_and_tables`
  - `backend.models` — `Tournament`, `PlayerStanding`, `TeamStanding`, `Match`, `TeamMatch`, `Supporter`, `Contribution`
  - `backend.api.*` — 10 routers and `api.schemas` (Pydantic response models, `MetaSnapshotResponse`)
  - `backend.analytics.factions` — `get_meta_snapshot`
  - `backend.data_structures` — `DataSource`, `Format`, `Source`, `Scenario`, `RoundType`, `Location`, `LocationType`
- **Exposes**: FastAPI `app` (the ASGI application); module-level `engine` and `create_db_and_tables()` from `database.py`; all ORM table classes via `models.py` for re-import by routers, scrapers (`backend.scrapers`), and CLI scripts (`backend.scripts`).
