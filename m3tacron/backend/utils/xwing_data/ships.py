import json
from functools import lru_cache
from ...data_structures.data_source import DataSource
from .core import get_data_dir

@lru_cache(maxsize=2)
def load_all_ships(source: DataSource = DataSource.XWA) -> list[dict]:
    """
    Load all unique ship chassis.
    Returns list of dicts: {"name": "X-wing", "xws": "t65xwing", "factions": ["rebelalliance"]}
    """
    data_dir = get_data_dir(source)
    pilots_dir = data_dir / "pilots"
    if not pilots_dir.exists():
        return []
    
    ships_map = {} # xws -> {name, xws, factions: set}
    
    for faction_dir in pilots_dir.iterdir():
        if not faction_dir.is_dir():
            continue
            
        current_faction = faction_dir.name
            
        for ship_file in faction_dir.glob("*.json"):
            try:
                with open(ship_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                xws = data.get("xws")
                name = data.get("name")
                
                if xws and name:
                    if xws not in ships_map:
                        ships_map[xws] = {
                            "name": name, 
                            "xws": xws, 
                            "factions": set()
                        }
                    ships_map[xws]["factions"].add(data.get("faction") or current_faction)
                    
            except Exception:
                continue
                
    results = []
    for s in ships_map.values():
        s["factions"] = list(s["factions"])
        results.append(s)
        
    return sorted(results, key=lambda x: x["name"])


def get_filtered_ships(factions: list[str] = None) -> list[dict]:
    """
    Get list of ships filtered by factions.
    Args:
        factions: List of faction XWS strings (e.g. ["rebelalliance"]).
                  If None or empty, returns all ships.
    """
    all_ships = load_all_ships()
    
    if not factions:
        return all_ships
        
    filtered = []
    target_factions = set(factions)
    
    for ship in all_ships:
        if not set(ship["factions"]).isdisjoint(target_factions):
            filtered.append(ship)
            
    return filtered
