from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
import os

from .database import engine, create_db_and_tables
from .models import Tournament, PlayerResult
from .analytics.factions import get_meta_snapshot
from .data_structures.data_source import DataSource
from .api.schemas import MetaSnapshotResponse
from .api.formatters import enrich_list_data

app = FastAPI(title="M3taCron Backend", version="1.0.0")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.get("/api/meta-snapshot", response_model=MetaSnapshotResponse)
def get_snapshot(data_source: str = Query("xwa", description="Data source: xwa or legacy")):
    ds_enum = DataSource.XWA if data_source == "xwa" else DataSource.LEGACY
    
    # We parse what HomeState loaded
    snapshot = get_meta_snapshot(ds_enum, allowed_formats=None)
    
    raw_lists = snapshot.get("lists", [])
    enriched_lists = [enrich_list_data(l) for l in raw_lists]
    
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
        # Fallback to 0 if database fails or is empty initially
        print(f"Error reading DB: {e}")
        
    return MetaSnapshotResponse(
        factions=snapshot.get("factions", []),
        faction_distribution=snapshot.get("faction_distribution", []),
        ships=snapshot.get("ships", []),
        lists=enriched_lists,
        pilots=snapshot.get("pilots", []),
        upgrades=snapshot.get("upgrades", []),
        last_sync=snapshot.get("last_sync", "Never"),
        date_range=snapshot.get("date_range", "Unknown"),
        total_tournaments=total_tournaments,
        total_players=total_players
    )
