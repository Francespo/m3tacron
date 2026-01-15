"""
X-Wing Data Helper - Access xwing-data2 for pilot/faction/ship information.

Data source: https://github.com/guidokessels/xwing-data2 (cloned as submodule)
"""
import json
from pathlib import Path
from functools import lru_cache


# Path to xwing-data2 data directory
# Structure: m3tacron/backend/xwing_data.py -> go up to m3tacron/ then into data/
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "xwing-data2" / "data"


@lru_cache(maxsize=1)
def load_factions() -> dict:
    """Load faction data. Returns dict mapping xws ID to faction info."""
    factions_file = DATA_DIR / "factions" / "factions.json"
    if not factions_file.exists():
        return {}
    
    with open(factions_file, "r", encoding="utf-8") as f:
        factions = json.load(f)
    
    return {f["xws"]: f for f in factions}


@lru_cache(maxsize=1)
def load_all_pilots() -> dict:
    """Load all pilots from all factions. Returns dict mapping xws ID to pilot info."""
    pilots_dir = DATA_DIR / "pilots"
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
                            "ship_icon": ship_icon,
                            "faction": faction,
                            "image": pilot.get("image", ""),
                            "artwork": pilot.get("artwork", ""),
                            "initiative": pilot.get("initiative", 0),
                            "cost": pilot.get("cost", 0),
                        }
            except Exception:
                continue
    
    return all_pilots


def get_faction_name(xws_faction: str) -> str:
    """Get human-readable faction name from XWS ID."""
    factions = load_factions()
    faction = factions.get(xws_faction.lower().replace(" ", ""))
    return faction["name"] if faction else xws_faction


def get_faction_icon(xws_faction: str) -> str:
    """Get faction icon URL from XWS ID."""
    factions = load_factions()
    faction = factions.get(xws_faction.lower().replace(" ", ""))
    return faction.get("icon", "") if faction else ""


def get_pilot_name(xws_pilot: str) -> str:
    """Get human-readable pilot name from XWS ID."""
    pilots = load_all_pilots()
    pilot = pilots.get(xws_pilot)
    return pilot["name"] if pilot else xws_pilot


def get_pilot_info(xws_pilot: str) -> dict | None:
    """Get full pilot info from XWS ID."""
    pilots = load_all_pilots()
    return pilots.get(xws_pilot)


def get_pilot_image(xws_pilot: str) -> str:
    """Get pilot card image URL from XWS ID."""
    pilot = get_pilot_info(xws_pilot)
    return pilot.get("image", "") if pilot else ""


def search_pilot(query: str) -> list[dict]:
    """Search pilots by name or XWS ID (partial match)."""
    pilots = load_all_pilots()
    query_lower = query.lower()
    
    results = []
    for xws_id, pilot in pilots.items():
        if query_lower in xws_id.lower() or query_lower in pilot["name"].lower():
            results.append({"xws": xws_id, **pilot})
    
    return results[:20]  # Limit results


# Pre-built faction name mapping for common XWS IDs
FACTION_NAMES = {
    "rebelalliance": "Rebel Alliance",
    "galacticempire": "Galactic Empire",
    "scumandvillainy": "Scum and Villainy",
    "resistance": "Resistance",
    "firstorder": "First Order",
    "galacticrepublic": "Galactic Republic",
    "separatistalliance": "Separatist Alliance",
}


@lru_cache(maxsize=1)
def load_all_upgrades() -> dict:
    """Load all upgrades. Returns dict mapping xws ID to upgrade info."""
    upgrades_dir = DATA_DIR / "upgrades"
    if not upgrades_dir.exists():
        return {}
    
    all_upgrades = {}
    
    for upgrade_file in upgrades_dir.glob("*.json"):
        try:
            with open(upgrade_file, "r", encoding="utf-8") as f:
                type_data = json.load(f)
            
            for upgrade in type_data:
                xws_id = upgrade.get("xws", "")
                if xws_id:
                    all_upgrades[xws_id] = {
                        "name": upgrade.get("name", xws_id),
                        "type": upgrade_file.stem.capitalize(), # e.g. "talent" -> "Talent"
                        "image": upgrade.get("image", ""),
                        "cost": upgrade.get("cost", {}).get("value", 0) if isinstance(upgrade.get("cost"), dict) else 0,
                    }
        except Exception:
            continue
            
    return all_upgrades


def get_upgrade_name(xws_upgrade: str) -> str:
    """Get human-readable upgrade name from XWS ID."""
    upgrades = load_all_upgrades()
    upgrade = upgrades.get(xws_upgrade)
    return upgrade["name"] if upgrade else xws_upgrade


def parse_xws(xws: dict) -> dict:
    """
    Parse generic XWS JSON into a rich structure with readable names.
    Returns:
    {
        "faction": "Rebel Alliance",
        "points": 20,
        "pilots": [
            {
                "name": "Luke Skywalker",
                "ship": "X-wing",
                "points": 6,
                "upgrades": [
                    {"type": "Talent", "name": "Instinctive Aim", "xws": "instinctiveaim"}
                ]
            }
        ]
    }
    """
    if not xws or not isinstance(xws, dict):
        return {}
        
    faction_raw = xws.get("faction", "")
    faction_name = get_faction_name(normalize_faction(faction_raw))
    
    output = {
        "faction": faction_name,
        "points": xws.get("points", 0),
        "pilots": []
    }
    
    total_points = 0
    
    pilots_data = xws.get("pilots", [])
    for p in pilots_data:
        p_xws = p.get("id") or p.get("name")
        if not p_xws: continue
        
        pilot_info = get_pilot_info(p_xws)
        pilot_name = pilot_info["name"] if pilot_info else p_xws
        ship_name = pilot_info.get("ship", "Unknown Ship") if pilot_info else "Unknown Ship"
        
        # Calculate points (simplified, ideally usage cost tables but usually provided in XWS or specific metadata which we might lack here)
        # For now, we rely on what we can get or just base costs
        pst_points = p.get("points", 0)
        if pst_points == 0 and pilot_info:
             pst_points = pilot_info.get("cost", 0)

        
        processed_upgrades = []
        upgrades_raw = p.get("upgrades", {})
        for u_type, u_list in upgrades_raw.items():
            for u_xws in u_list:
                u_name = get_upgrade_name(u_xws)
                processed_upgrades.append({
                    "type": u_type.capitalize(),
                    "name": u_name,
                    "xws": u_xws
                })
        
        output["pilots"].append({
            "name": pilot_name,
            "ship": ship_name,
            "points": pst_points,
            "upgrades": processed_upgrades
        })
        total_points += pst_points
        
    if output["points"] == 0:
        output["points"] = total_points
        
    return output


def normalize_faction(faction_str: str) -> str:
    """Normalize faction string to standard XWS format."""
    if not faction_str:
        return ""
    
    normalized = faction_str.lower().replace(" ", "").replace("-", "")
    
    # Map to standard XWS ID
    mapping = {
        "rebel": "rebelalliance",
        "rebels": "rebelalliance",
        "empire": "galacticempire",
        "imperial": "galacticempire",
        "scum": "scumandvillainy",
        "republic": "galacticrepublic",
        "separatist": "separatistalliance",
        "cis": "separatistalliance",
    }
    
    return mapping.get(normalized, normalized)
