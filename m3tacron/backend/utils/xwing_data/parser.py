from ...data_structures.factions import Faction
from .core import get_faction_name
from .pilots import get_pilot_info
from .upgrades import get_upgrade_name

def normalize_faction(faction_str: str) -> str:
    return Faction.from_xws(faction_str).value

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
        
        # Calculate points
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
