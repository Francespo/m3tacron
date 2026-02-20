import json
from pathlib import Path
from functools import lru_cache
from ...data_structures.data_source import DataSource

# Path to data directories
# m3tacron/backend/utils/xwing_data/core.py -> up to root
ROOT_DIR = Path(__file__).parents[4]
EXTERNAL_DATA_DIR = ROOT_DIR / "external_data"

XWA_DATA_DIR = EXTERNAL_DATA_DIR / "xwing-data2" / "data"
LEGACY_DATA_DIR = EXTERNAL_DATA_DIR / "xwing-data2-legacy" / "data"

def get_data_dir(source: DataSource) -> Path:
    """Get data directory for the specified source."""
    if source == DataSource.LEGACY:
        return LEGACY_DATA_DIR
    return XWA_DATA_DIR

@lru_cache(maxsize=1)
def load_factions() -> dict:
    """Load faction data. Returns dict mapping xws ID to faction info."""
    # Factions are common, default to XWA location
    factions_file = XWA_DATA_DIR / "factions" / "factions.json"
    if not factions_file.exists():
        return {}
    
    with open(factions_file, "r", encoding="utf-8") as f:
        factions = json.load(f)
    
    return {f["xws"]: f for f in factions}

def get_faction_name(faction_xws: str) -> str:
    """Get human-readable faction name from XWS ID."""
    factions = load_factions()
    faction_info = factions.get(faction_xws, {})
    return faction_info.get("name", faction_xws.replace("-", " ").title())
