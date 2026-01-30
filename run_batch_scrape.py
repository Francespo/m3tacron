
import sys
import logging
import subprocess
import os
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel, delete

# Setup Logging
logging.basicConfig(level=logging.INFO)

# Add project root
sys.path.append(str(Path(__file__).parent))

from m3tacron.backend.models import Tournament, PlayerResult, Match

# DB Setup
DB_FILE = "test_results.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

def get_engine():
    return create_engine(DATABASE_URL)

URLS = [
    "https://xwing.longshanks.org/event/29346/",
    "https://xwing-legacy.longshanks.org/event/28919/"
]

def init_db():
    print(f"Initializing DB: {DB_FILE}...")
    SQLModel.metadata.create_all(get_engine())

def cleanup_db():
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print(f"Deleted {DB_FILE} for clean schema regeneration.")
        except Exception as e:
            print(f"Warning: Could not delete {DB_FILE}: {e}")
    
    print(f"Ensuring match, playerresult, tournament tables exist...")
    SQLModel.metadata.create_all(get_engine())
    print("Database cleared.")

def run_orchestrator():
    cleanup_db()
    
    for url in URLS:
        print(f"\n>>> Dispatching worker for: {url}")
        
        # Run worker as subprocess
        result = subprocess.run(
            ["python", "batch_worker.py", url, "test"],
            capture_output=False, 
            check=False
        )
        
        if result.returncode != 0:
            print(f"❌ Worker failed for {url} with exit code {result.returncode}")

if __name__ == "__main__":
    run_orchestrator()
