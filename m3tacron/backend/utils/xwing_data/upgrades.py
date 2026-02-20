import json
from functools import lru_cache
from ...data_structures.data_source import DataSource
from .core import get_data_dir

@lru_cache(maxsize=4)
def load_all_upgrades(source: DataSource = DataSource.XWA) -> dict:
    """Load all upgrades. Returns dict mapping xws ID to upgrade info."""
    data_dir = get_data_dir(source)
    upgrades_dir = data_dir / "upgrades"
    
    if not upgrades_dir.exists():
        return {}
    
    all_upgrades = {}
    
    for upgrade_file in upgrades_dir.glob("*.json"):
        try:
            with open(upgrade_file, "r", encoding="utf-8") as f:
                upgrades_list = json.load(f)
            
            for upgrade in upgrades_list:
                xws_id = upgrade.get("xws", "")
                if xws_id:
                    # Enrich with slot info from filename or default?
                    # Upgrades in xwing-data2 are in files named by slot (e.g. talent.json)
                    # But the upgrade object inside has "sides" -> "slots".
                    # However, typical usage needs a primary slot.
                    # Filename stem is a good proxy for slot category.
                    slot_category = upgrade_file.stem
                    
                    all_upgrades[xws_id] = {
                        "name": upgrade.get("name", xws_id),
                        "xws": xws_id,
                        "sides": upgrade.get("sides", []),
                        "cost": upgrade.get("cost", {}),
                        "limited": upgrade.get("limited", 0),
                        "slot_category": slot_category, # Normalized slot name
                        "valid_in_standard": upgrade.get("standard", False) or upgrade.get("extended", False),
                        "wildspace": upgrade.get("wildspace", False),
                        "epic": upgrade.get("epic", False),
                        "image": upgrade.get("image") or (upgrade.get("sides", [{}])[0].get("image") if upgrade.get("sides") else ""),
                        "artwork": upgrade.get("artwork") or (upgrade.get("sides", [{}])[0].get("artwork") if upgrade.get("sides") else ""),
                    }
        except Exception:
            continue
            
    return all_upgrades

def get_upgrade_info(xws_upgrade: str, source: DataSource = DataSource.XWA) -> dict | None:
    """Get full upgrade info from XWS ID."""
    upgrades = load_all_upgrades(source)
    return upgrades.get(xws_upgrade)

def get_upgrade_name(xws_upgrade: str) -> str:
    """Get human-readable upgrade name from XWS ID (uses Default XWA source)."""
    upgrades = load_all_upgrades()
    upgrade = upgrades.get(xws_upgrade)
    return upgrade["name"] if upgrade else xws_upgrade

def get_upgrade_slot(xws_upgrade: str) -> str:
    """Get the primary slot name for an upgrade XWS ID."""
    upgrades = load_all_upgrades()
    upgrade = upgrades.get(xws_upgrade)
    if not upgrade:
        return "unknown"
    
    # Try to determine slot from sides if available, or fallback to file category
    sides = upgrade.get("sides", [])
    if sides and len(sides) > 0:
        slots = sides[0].get("slots", [])
        if slots:
            return slots[0] # Return the first slot as primary
            
    return upgrade.get("slot_category", "unknown")
