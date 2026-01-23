import json
from functools import lru_cache
from ...data_structures.data_source import DataSource
from .core import get_data_dir

@lru_cache(maxsize=4)
def load_all_pilots(source: DataSource = DataSource.XWA) -> dict:
    """Load all pilots from all factions. Returns dict mapping xws ID to pilot info."""
    data_dir = get_data_dir(source)
    pilots_dir = data_dir / "pilots"
    
    if not pilots_dir.exists():
        return {}
    
    all_pilots = {}
    
    for faction_dir in pilots_dir.iterdir():
        if not faction_dir.is_dir():
            continue
        
        for ship_file in faction_dir.glob("*.json"):
            try:
                with open(ship_file, "r", encoding="utf-8") as f:
                    ship_data = json.load(f)
                
                ship_name = ship_data.get("name", "Unknown Ship")
                ship_icon = ship_data.get("icon", "")
                faction = ship_data.get("faction", "")
                
                for pilot in ship_data.get("pilots", []):
                    xws_id = pilot.get("xws", "")
                    if xws_id:
                        all_pilots[xws_id] = {
                            "name": pilot.get("name", xws_id),
                            "caption": pilot.get("caption", ""),
                            "ship": ship_name,
                            "ship_xws": ship_data.get("xws", ""),
                            "ship_icon": ship_icon,
                            "faction": faction,
                            "image": pilot.get("image", ""),
                            "artwork": pilot.get("artwork", ""),
                            "initiative": pilot.get("initiative", 0),
                            "cost": pilot.get("cost", 0),
                            "ability": pilot.get("ability", ""),
                        }
            except Exception:
                continue
    
    # Manual patches for missing scenario pilots (e.g. Battle of Yavin / D'Qar)
    # Only apply to XWA, they don't exist in Legacy.
    # For safety, applying generally if missing.
    MANUAL_PILOT_DATA = {
        "longshot-evacuationofdqar": {
            "name": "Longshot", "ship": "TIE/fo Fighter", "ship_xws": "tiefofighter", "faction": "First Order", "ship_icon": "tiefofighter"
        },
        "stomeronistarck-evacuationofdqar": {
            "name": "Stomeroni Starck", "ship": "T-70 X-wing", "ship_xws": "t70xwing", "faction": "Resistance", "ship_icon": "t70xwing"
        },
        "zizitlo-evacuationofdqar": {
            "name": "Zizi Tlo", "ship": "RZ-2 A-wing", "ship_xws": "rz2awing", "faction": "Resistance", "ship_icon": "rz2awing"
        },
        "caithrenalli-evacuationofdqar": {
            "name": "C'ai Threnalli", "ship": "T-70 X-wing", "ship_xws": "t70xwing", "faction": "Resistance", "ship_icon": "t70xwing"
        },
        "fennrau-armedanddangerous": {
            "name": "Fenn Rau", "ship": "Fang Fighter", "ship_xws": "fangfighter", "faction": "Scum and Villainy", "ship_icon": "fangfighter"
        },
        "themandalorian-armedanddangerous": {
            "name": "The Mandalorian", "ship": "ST-70 Assault Ship", "ship_xws": "st70assaultship", "faction": "Scum and Villainy", "ship_icon": "st70assaultship"
        },
        "dengar-armedanddangerous": {
            "name": "Dengar", "ship": "JumpMaster 5000", "ship_xws": "jumpmaster5000", "faction": "Scum and Villainy", "ship_icon": "jumpmaster5000"
        },
        "bossk-armedanddangerous": {
            "name": "Bossk", "ship": "YV-666", "ship_xws": "yv666lightfreighter", "faction": "Scum and Villainy", "ship_icon": "yv666lightfreighter"
        },
        "cadbane-armedanddangerous": {
            "name": "Cad Bane", "ship": "Rogue-class Starfighter", "ship_xws": "rogueclassstarfighter", "faction": "Scum and Villainy", "ship_icon": "rogueclassstarfighter"
        }
    }
    
    for pid, pdata in MANUAL_PILOT_DATA.items():
        if pid not in all_pilots:
            all_pilots[pid] = pdata

    return all_pilots

def get_pilot_info(xws_pilot: str, source: DataSource = DataSource.XWA) -> dict | None:
    """Get full pilot info from XWS ID."""
    pilots = load_all_pilots(source)
    return pilots.get(xws_pilot)

def get_pilot_name(xws_pilot: str) -> str:
    """Get human-readable pilot name from XWS ID (uses Default XWA source for name lookup)."""
    pilots = load_all_pilots()
    pilot = pilots.get(xws_pilot)
    return pilot["name"] if pilot else xws_pilot

def get_pilot_image(xws_pilot: str, source: DataSource = DataSource.XWA) -> str:
    """Get pilot card image URL from XWS ID."""
    pilot = get_pilot_info(xws_pilot, source)
    return pilot.get("image", "") if pilot else ""

def search_pilot(query: str) -> list[dict]:
    """Search pilots by name or XWS ID (partial match). Uses XWA default."""
    pilots = load_all_pilots()
    query_lower = query.lower()
    
    results = []
    for xws_id, pilot in pilots.items():
        if query_lower in xws_id.lower() or query_lower in pilot["name"].lower():
            results.append({"xws": xws_id, **pilot})
    
    return results[:20]
