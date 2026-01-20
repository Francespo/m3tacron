"""
Squadron signature utilities for grouping X-Wing lists (archetypes).
"""

from .xwing_data import get_pilot_info

def get_squadron_signature(xws: dict) -> str | None:
    """
    Generates a unique signature for a squadron based on its ships.
    Format: "Faction|Ship1,Ship2,Ship3" (Ships sorted alphabetically)
    Returns None if XWS is invalid.
    """
    if not xws or not isinstance(xws, dict):
        return None
        
    faction_key = xws.get("faction")
    if not faction_key:
        return None
    
    # Normalize faction name to standard key if possible, mostly relying on raw input or FACTION_NAMES lookups
    # But usually xws['faction'] is the XWS slug like 'rebelalliance'.
    # We will use the raw XWS faction slug in the signature to avoid whitespace ambiguities, or better yet, use the same key everywhere.
    # But previous system likely used human readable names? No, probably xws keys or whatever 'faction' key holds.
    # Let's check 'squadrons.py' expectation. 
    # It parses sig -> faction, ships.
    # Then `FACTION_NAMES.get(faction, faction)` suggests signature might contain the raw key.
    
    ships = []
    pilots = xws.get("pilots", [])
    if not pilots:
        return None
        
    for p in pilots:
        # Resolve ship name from pilot ID
        pid = p.get("id") or p.get("name")
        pinfo = get_pilot_info(pid)
        if pinfo:
            ships.append(pinfo.get("ship", "Unknown"))
        else:
            ships.append("Unknown")
            
    ships.sort()
    ship_str = ",".join(ships)
    return f"{faction_key}|{ship_str}"

def parse_squadron_signature(signature: str) -> tuple[str, list[str]]:
    """
    Parses a squadron signature into (faction_key, list_of_ship_names).
    """
    if "|" not in signature:
        return "unknown", []
        
    parts = signature.split("|")
    faction = parts[0]
    ships_str = parts[1]
    
    if not ships_str:
        return faction, []
        
    ships = ships_str.split(",")
    return faction, ships
