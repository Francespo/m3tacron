from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
import os
import time

from .database import engine, create_db_and_tables
from .models import Tournament, PlayerStanding
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

@app.on_event("startup")
def on_startup():
    retries = int(os.getenv("DB_STARTUP_RETRIES", "20"))
    delay_seconds = float(os.getenv("DB_STARTUP_DELAY_SECONDS", "3"))

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            create_db_and_tables()
            print(f"Database ready on attempt {attempt}/{retries}")
            break
        except Exception as exc:
            last_error = exc
            print(f"Database not ready (attempt {attempt}/{retries}): {exc}")
            time.sleep(delay_seconds)
    else:
        raise RuntimeError(f"Database startup failed after {retries} attempts: {last_error}")

    # Pre-warm the analytics cache so the first user request is instant.
    # Runs in a background thread so the server accepts traffic immediately.
    if os.getenv("PREWARM_CACHE", "true").lower() == "true":
        _prewarm_cache()


def _prewarm_cache():
    """Hit the API endpoints via HTTP so cache keys exactly match what users request.

    Runs in a daemon thread so startup returns immediately. Uses internal
    HTTP requests (no external port needed) via the same uvicorn worker.
    """
    import threading

    def _run():
        import urllib.request
        import json

        base = "http://127.0.0.1:8888"
        # Cover the most common URL variants the frontend sends on first visit
        endpoints = [
            # Lists - default landing, with and without min_games/factions
            "lists?page=0&size=20&sort_metric=Games&sort_direction=desc&min_games=3&data_source=xwa",
            "lists?page=0&size=20&sort_metric=Games&sort_direction=desc&data_source=xwa",
            "lists?page=0&size=20&sort_metric=Win%20Rate&sort_direction=desc&min_games=3&data_source=xwa",
            # Squadrons - default + Win Rate
            "squadrons?page=0&size=20&sort_metric=Games&sort_direction=desc&data_source=xwa",
            "squadrons?page=0&size=20&sort_metric=Win%20Rate&sort_direction=desc&data_source=xwa",
            # Ships - Popularity + Games
            "ships?page=0&size=50&sort_metric=Popularity&sort_direction=desc&data_source=xwa",
            "ships?page=0&size=50&sort_metric=Games&sort_direction=desc&data_source=xwa",
            # Cards/Pilots - default
            "cards/pilots?page=0&size=20&sort_metric=Popularity&sort_direction=desc&data_source=xwa",
            "cards/pilots?page=0&size=20&sort_metric=Win%20Rate&sort_direction=desc&data_source=xwa",
            # Cards/Upgrades - default
            "cards/upgrades?page=0&size=20&sort_metric=Popularity&sort_direction=desc&data_source=xwa",
            "cards/upgrades?page=0&size=20&sort_metric=Win%20Rate&sort_direction=desc&data_source=xwa",
        ]
        for path in endpoints:
            name = path.split("?")[0].split("/")[-1] or "root"
            try:
                t0 = time.time()
                req = urllib.request.Request(f"{base}/api/{path}")
                resp = urllib.request.urlopen(req, timeout=150)
                data = json.loads(resp.read())
                count = data.get("total", len(data.get("items", [])))
                elapsed = time.time() - t0
                print(f"[prewarm] {name}: {count} items in {elapsed:.1f}s ✓")
            except Exception as e:
                print(f"[prewarm] {name}: FAILED ({e})")

        print("[prewarm] done")

    thread = threading.Thread(target=_run, daemon=True, name="cache-prewarm")
    thread.start()

@app.get("/")
def read_root():
    return {"status": "Backend is running"}


@app.get("/api/meta-snapshot", response_model=MetaSnapshotResponse)
def get_snapshot(data_source: str = Query("xwa", description="Data source: xwa or legacy")):
    ds_enum = DataSource.XWA if data_source == "xwa" else DataSource.LEGACY
    
    # We parse what HomeState loaded
    snapshot = get_meta_snapshot(ds_enum, allowed_formats=None)
    
    # Lists are already aggregated in correct format by lists.aggregate_list_stats
    enriched_lists = snapshot.get("lists", [])
    
    total_tournaments = 0
    total_players = 0
    
    try:
        with Session(engine) as session:
            start_date = datetime.now() - timedelta(days=90)
            
            total_tournaments_query = select(func.count(Tournament.id)).where(Tournament.date >= start_date)
            res_tournaments = session.exec(total_tournaments_query).one_or_none()
            total_tournaments = res_tournaments if res_tournaments else 0
            
            total_players_query = select(func.count(PlayerStanding.id)).join(Tournament).where(Tournament.date >= start_date)
            res_players = session.exec(total_players_query).one_or_none()
            total_players = res_players if res_players else 0
    except Exception as e:
        # Fallback to 0 if database fails or is empty initially
        print(f"Error reading DB: {e}")
        
    return MetaSnapshotResponse(
        factions=snapshot.get("factions", []),
        ships=snapshot.get("ships", []),
        lists=enriched_lists,
        pilots=snapshot.get("pilots", []),
        upgrades=snapshot.get("upgrades", []),
        last_sync=snapshot.get("last_sync", "Never"),
        date_range=snapshot.get("date_range", "Unknown"),
        total_tournaments=total_tournaments,
        total_players=total_players
    )
