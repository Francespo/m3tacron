import logging

logger = logging.getLogger(__name__)

def parse_builder_url(url: str) -> dict:
    import urllib.parse
    """
    Parses a YASB or Launch Bay Next URL and returns an XWS dictionary.
    """
    if "yasb.app" in url:
        return _parse_yasb(url)
    elif "launchbaynext.app" in url:
        return _parse_lbn(url)
    return {}

def _parse_lbn(url: str) -> dict:
    return {"vendor": {"link": url}}

def _parse_yasb(url: str) -> dict:
    import urllib.parse
    try:
        from ..data_structures.factions import Faction
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        
        # d parameter holds the squad data
        d_val = params.get("d", [""])[0]
        f_val = params.get("f", ["Unknown"])[0]
        
        xws = {
            "faction": Faction.from_xws(f_val).value,
            "pilots": [],
            "vendor": {"yasb": {"link": url}}
        }
        
        return xws
    except Exception as e:
        logger.error(f"YASB Parse Error: {e}")
        return {}

def get_squadron_signature(xws: dict) -> str | None:
    from .xwing_data.pilots import get_pilot_info
    """
    Generates a unique signature for a squadron based on its ships.
    Format: "Faction|Ship1,Ship2,Ship3" (Ships sorted alphabetically)
    """
    if not xws or not isinstance(xws, dict):
        return None
        
    faction_key = xws.get("faction")
    if not faction_key:
        return None
    
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

def get_list_signature(xws: dict) -> str | None:
    from .xwing_data.pilots import get_pilot_info
    """
    Generates a unique signature for a full list (Faction + Ships + Pilots + Upgrades).
    Format: "Faction|Ship1:Pilot1:Upgrades|Ship2:Pilot2:Upgrades"
    Sorted alphabetically by ship/pilot signature to ensure consistent ordering.
    """
    if not xws or not isinstance(xws, dict):
        return None
        
    faction_key = xws.get("faction")
    if not faction_key:
        return None
        
    pilots = xws.get("pilots", [])
    if not pilots:
        return None
        
    ship_signatures = []
    
    for p in pilots:
        # Resolve ship name and pilot name
        pid = p.get("id") or p.get("name")
        pinfo = get_pilot_info(pid)
        
        ship_name = pinfo.get("ship", "Unknown") if pinfo else "Unknown"
        pilot_name = pinfo.get("name", pid) if pinfo else pid
        
        # Resolve Upgrades
        upgrades = p.get("upgrades", {})
        upgrade_list = []
        if isinstance(upgrades, dict):
            for slot, items in upgrades.items():
                if isinstance(items, list):
                    upgrade_list.extend(items)
                elif isinstance(items, str):
                    upgrade_list.append(items)
        
        # Sort upgrades to ensure consistency (e.g. "instinctive-aim, sense" == "sense, instinctive-aim")
        upgrade_list.sort()
        upgrades_str = ",".join(upgrade_list)
        
        # Specific ship signature
        ship_sig = f"{ship_name}:{pilot_name}:{upgrades_str}"
        ship_signatures.append(ship_sig)
        
    # Sort ship signatures (e.g. ensure "Luke, Wedge" == "Wedge, Luke")
    ship_signatures.sort()
    
    full_sig = "|".join(ship_signatures)
    return f"{faction_key}|{full_sig}"
