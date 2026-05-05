from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
import os
import time

from .cache import persistent_cache, VERSION_FILE, CACHE_DATA_DIR
from .database import engine, create_db_and_tables
from .models import Tournament, PlayerResult
from .analytics.factions import get_meta_snapshot
from .data_structures.data_source import DataSource
from .api.schemas import MetaSnapshotResponse
from .api.tournaments import router as tournaments_router
from .api.lists import router as lists_router
from .api.squadrons import router as squadrons_router
from .api.cards import router as cards_router
from .api.ships import router as ships_router
from .api.pilot_detail import router as pilot_detail_router
from .api.ship_detail import router as ship_detail_router
from .api.squadron_detail import router as squadron_detail_router
from .api.list_detail import router as list_detail_router
from .api.support import router as support_router

app = FastAPI(title="M3taCron Backend", version="1.0.0")

# Include routers
app.include_router(tournaments_router)
app.include_router(lists_router)
app.include_router(squadrons_router)
app.include_router(cards_router)
app.include_router(ships_router)
app.include_router(pilot_detail_router)
app.include_router(ship_detail_router)
app.include_router(squadron_detail_router)
app.include_router(list_detail_router)
app.include_router(support_router)

# Configure CORS for frontend access
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
allow_all_origins = len(allowed_origins) == 1 and allowed_origins[0] == "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else allowed_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add Cache-Control headers to API responses for CDN/proxy caching."""

    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        if request.method == "GET" and response.status_code < 400:
            path = request.url.path

            if path.startswith("/api/cache/"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            elif path in ("/api/ships/all", "/api/tournaments/locations"):
                response.headers["Cache-Control"] = "public, max-age=3600"
            else:
                response.headers["Cache-Control"] = "public, max-age=600"
        return response


app.add_middleware(CacheControlMiddleware)


@app.on_event("startup")
def on_startup():
    retries = int(os.getenv("DB_STARTUP_RETRIES", "20"))
    delay_seconds = float(os.getenv("DB_STARTUP_DELAY_SECONDS", "3"))

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            create_db_and_tables()
            print(f"Database ready on attempt {attempt}/{retries}")
            return
        except Exception as exc:
            last_error = exc
            print(f"Database not ready (attempt {attempt}/{retries}): {exc}")
            time.sleep(delay_seconds)

    raise RuntimeError(f"Database startup failed after {retries} attempts: {last_error}")


@app.get("/")
def read_root():
    return {"status": "Backend is running"}


@app.get("/api/cache/status")
def get_cache_status():
    """Return cache statistics for monitoring."""
    return {
        "hits": persistent_cache.hits,
        "misses": persistent_cache.misses,
        "hot_size": persistent_cache.size,
        "hit_ratio": round(
            persistent_cache.hits / max(persistent_cache.hits + persistent_cache.misses, 1), 4
        ),
        "cache_version": VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "0",
    }


@app.post("/api/cache/clear")
def clear_cache(key: str = Query("", description="Secret key for authorization")):
    """Clear all cached responses and bump the cache version.

    Called by the GitHub Actions scrape workflow after a successful
    database update. Bumping the version file invalidates all existing
    cached entries atomically without needing to delete them from disk.
    """
    expected_key = os.getenv("CACHE_CLEAR_KEY", "")
    if expected_key and key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid cache clear key")

    version = str(int(time.time()))
    CACHE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        VERSION_FILE.write_text(version)
    except OSError as e:
        print(f"Warning: failed to write cache version file: {e}")
    # Also clear in-memory hot cache
    persistent_cache.clear()
    return {"status": "cache_cleared", "version": version}


@persistent_cache.cached(ttl=86400)
def _compute_meta_snapshot(data_source: str) -> dict:
    """Compute the full meta-snapshot. Cached until DB update."""
    ds_enum = DataSource.XWA if data_source == "xwa" else DataSource.LEGACY

    snapshot = get_meta_snapshot(ds_enum, allowed_formats=None)

    enriched_lists = snapshot.get("lists", [])

    total_tournaments = 0
    total_players = 0

    try:
        with Session(engine) as session:
            start_date = datetime.now() - timedelta(days=90)

            total_tournaments_query = select(func.count(Tournament.id)).where(Tournament.date >= start_date)
            res_tournaments = session.exec(total_tournaments_query).one_or_none()
            total_tournaments = res_tournaments if res_tournaments else 0

            total_players_query = select(func.count(PlayerResult.id)).join(Tournament).where(Tournament.date >= start_date)
            res_players = session.exec(total_players_query).one_or_none()
            total_players = res_players if res_players else 0
    except Exception as e:
        print(f"Error reading DB: {e}")

    return {
        "factions": snapshot.get("factions", []),
        "ships": snapshot.get("ships", []),
        "lists": enriched_lists,
        "pilots": snapshot.get("pilots", []),
        "upgrades": snapshot.get("upgrades", []),
        "last_sync": snapshot.get("last_sync", "Never"),
        "date_range": snapshot.get("date_range", "Unknown"),
        "total_tournaments": total_tournaments,
        "total_players": total_players,
    }


@app.get("/api/meta-snapshot", response_model=MetaSnapshotResponse)
def get_snapshot(data_source: str = Query("xwa", description="Data source: xwa or legacy")):
    result = _compute_meta_snapshot(data_source)
    return MetaSnapshotResponse(**result)
