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

    # Manual patches for missing scenario upgrades. These cards ship in
    # scenario packs (Armed and Dangerous / Evacuation of D'QAR) and are
    # absent from the vendored upstream data. Base XWS ids are injected so
    # both the bare id and the "<id>-<pack>" variant resolve to a name.
    MANUAL_UPGRADE_DATA = {
        # Evacuation of D'QAR
        "acceleratedsensorarray": {"name": "Accelerated Sensor Array", "slot": "Tech"},
        "dedicatedgunners": {"name": "Dedicated Gunners", "slot": "Gunner"},
        "determination": {"name": "Determination", "slot": "Talent"},
        "escortfighter": {"name": "Escort Fighter", "slot": "Talent"},
        "forthecause": {"name": "For the Cause", "slot": "Talent"},
        "precisionholotargeter": {"name": "Precision Holotargeter", "slot": "Tech"},
        "primedoverdrivethrusters": {"name": "Primed Overdrive Thrusters", "slot": "Tech"},
        "repulsorliftengines": {"name": "Repulsorlift Engines", "slot": "Modification"},
        "targetassistalgorithm": {"name": "Target Assist Algorithm", "slot": "Tech"},
        "threatsensors": {"name": "Threat Sensors", "slot": "Tech"},
        # Armed and Dangerous
        "adaptablepowersystems": {"name": "Adaptable Power Systems", "slot": "Modification"},
        "flechettecannons": {"name": "Flechette Cannons", "slot": "Cannon"},
        "homingbeacon": {"name": "Homing Beacon", "slot": "Sensor"},
        "kinesoswitch": {"name": "Kineso Switch", "slot": "Illicit"},
        "r2g8": {"name": "R2-G8", "slot": "Astromech"},
        "starboardthrusters": {"name": "Starboard Thrusters", "slot": "Modification"},
        "synchronizedhandling": {"name": "Synchronized Handling", "slot": "Tech"},
        "todo360": {"name": "ToDo-360", "slot": "Crew"},
        "fennecshand": {"name": "Fennec Shand", "slot": "Gunner"},
    }

    for uid, udata in MANUAL_UPGRADE_DATA.items():
        if uid not in all_upgrades:
            slot = udata["slot"]
            all_upgrades[uid] = {
                "name": udata["name"],
                "xws": uid,
                "sides": [{"title": udata["name"], "type": slot, "slots": [slot]}],
                "cost": {},
                "limited": 0,
                "slot_category": slot.lower(),
                "valid_in_standard": True,
                "wildspace": False,
                "epic": False,
                "image": "",
                "artwork": "",
            }

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
