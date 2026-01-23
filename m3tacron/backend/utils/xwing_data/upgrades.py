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
                type_data = json.load(f)
            
            for upgrade in type_data:
                xws_id = upgrade.get("xws", "")
                if xws_id:
                    # Extract text and image from sides
                    text = ""
                    image = upgrade.get("image", "")
                    sides = upgrade.get("sides", [])
                    
                    if sides:
                        text_parts = []
                        for side in sides:
                            if "ability" in side: text_parts.append(side["ability"])
                            if "text" in side: text_parts.append(side["text"])
                        text = " ".join(text_parts)
                        
                        if not image and len(sides) > 0:
                            image = sides[0].get("image", "")

                    all_upgrades[xws_id] = {
                        "name": upgrade.get("name", xws_id),
                        "type": upgrade_file.stem.capitalize(), 
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
