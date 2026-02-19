import json
from functools import lru_cache
from ...data_structures.data_source import DataSource
from .core import get_data_dir

@lru_cache(maxsize=4)
def load_all_ships(source: DataSource = DataSource.XWA) -> dict:
    """Load all ships. Returns dict mapping xws ID to ship info."""
    data_dir = get_data_dir(source)
    pilots_dir = data_dir / "pilots"
    
    if not pilots_dir.exists():
        return {}
    
    all_ships = {}
    
    for faction_dir in pilots_dir.iterdir():
        if not faction_dir.is_dir():
            continue
        
        for ship_file in faction_dir.glob("*.json"):
            try:
                with open(ship_file, "r", encoding="utf-8") as f:
                    ship_data = json.load(f)
                
                xws_id = ship_data.get("xws", "")
                if xws_id:
                    # Basic ship info
                    all_ships[xws_id] = {
                        "name": ship_data.get("name", "Unknown Ship"),
                        "xws": xws_id,
                        "faction": ship_data.get("faction", ""),
                        "icon": ship_data.get("icon", ""),
                        "size": ship_data.get("size", "Small"),
                        "stats": ship_data.get("stats", []),
                        "actions": ship_data.get("actions", []),
                        "maneuvers": ship_data.get("maneuvers", []),
                    }
            except Exception:
                continue
            
    return all_ships

def get_ship_info(xws_ship: str, source: DataSource = DataSource.XWA) -> dict | None:
    """Get full ship info from XWS ID."""
    ships = load_all_ships(source)
    return ships.get(xws_ship)

def get_ship_icon_name(ship_xws: str) -> str:
    """
    Get the icon class name/suffix from ship XWS ID.
    Replicates logic from components/icons.py but for backend/string usage.
    """
    clean_name = ship_xws.lower().replace("xwing-miniatures-ship-", "")
    if clean_name == "tieininterceptor":
        return "tieinterceptor"
    return clean_name

def get_filtered_ships(faction_filter: str | list[str] | None = "all", source: DataSource = DataSource.XWA) -> list[dict]:
    """Get a list of ships, optionally filtered by faction."""
    ships = load_all_ships(source)
    result = []
    
    # Normalize Filter
    allowed_factions = set()
    if faction_filter and faction_filter != "all":
        if isinstance(faction_filter, str):
            allowed_factions.add(faction_filter.lower().replace(" ", ""))
        elif isinstance(faction_filter, list):
            for f in faction_filter:
                if isinstance(f, str):
                    allowed_factions.add(f.lower().replace(" ", ""))

    for ship in ships.values():
        if allowed_factions:
            # Check faction match
            s_fact = ship.get("faction", "").lower().replace(" ", "")
            if s_fact not in allowed_factions:
                continue
            
        result.append(ship)
        
    return result
