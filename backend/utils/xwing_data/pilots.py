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
                ship_size = ship_data.get("size", "Small")
                
                # Parse ship-level stats from stats array
                ship_stats_raw = ship_data.get("stats", [])
                stats_flat = {}
                for s_entry in ship_stats_raw:
                    stat_type = s_entry.get("type")
                    if stat_type in ("hull", "shields", "agility"):
                        stats_flat[stat_type] = s_entry.get("value", 0)
                    elif stat_type == "attack":
                        # Take max attack value if multiple arcs
                        stats_flat["attack"] = max(stats_flat.get("attack", 0), s_entry.get("value", 0))
                
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
                            "loadout": pilot.get("loadout", 0),
                            "ability": pilot.get("ability", ""),
                            # Ship stats for filtering
                            "hull": stats_flat.get("hull"),
                            "shields": stats_flat.get("shields"),
                            "agility": stats_flat.get("agility"),
                            "attack": stats_flat.get("attack"),
                            "size": ship_size,
                            "limited": pilot.get("limited", 0),
                            # Formats
                            "valid_in_standard": pilot.get("standard", False) or pilot.get("extended", False),
                            "wildspace": pilot.get("wildspace", False),
                            "epic": pilot.get("epic", False),
                        }
            except Exception:
                continue
    return all_pilots

PACK_SUFFIXES = [
    "-armedanddangerous",
    "-evacuationofdqar",
    "-battleoverendor",
    "-battleofyavin",
    "-siegeofcoruscant",
    "-alphastrike",
    "-lsl",
]

def get_pilot_info(xws_pilot: str, source: DataSource = DataSource.XWA) -> dict | None:
    """Get full pilot info from XWS ID."""
    pilots = load_all_pilots(source)
    if xws_pilot in pilots:
        return pilots[xws_pilot]

    # Try fallback stripping of pack/variant suffixes
    clean_id = xws_pilot
    for suf in PACK_SUFFIXES:
        if clean_id.endswith(suf):
            clean_id = clean_id[:-len(suf)]
    
    if clean_id in pilots:
        base_p = pilots[clean_id]
        return {**base_p, "xws": xws_pilot}

    return None

def get_pilot_name(xws_pilot: str) -> str:
    """Get human-readable pilot name from XWS ID (uses Default XWA source for name lookup)."""
    pilot = get_pilot_info(xws_pilot)
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
