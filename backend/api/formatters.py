from .schemas import ListData, PilotData, UpgradeData
from ..utils.xwing_data.pilots import get_pilot_info
from ..utils.xwing_data.ships import get_ship_icon_name
from ..utils.xwing_data.upgrades import get_upgrade_info, get_upgrade_slot
from ..data_structures.factions import Faction

from ..data_structures.data_source import DataSource

def enrich_list_data(stats: dict, source: DataSource = DataSource.XWA) -> ListData:
    pilots = stats.get("pilots", [])
    rich_pilots = []
    
    total_loadout = 0
    calculated_points = 0
    
    for p in pilots:
        pid = p.get("id") or p.get("name")
        pilot_info = get_pilot_info(pid, source=source) or {}
        
        pilot_name = pilot_info.get("name", pid)
        ship_xws = pilot_info.get("ship_xws", "")
        ship_name = pilot_info.get("ship", "Unknown Ship")
        ship_icon_name = get_ship_icon_name(ship_xws)
        pilot_image = pilot_info.get("image", "")
        
        # Prioritize external_data cost over DB cost if available
        pilot_points_raw = pilot_info.get("cost", p.get("points", 0))
        pilot_loadout_raw = pilot_info.get("loadout", 0)
        
        try: pilot_points = int(pilot_points_raw)
        except (ValueError, TypeError): pilot_points = 0
            
        try: pilot_loadout = int(pilot_loadout_raw)
        except (ValueError, TypeError): pilot_loadout = 0
            
        total_loadout += pilot_loadout
        calculated_points += pilot_points
        
        rich_upgrades = []
        upgrades_data = p.get("upgrades", {})
        
        if isinstance(upgrades_data, dict):
            for slot, items in upgrades_data.items():
                if not isinstance(items, list): continue
                for item_id in items:
                    upg_info = get_upgrade_info(item_id, source=source) or {}
                    norm_slot = slot.lower()
                    if norm_slot == "configuration": norm_slot = "config"
                    
                    # Prioritize external_data cost
                    upg_cost = upg_info.get("cost")
                    if isinstance(upg_cost, dict):
                        upg_cost = upg_cost.get("value", 0)
                    
                    try: upg_cost = int(upg_cost or 0)
                    except: upg_cost = 0
                    
                    if source == DataSource.LEGACY:
                        calculated_points += upg_cost

                    rich_upgrades.append(UpgradeData(
                        xws=item_id,
                        slot_xws=norm_slot
                    ))
        elif isinstance(upgrades_data, list):
            for item_id in upgrades_data:
                upg_info = get_upgrade_info(item_id, source=source) or {}
                slot = get_upgrade_slot(item_id)
                norm_slot = slot.lower()
                if norm_slot == "configuration": norm_slot = "config"
                
                # Prioritize external_data cost
                upg_cost = upg_info.get("cost")
                if isinstance(upg_cost, dict):
                    upg_cost = upg_cost.get("value", 0)
                
                try: upg_cost = int(upg_cost or 0)
                except: upg_cost = 0
                
                if source == DataSource.LEGACY:
                    calculated_points += upg_cost

                rich_upgrades.append(UpgradeData(
                    xws=item_id,
                    slot_xws=norm_slot
                ))
        
        rich_pilots.append(PilotData(
            xws=pid,
            ship_xws=ship_xws,
            faction_xws=pilot_info.get("faction", ""),
            upgrades=rich_upgrades
        ))
    
    f_key = stats.get("faction", "unknown")

    try: points = int(stats.get("points", 0))
    except (ValueError, TypeError): points = 0
    
    try: count = int(stats.get("popularity", 0))
    except (ValueError, TypeError): count = 0
    
    try: games = int(stats.get("games", 0))
    except (ValueError, TypeError): games = 0
    
    try: win_rate = float(stats.get("win_rate", 0.0))
    except (ValueError, TypeError): win_rate = 0.0

    return ListData(
        signature=stats.get("signature", "Unknown Signature") or "Unknown Signature",
        name=stats.get("name", "Unknown List") or "Unknown List",
        faction=f_key,
        faction_key=f_key,
        faction_xws=stats.get("faction_xws", f_key),
        points=calculated_points,
        original_points=points,
        count=count,
        games=games,
        win_rate=win_rate,
        total_loadout=total_loadout,
        pilots=rich_pilots
    )
