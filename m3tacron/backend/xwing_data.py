"""
X-Wing Data Helper - Access xwing-data2 for pilot/faction/ship information.

Data source: https://github.com/guidokessels/xwing-data2 (cloned as submodule)
"""
import json
from pathlib import Path
from functools import lru_cache
from .enums.factions import Faction


# Path to data directories
# Structure: m3tacron/backend/xwing_data.py -> up to root -> external_data
ROOT_DIR = Path(__file__).parent.parent.parent
EXTERNAL_DATA_DIR = ROOT_DIR / "external_data"

XWA_DATA_DIR = EXTERNAL_DATA_DIR / "xwing-data2" / "data"
LEGACY_DATA_DIR = EXTERNAL_DATA_DIR / "xwing-data2-legacy" / "data"

def get_data_dir(source: str = "xwa") -> Path:
    if source.lower() == "legacy":
        return LEGACY_DATA_DIR
    return XWA_DATA_DIR


@lru_cache(maxsize=1)
def load_factions() -> dict:
    """Load faction data. Returns dict mapping xws ID to faction info."""
    # Factions are usually common, but let's default to XWA
    factions_file = XWA_DATA_DIR / "factions" / "factions.json"
    if not factions_file.exists():
        return {}
    
    with open(factions_file, "r", encoding="utf-8") as f:
        factions = json.load(f)
    
    return {f["xws"]: f for f in factions}


@lru_cache(maxsize=4)
def load_all_pilots(source: str = "xwa") -> dict:
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
    
    # Merge manual data if not already present
    for pid, pdata in MANUAL_PILOT_DATA.items():
        if pid not in all_pilots:
            all_pilots[pid] = pdata

    return all_pilots




def get_pilot_name(xws_pilot: str) -> str:
    """Get human-readable pilot name from XWS ID."""
    pilots = load_all_pilots()
    pilot = pilots.get(xws_pilot)
    return pilot["name"] if pilot else xws_pilot


def get_pilot_info(xws_pilot: str, source: str = "xwa") -> dict | None:
    """Get full pilot info from XWS ID."""
    pilots = load_all_pilots(source)
    return pilots.get(xws_pilot)


def get_pilot_image(xws_pilot: str, source: str = "xwa") -> str:
    """Get pilot card image URL from XWS ID."""
    pilot = get_pilot_info(xws_pilot, source)
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


    return results[:20]  # Limit results


@lru_cache(maxsize=4)
def load_all_upgrades(source: str = "xwa") -> dict:
    """Load all upgrades. Returns dict mapping xws ID to upgrade info."""
    data_dir = get_data_dir(source)
    upgrades_dir = data_dir / "upgrades"
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
                    # Extract text and image from sides
                    text = ""
                    image = upgrade.get("image", "")
                    sides = upgrade.get("sides", [])
                    
                    if sides:
                        # Join ability/text from all sides
                        text_parts = []
                        for side in sides:
                            if "ability" in side: text_parts.append(side["ability"])
                            if "text" in side: text_parts.append(side["text"])
                        text = " ".join(text_parts)
                        
                        # Fallback for image from first side if top-level is empty
                        if not image and len(sides) > 0:
                            image = sides[0].get("image", "")

                    all_upgrades[xws_id] = {
                        "name": upgrade.get("name", xws_id),
                        "type": upgrade_file.stem.capitalize(), # e.g. "talent" -> "Talent"
                        "image": image,
                        "cost": upgrade.get("cost", {}).get("value", 0) if isinstance(upgrade.get("cost"), dict) else 0,
                        "text": text,
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
            "xws": p_xws,  # Include XWS ID for image lookups
            "ship": ship_name,
            "points": pst_points,
            "upgrades": processed_upgrades
        })
        total_points += pst_points
        
    if output["points"] == 0:
        output["points"] = total_points
        
    return output


def normalize_faction(faction_str: str) -> str:
    return Faction.from_xws(faction_str).value
