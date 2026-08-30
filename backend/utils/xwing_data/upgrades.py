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
                    
                    # Aggregate slots / charges / force across sides for filtering
                    _sides = upgrade.get("sides", [])
                    _all_slots: list[str] = []
                    _charges_val: int | None = None
                    _charges_recovers: int = 0
                    _force_val: int | None = None
                    for _side in _sides:
                        for _slot in (_side.get("slots") or []):
                            if _slot and _slot not in _all_slots:
                                _all_slots.append(str(_slot))
                        if _charges_val is None and "charges" in _side:
                            ch = _side["charges"] or {}
                            _charges_val = int(ch.get("value", 0) or 0)
                            _charges_recovers = int(ch.get("recovers", 0) or 0)
                        if _force_val is None and "force" in _side:
                            fc = _side["force"] or {}
                            _force_val = int(fc.get("value", 0) or 0)
                    all_upgrades[xws_id] = {
                        "name": upgrade.get("name", xws_id),
                        "xws": xws_id,
                        "sides": _sides,
                        "cost": upgrade.get("cost", {}),
                        "limited": upgrade.get("limited", 0),
                        "slot_category": slot_category, # Normalized slot name
                        "slots": _all_slots,
                        "charges": {"value": _charges_val if _charges_val is not None else 0, "recovers": _charges_recovers} if _charges_val is not None else None,
                        "force": {"value": _force_val} if _force_val is not None else None,
                        "keywords": [],  # Upgrades have no keywords in xwing-data2
                        "valid_in_standard": upgrade.get("standard", False) or upgrade.get("extended", False),
                        "wildspace": upgrade.get("wildspace", False),
                        "epic": upgrade.get("epic", False),
                        "image": upgrade.get("image") or (_sides[0].get("image") if _sides else ""),
                        "artwork": upgrade.get("artwork") or (_sides[0].get("artwork") if _sides else ""),
                    }
        except Exception:
            continue

    return all_upgrades

PACK_SUFFIXES = [
    "-armedanddangerous",
    "-evacuationofdqar",
    "-battleoverendor",
    "-battleofyavin",
    "-siegeofcoruscant",
    "-alphastrike",
    "-lsl",
]

def get_upgrade_info(xws_upgrade: str, source: DataSource = DataSource.XWA) -> dict | None:
    """Get full upgrade info from XWS ID."""
    upgrades = load_all_upgrades(source)
    if not isinstance(xws_upgrade, str):
        return None
    if xws_upgrade in upgrades:
        return upgrades[xws_upgrade]

    clean_id = xws_upgrade
    for suf in PACK_SUFFIXES:
        if clean_id.endswith(suf):
            clean_id = clean_id[:-len(suf)]

    if isinstance(clean_id, str) and clean_id in upgrades:
        base_u = upgrades[clean_id]
        return {**base_u, "xws": xws_upgrade}

    return None

def get_upgrade_name(xws_upgrade: str) -> str:
    """Get human-readable upgrade name from XWS ID (uses Default XWA source)."""
    upgrade = get_upgrade_info(xws_upgrade)
    return upgrade["name"] if upgrade else xws_upgrade

def get_upgrade_slot(xws_upgrade: str) -> str:
    """Get the primary slot name for an upgrade XWS ID."""
    upgrade = get_upgrade_info(xws_upgrade)
    if not upgrade:
        return "unknown"
    
    # Try to determine slot from sides if available, or fallback to file category
    sides = upgrade.get("sides", [])
    if sides and len(sides) > 0:
        slots = sides[0].get("slots", [])
        if slots:
            return slots[0] # Return the first slot as primary
            
    return upgrade.get("slot_category", "unknown")
