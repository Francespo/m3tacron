import json

def get_list_key(xws: dict) -> str:
    """
    Generate a unique, canonical signature for a list based on pilots and upgrades.
    """
    if not xws or not isinstance(xws, dict):
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
