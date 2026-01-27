"""
Card Analytics - Aggregation Logic for Pilots and Upgrades.
"""
from sqlmodel import Session, select
from ..database import engine
from ..models import PlayerResult, Tournament
from ..utils import get_pilot_name, get_upgrade_name, get_pilot_info, load_all_pilots, load_all_upgrades, load_all_ships
from ..data_structures.factions import Faction
from ..data_structures.formats import Format, MacroFormat
from ..data_structures.data_source import DataSource
from .filters import filter_query

def aggregate_card_stats(
    filters: dict,
    sort_mode: str = "popularity", # popularity, win_rate
    mode: str = "pilots", # pilots, upgrades
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for pilots or upgrades.
    """
    with Session(engine) as session:
        # Join PlayerResult and Tournament
        query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
        
        # Apply SQL-level filters (Dates)
        query = filter_query(query, filters)
        
        rows = session.exec(query).all()
        
        stats = {} # xws_id -> {counts, wins, games, faction, ...}
        
        # Pre-load Data using Source (XWA/Legacy)
        all_pilots = load_all_pilots(data_source)
        all_upgrades = load_all_upgrades(data_source)
        
        allowed_formats = filters.get("allowed_formats", None) # Set of strings
        faction_filter = filters.get("faction") # For pilots
        type_filter = filters.get("upgrade_type") # For upgrades
        text_filter = filters.get("search_text", "").lower()
        ship_filter = filters.get("ship")
        initiative_filter = filters.get("initiative")
        
        # New Context Filters
        filter_pilot_id = filters.get("pilot_id")
        if filter_pilot_id: filter_pilot_id = filter_pilot_id.strip('"').strip("'")
        
        filter_upgrade_id = filters.get("upgrade_id")
        if filter_upgrade_id: filter_upgrade_id = filter_upgrade_id.strip('"').strip("'")
        
        # Pre-process initiative filter
        allowed_initiatives = set()
        if initiative_filter and initiative_filter != "all":
            if isinstance(initiative_filter, list):
                for i_str in initiative_filter:
                    try:
                        allowed_initiatives.add(int(i_str))
                    except ValueError:
                        pass
            else:
                 try:
                     allowed_initiatives.add(int(initiative_filter))
                 except ValueError:
                     pass
        
        # Ship Filter Logic
        allowed_ships = set()
        if ship_filter and ship_filter != "all":
            if isinstance(ship_filter, list):
                allowed_ships = set(ship_filter)
            else:
                 # Legacy CSV string support
                 parts = [s.strip().lower() for s in ship_filter.split(",") if s.strip()]
                 # If usage requires handling string legacy, we keep it logic-less here or implement if needed.
                 pass

        # Faction Filter Logic
        allowed_factions = set()
        if faction_filter and faction_filter != "all":
             if isinstance(faction_filter, list):
                 allowed_factions = set(faction_filter)
             else:
                 allowed_factions = {faction_filter}
        
        # Upgrade Type Logic
        allowed_types = set()
        if type_filter and type_filter != "all":
            if isinstance(type_filter, list):
                allowed_types = set(t.lower() for t in type_filter)
            else:
                allowed_types = {type_filter.lower()}

        for result, tournament in rows:
            # Python-level Filtering
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            if allowed_formats: 
                if t_fmt not in allowed_formats:
                    continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            
            # Process List
            wins = result.swiss_wins + result.cut_wins
            games = wins + result.swiss_losses + result.cut_losses + result.swiss_draws
            
            if mode == "pilots":
                list_faction = xws.get("faction", "unknown")
                if allowed_factions:
                    current_faction = Faction.from_xws(list_faction).value
                    if current_faction not in allowed_factions:
                        continue
                
                for p in xws.get("pilots", []):
                    pid = p.get("id") or p.get("name")
                    if not pid: continue
                    
                    # Context Filter: Upgrade ID
                    # If we are looking for pilots that use a specific upgrade
                    if filter_upgrade_id:
                        has_upgrade = False
                        upgrades = p.get("upgrades", {}) or {}
                        for u_list in upgrades.values():
                            if filter_upgrade_id in u_list:
                                has_upgrade = True
                                break
                        if not has_upgrade:
                            continue

                    # Ship Filter
                    if allowed_ships:
                         p_info = all_pilots.get(pid, {})
                         p_ship_xws = p_info.get("ship_xws", "") 
                         if p_ship_xws not in allowed_ships:
                             continue
                             
                    # Legacy String Search
                    elif isinstance(ship_filter, str) and ship_filter and ship_filter != "all":
                        p_info = all_pilots.get(pid, {})
                        p_ship = p_info.get("ship", "").lower()
                        terms = [s.strip().lower() for s in ship_filter.split(",") if s.strip()]
                        match_ship = False
                        for term in terms:
                            if term in p_ship:
                                match_ship = True
                                break
                        if not match_ship: continue

                    # Initiative Filter
                    if allowed_initiatives:
                         p_info = all_pilots.get(pid, {})
                         p_init = p_info.get("initiative")
                         if p_init not in allowed_initiatives:
                             continue

                    # Search Text Filter
                    if text_filter:
                        p_info = all_pilots.get(pid, {})
                        p_name = p_info.get("name", pid).lower()
                        p_ability = p_info.get("ability", "").lower()
                        p_ship = p_info.get("ship", "").lower()
                        
                        match = (text_filter in p_name) or \
                                (text_filter in p_ability) or \
                                (text_filter in p_ship)
                            
                        if not match: continue

                    if pid not in stats:
                        p_info = all_pilots.get(pid, {})
                        stats[pid] = {
                            "name": p_info.get("name", pid),
                            "xws": pid,
                            "count": 0, "wins": 0, "games": 0,
                            "faction": p_info.get("faction", list_faction), # Pilot faction
                            "ship": p_info.get("ship", ""),
                            "ship_icon": p_info.get("ship_icon", ""),
                            "image": p_info.get("image", ""),
                            "cost": p_info.get("cost", 0)
                        }
                    
                    s = stats[pid]
                    s["count"] += 1
                    s["wins"] += wins
                    s["games"] += games
                    
            elif mode == "upgrades":
                for p in xws.get("pilots", []):
                    pid = p.get("id") or p.get("name")
                    
                    # Context Filter: Pilot ID
                    # If we are looking for upgrades on a specific pilot
                    if filter_pilot_id:
                        if pid != filter_pilot_id:
                            continue
                    
                    upgrades = p.get("upgrades", {}) or {}
                    
                    # Context Filter: Upgrade ID
                    # If we are looking for Paired Upgrades (upgrades in the same loadout as the target upgrade)
                    if filter_upgrade_id:
                        has_target_upgrade = False
                        for u_list in upgrades.values():
                            if filter_upgrade_id in u_list:
                                has_target_upgrade = True
                                break
                        if not has_target_upgrade:
                            continue

                    for u_type, u_list in upgrades.items():
                        
                        # Type Filter
                        if allowed_types and u_type.lower() not in allowed_types:
                            continue
                            
                        for u_xws in u_list:
                            # Skip self if looking for paired upgrades
                            if filter_upgrade_id and u_xws == filter_upgrade_id:
                                continue

                            # Search Text
                            if text_filter:
                                u_info = all_upgrades.get(u_xws, {})
                                u_name = u_info.get("name", u_xws).lower()
                                u_text = u_info.get("text", "").lower()

                                match = (text_filter in u_name) or (text_filter in u_text)
                                if not match: continue
                            
                            if u_xws not in stats:
                                u_info = all_upgrades.get(u_xws, {})
                                stats[u_xws] = {
                                    "name": u_info.get("name", u_xws),
                                    "xws": u_xws,
                                    "type": u_type.replace("-", " ").replace("_", " ").title(), # Format human readable label
                                    "count": 0, "wins": 0, "games": 0,
                                    "image": u_info.get("image", ""),
                                    "cost": u_info.get("cost", 0)
                                }
                            
                            s = stats[u_xws]
                            s["count"] += 1
                            s["wins"] += wins
                            s["games"] += games

        # Post-Processing
        results = []
        for xws_id, s_data in stats.items():
            if s_data["games"] > 0:
                win_rate = (s_data["wins"] / s_data["games"]) * 100
            else:
                win_rate = 0.0

            # Ensure we aren't returning raw XWS if name exists in stats
            name = s_data.get("name", xws_id)
            if not name or name == xws_id:
                # Fallback lookup if stats construction missed it
                if mode == "pilots":
                    info = all_pilots.get(xws_id, {})
                else: 
                     # mode == "upgrades" or "tech" etc.
                    info = all_upgrades.get(xws_id, {})
                name = info.get("name", xws_id)
            
            # Enrich data
            s_data["name"] = name
            s_data["win_rate"] = round(win_rate, 1)
            
            results.append(s_data)
            
        # Sorting
        if sort_mode == "win_rate":
            results.sort(key=lambda x: (x["games"] > 5, x["win_rate"], x["count"]), reverse=True)
        else: # popularity
            results.sort(key=lambda x: x["count"], reverse=True)
            
        return results
