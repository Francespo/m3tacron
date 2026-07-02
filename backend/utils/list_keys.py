import json
from typing import Any


def coerce_list_json(raw: Any) -> dict:
    """Return a dict for a list payload, parsing JSON strings when needed."""
    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except Exception:
            return {}
        if isinstance(parsed, dict):
            return parsed

    return {}


def get_list_key(xws: Any) -> str:
    """
    Generate a unique, canonical signature for a list based on pilots and upgrades.
    """
    xws = coerce_list_json(xws)
    if not xws:
        return ""
    
    pilots = xws.get("pilots", [])
    if not pilots:
        return ""
        
    temp_pilots = []
    for p in pilots:
        pid = p.get("id") or p.get("name") # Handle diff xws formats
        
        # Upgrades
        raw_upgrades = p.get("upgrades", {})
        u_xws_list = []
        
        if isinstance(raw_upgrades, dict):
            for slot, items in raw_upgrades.items():
                if isinstance(items, list):
                    for item in items: u_xws_list.append(str(item))
                else: u_xws_list.append(str(items))
        elif isinstance(raw_upgrades, list):
            for item in raw_upgrades: u_xws_list.append(str(item))
            
        u_xws_list.sort()
        
        temp_pilots.append({
            "xws": pid,
            "upgrades": [{"xws": u} for u in u_xws_list]
        })
        
    # Sort by pilot xws then upgrades
    temp_pilots.sort(key=lambda x: (x["xws"], str(x["upgrades"])))
    
    return json.dumps(temp_pilots, sort_keys=True)


def get_ship_list(xws: dict) -> str:
    """
    Extract sorted ship XWS list from list_json for squadron grouping.
    Returns comma-joined string like "btla4ywing,t65xwing,t65xwing".
    """
    if not xws or not isinstance(xws, dict):
        return ""
    
    pilots = xws.get("pilots", [])
    ships = []
    for p in pilots:
        ship = p.get("ship") or ""
        if ship:
            ships.append(ship)
    
    ships.sort()
    return ",".join(ships)
