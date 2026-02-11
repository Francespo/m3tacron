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
from ..data_structures.sorting_order import SortingCriteria, SortDirection

def aggregate_card_stats(
    filters: dict,
    sort_criteria: SortingCriteria = SortingCriteria.POPULARITY,
    sort_direction: SortDirection = SortDirection.DESCENDING,
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
        
        # Pre-process filters for optimization
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
        
        allowed_ships = set()
        if ship_filter and ship_filter != "all":
            if isinstance(ship_filter, list):
                allowed_ships = set(ship_filter)
            else:
                 parts = [s.strip().lower() for s in ship_filter.split(",") if s.strip()]
                 pass

        allowed_factions = set()
        if faction_filter and faction_filter != "all":
             if isinstance(faction_filter, list):
                 allowed_factions = set(faction_filter)
             else:
                 allowed_factions = {faction_filter}
        
        allowed_types = set()
        if type_filter and type_filter != "all":
            if isinstance(type_filter, list):
                allowed_types = set(t.lower() for t in type_filter)
            else:
                allowed_types = {type_filter.lower()}

        # Advanced Filters
        points_min = filters.get("points_min", 0)
        points_max = filters.get("points_max", 200)
        loadout_min = filters.get("loadout_min", 0)
        loadout_max = filters.get("loadout_max", 99)
        
        hull_min = filters.get("hull_min", 0)
        hull_max = filters.get("hull_max", 20)
        
        shields_min = filters.get("shields_min", 0)
        shields_max = filters.get("shields_max", 20)
        
        agility_min = filters.get("agility_min", 0)
        agility_max = filters.get("agility_max", 10)
        
        attack_min = filters.get("attack_min", 0)
        attack_max = filters.get("attack_max", 10)
        
        init_min = filters.get("init_min", 0)
        init_max = filters.get("init_max", 8)
        
        if init_min is not None:
            try: init_min = int(init_min)
            except: init_min = 0
        if init_max is not None:
             try: init_max = int(init_max)
             except: init_max = 8

        # Limited/Unique filters
        is_unique = filters.get("is_unique", False)  # limited == 1
        is_limited = filters.get("is_limited", False)  # limited != 0
        is_not_limited = filters.get("is_not_limited", False)  # limited == 0
        
        # Base Size filter: dict of size -> bool
        base_sizes = filters.get("base_sizes", {})

        # Location Filters
        filter_continents = filters.get("continent", None)
        filter_countries = filters.get("country", None)
        filter_cities = filters.get("city", None)
        
        allowed_continents = set(filter_continents) if filter_continents else set()
        allowed_countries = set(filter_countries) if filter_countries else set()
        allowed_cities = set(filter_cities) if filter_cities else set()

        # INITIALIZE STATS WITH ALL CARDS
        # This ensures we show cards with 0 usage.
        if mode == "pilots":
            for pid, p_info in all_pilots.items():
                try:
                    p_cost = int(p_info.get("cost", 0) or 0)
                except (ValueError, TypeError):
                    p_cost = 0
                    
                try:
                    p_loadout = int(p_info.get("loadout", 0) or 0)
                except (ValueError, TypeError):
                    p_loadout = 0
                
                # --- Advanced Numeric Filters ---
                if p_cost < points_min or p_cost > points_max:
                    continue
                    
                if data_source == DataSource.XWA:
                    if p_loadout < loadout_min or p_loadout > loadout_max:
                        continue
                        
                # Ship Stats Filters
                # Use safe default for filter checks
                # Default Logic: Show if standard OR extended OR wildspace is True.
                # If include_epic is True, show if epic is True (regardless of others).
                # If include_epic is False, DO NOT show if ONLY epic is True.
                
                is_std = p_info.get("standard", False)
                is_ext = p_info.get("extended", False)
                is_wild = p_info.get("wildspace", False)
                is_epic = p_info.get("epic", False)
                
                include_epic_content = filters.get("include_epic", False)

                # Strict Format Visibility Filter
                is_std = p_info.get("standard", False)
                is_ext = p_info.get("extended", False)
                is_wild = p_info.get("wildspace", False)
                is_epic = p_info.get("epic", False)
                
                show_card = False
                
                # Check against allowed formats from filter
                # allowed_formats contains strings from Format enum (e.g. 'xwa', 'amg', 'wildspace')
                if allowed_formats:
                     # 2.5 / Standard / Extended Logic
                     # 'xwa' and 'amg' usually imply Standard/Extended legality
                     if "xwa" in allowed_formats or "amg" in allowed_formats:
                         if is_std or is_ext:
                             show_card = True
                             
                     # Wild Space
                     if "wildspace" in allowed_formats and is_wild:
                         show_card = True
                         
                     # Epic
                     if ("xwa_epic" in allowed_formats or "legacy_epic" in allowed_formats) and is_epic:
                         show_card = True

                     # Legacy Logic (Fallthrough for Legacy Data Source)
                     if data_source == DataSource.LEGACY:
                         # Assume legacy cards are valid if legacy formats are selected
                         legacy_keys = {"legacy_x2po", "legacy_xlc", "ffg"}
                         if not legacy_keys.isdisjoint(allowed_formats):
                             show_card = True
                else:
                    # No formats selected? Should imply showing nothing? 
                    # Or fallback to showing everything? 
                    # Ideally nothing.
                    pass 

                if not show_card:
                    continue

                # Checking hypothetical structure. If keys missing, we skip filter or default to 0.
                # Based on typical xwing-data2, stats are usually under 'ship' -> 'stats'.
                # But 'load_all_pilots' helper might flatten.
                # Let's assume standard xwing-data2 pilot json structure if not flattened:
                # But we are iterating `all_pilots` which is a processed dict.
                # Safe bet: check if keys exist, else skip filter (or fail open).
                # Actually, Hull/Shields/Agility are SHIP properties.
                
                # We need to ensure we can access these.
                # If `load_all_pilots` doesn't provide them, we might be in trouble.
                # See `utils.py` logic later if needed. For now assume they are available or accessible.
                # Try to access them as top level or 'stats' dict.
                
                # Ship stats (now flattened in pilots.py)
                try: p_hull = int(p_info.get("hull") or 0)
                except: p_hull = 0
                
                try: p_shields = int(p_info.get("shields") or 0)
                except: p_shields = 0
                
                try: p_agility = int(p_info.get("agility") or 0)
                except: p_agility = 0
                
                try: p_attack = int(p_info.get("attack") or 0)
                except: p_attack = 0
                
                p_size = p_info.get("size", "Small")
                p_limited = p_info.get("limited", 0)
                
                # Stat range filters (skip if value is None)
                if p_hull < hull_min or p_hull > hull_max: continue
                if p_shields < shields_min or p_shields > shields_max: continue
                if p_agility < agility_min or p_agility > agility_max: continue
                if p_attack < attack_min or p_attack > attack_max: continue
                
                # Initiative Range Filter (replaces grid)
                p_init = p_info.get("initiative", 0)
                if p_init < init_min or p_init > init_max:
                    continue
                
                # Base Size Filter
                # Only filter if at least one size is explicitly set to True
                active_sizes = [s for s, v in base_sizes.items() if v]
                if active_sizes:
                    # Normalize size comparison
                    size_map = {"S": "Small", "M": "Medium", "L": "Large", "H": "Huge"}
                    allowed_sizes = {size_map.get(s, s) for s in active_sizes}
                    if p_size not in allowed_sizes:
                        continue
                
                # Limited/Unique Filters
                # is_unique: limited == 1
                # is_limited: limited > 1 (2 or 3)
                # is_not_limited: limited == 0 (generic)
                # If multiple are checked, treat as OR (additive)
                if is_unique or is_limited or is_not_limited:
                    match = False
                    if is_unique and p_limited == 1:
                        match = True
                    if is_limited and p_limited > 1:
                        match = True
                    if is_not_limited and p_limited == 0:
                        match = True
                    if not match:
                        continue


                # Apply Static Filters (Faction, Ship, Initiative, Text) at initialization
                
                # Faction Filter
                if allowed_factions:
                    p_faction = p_info.get("faction", "")
                    # Robust check: normalize both
                    p_f_norm = p_faction.lower().replace(" ", "").replace("-", "")
                    allowed_norm = {f.lower().replace(" ", "").replace("-", "") for f in allowed_factions}
                    
                    if p_f_norm not in allowed_norm:
                        continue

                # Ship Filter
                p_ship_xws = p_info.get("ship_xws", "")
                if allowed_ships and p_ship_xws not in allowed_ships:
                     continue
                
                # Legacy String Search Ship Filter
                if isinstance(ship_filter, str) and ship_filter and ship_filter != "all":
                    p_ship_name = p_info.get("ship", "").lower()
                    terms = [s.strip().lower() for s in ship_filter.split(",") if s.strip()]
                    match_ship = False
                    for term in terms:
                        if term in p_ship_name:
                            match_ship = True
                            break
                    if not match_ship: continue

                # Initiative Filter (legacy grid support - skip if using range)
                # Range filter already applied above, this is for backwards compat if grid is used
                if allowed_initiatives:
                    p_init_check = p_info.get("initiative")
                    if p_init_check not in allowed_initiatives:
                        continue

                # Text Filter
                if text_filter:
                    p_name = p_info.get("name", pid).lower()
                    p_ability = p_info.get("ability", "").lower()
                    p_ship_name = p_info.get("ship", "").lower()
                    p_caption = p_info.get("caption", "").lower()
                    
                    match = (text_filter in p_name) or \
                            (text_filter in p_ability) or \
                            (text_filter in p_ship_name) or \
                            (text_filter in p_caption)
                    if not match: continue

                stats[pid] = {
                    "name": p_info.get("name", pid),
                    "xws": pid,
                    "count": 0, "wins": 0, "games": 0,
                    "faction": p_info.get("faction", ""), 
                    "ship": p_info.get("ship", ""),
                    "ship_icon": p_info.get("ship_icon", ""),
                    "image": p_info.get("image", ""),
                    "cost": p_info.get("cost", 0),
                    "loadout": p_info.get("loadout", 0)
                }
        
        elif mode == "upgrades":
             for u_xws, u_info in all_upgrades.items():
                
                try:
                    u_cost = int(u_info.get("cost", 0) or 0)
                except (ValueError, TypeError):
                    u_cost = 0

                if u_cost < points_min or u_cost > points_max:
                    continue
            
                # --- Faction Filter (New) ---
                if allowed_factions:
                    # Extract factions from restrictions
                    u_restrictions = u_info.get("restrictions", [])
                    u_factions = set()
                    for r in u_restrictions:
                        if "factions" in r:
                            # Normalize factions in restrictions just in case
                            for f in r["factions"]:
                                u_factions.add(f.lower().replace(" ", "").replace("-", ""))
                    
                    # Logic: 
                    # If "unrestricted" is in allowed_factions, match if u_factions is EMPTY.
                    # If specific factions are in allowed_factions, match if intersection with u_factions is NOT EMPTY.
                    # Behavior is usually OR (e.g. show "Rebel" OR "Unrestricted" upgrades)
                    
                    match_faction = False
                    
                    # Check Unrestricted (No faction restrictions)
                    if "unrestricted" in allowed_factions:
                        if not u_factions:
                            match_faction = True
                            
                    # Check Specific Factions
                    # allowed_factions contains normalized strings from frontend (usually)
                    # We need to ensure allowed_factions are normalized to match u_factions
                    if not match_faction:
                        # Filter out "unrestricted" to check actual factions
                        real_allowed = {f for f in allowed_factions if f != "unrestricted"}
                        if not u_factions.isdisjoint(real_allowed):
                            match_faction = True
                            
                    if not match_faction:
                        continue


                # Strict Format Visibility Filter (Upgrades)
                is_std = u_info.get("standard", False)
                is_ext = u_info.get("extended", False)
                is_wild = u_info.get("wildspace", False)
                is_epic = u_info.get("epic", False)
                
                show_card = False
                
                # Check against allowed formats
                if allowed_formats:
                     if "xwa" in allowed_formats or "amg" in allowed_formats:
                         if is_std or is_ext:
                             show_card = True
                             
                     if "wildspace" in allowed_formats and is_wild:
                         show_card = True
                         
                     if ("xwa_epic" in allowed_formats or "legacy_epic" in allowed_formats) and is_epic:
                         show_card = True

                     if data_source == DataSource.LEGACY:
                         legacy_keys = {"legacy_x2po", "legacy_xlc", "ffg"}
                         if not legacy_keys.isdisjoint(allowed_formats):
                             show_card = True
                else:
                    pass 

                if not show_card:
                    continue
                
                # NOTE: all_upgrades from legacy xwing-data2 usually has 'sides' list with 'type'.
                types = set()
                sides = u_info.get("sides", [])
                if sides and isinstance(sides, list):
                    for side in sides:
                        if "type" in side:
                            types.add(side["type"].lower())
                else:
                    # Fallback if flat structure
                    if "type" in u_info:
                        types.add(u_info["type"].lower())

                if allowed_types:
                    if types.isdisjoint(allowed_types):
                        continue

                # Text Filter
                if text_filter:
                    u_name = u_info.get("name", u_xws).lower()
                    u_text = ""
                    # aggregating text from sides
                    if sides:
                        for side in sides:
                            u_text += " " + side.get("ability", "").lower()
                    else:
                        u_text = u_info.get("text", "").lower()

                    match = (text_filter in u_name) or (text_filter in u_text)
                    if not match: continue

                # Resolve display type (use first match or default)
                display_type = list(types)[0].title() if types else "Unknown"

                stats[u_xws] = {
                    "name": u_info.get("name", u_xws),
                    "xws": u_xws,
                    "type": display_type,
                    "count": 0, "wins": 0, "games": 0,
                    "image": u_info.get("image", ""),
                    "cost": u_info.get("cost", 0)
                }

        for result, tournament in rows:
            # Python-level Filtering
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            if allowed_formats is not None: 
                if t_fmt not in allowed_formats:
                    continue

            # Location Filtering
            if allowed_continents or allowed_countries or allowed_cities:
                loc = tournament.location
                if not loc:
                    continue
                
                if allowed_continents and (not loc.continent or loc.continent not in allowed_continents):
                    continue
                    
                if allowed_countries and (not loc.country or loc.country not in allowed_countries):
                    continue
                    
                if allowed_cities and (not loc.city or loc.city not in allowed_cities):
                    continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            
            # Process List
            # wins = swiss_wins + (cut_wins or 0)
            # games = (swiss_wins + swiss_losses + swiss_draws) + (cut_wins + cut_losses + cut_draws or 0)
            
            s_wins = result.swiss_wins or 0
            s_losses = result.swiss_losses or 0
            s_draws = result.swiss_draws or 0
            
            c_wins = result.cut_wins or 0
            c_losses = result.cut_losses or 0
            c_draws = result.cut_draws or 0
            
            wins = s_wins + c_wins
            games = wins + s_losses + c_losses + s_draws + c_draws

            
            if mode == "pilots":
                list_faction = xws.get("faction", "unknown")
                
                # Faction check for LIST context (already handled for individual stats init)
                # But we must only process lists that match the faction filter to count usage correctly?
                # Actually, if we filter by Faction X, we only want usage in Faction X lists?
                # Usually YES.
                if allowed_factions:
                    current_faction = Faction.from_xws(list_faction).value
                    if current_faction not in allowed_factions:
                        continue
                
                for p in xws.get("pilots", []):
                    pid = p.get("id") or p.get("name")
                    if not pid: continue
                    
                    # Context Filter: Upgrade ID
                    if filter_upgrade_id:
                        has_upgrade = False
                        upgrades = p.get("upgrades", {}) or {}
                        for u_list in upgrades.values():
                            if filter_upgrade_id in u_list:
                                has_upgrade = True
                                break
                        if not has_upgrade:
                            continue

                    # If pid is in stats, update it
                    if pid in stats:
                        s = stats[pid]
                        s["count"] += 1
                        s["wins"] += wins
                        s["games"] += games
                    else:
                        # This implies it wasn't in all_pilots OR it was filtered out by static filters.
                        # If it was filtered out, we shouldn't count it.
                        # If it wasn't in all_pilots (unknown card?), we ignore it to be safe (or add it?)
                        # We ignore it to enforce using valid data.
                        pass
                    
            elif mode == "upgrades":
                for p in xws.get("pilots", []):
                    pid = p.get("id") or p.get("name")
                    
                    # Context Filter: Pilot ID
                    if filter_pilot_id:
                        if pid != filter_pilot_id:
                            continue
                    
                    upgrades = p.get("upgrades", {}) or {}
                    
                    # Context Filter: Upgrade ID (Paired)
                    if filter_upgrade_id:
                        has_target_upgrade = False
                        for u_list in upgrades.values():
                            if filter_upgrade_id in u_list:
                                has_target_upgrade = True
                                break
                        if not has_target_upgrade:
                            continue

                    for u_type, u_list in upgrades.items():
                         # We don't filter by u_type here rigidly if the card exists in stats 
                         # (because stats init handled type logic).
                         # But checking helps optimization.
                        if allowed_types and u_type.lower() not in allowed_types:
                             continue
                            
                        for u_xws in u_list:
                            if filter_upgrade_id and u_xws == filter_upgrade_id:
                                continue

                            if u_xws in stats:
                                s = stats[u_xws]
                                s["count"] += 1
                                s["wins"] += wins
                                s["games"] += games

        # Post-Processing
        results = []
        for xws_id, s_data in stats.items():
            if s_data["games"] > 0:
                win_rate = (s_data["wins"] / s_data["games"]) * 100
                s_data["win_rate"] = round(win_rate, 1)
            else:
                s_data["win_rate"] = "NA" # String sentinel for UI

            # Ensure display name fallback
            if not s_data.get("name"):
                 s_data["name"] = xws_id
            
            results.append(s_data)
            
        # Sorting
        reverse = (sort_direction == SortDirection.DESCENDING)
        
        # Helper for NA winrate
        def winrate_sort_key(x):
            wr = x["win_rate"]
            if wr == "NA":
                return -1.0 # Treat as lowest
            return float(wr)

        if sort_criteria == SortingCriteria.WINRATE:
            results.sort(key=lambda x: (winrate_sort_key(x), x["games"]), reverse=reverse)
        elif sort_criteria == SortingCriteria.COST:
             results.sort(key=lambda x: (x["cost"], x["count"]), reverse=reverse)
        elif sort_criteria == SortingCriteria.GAMES:
             results.sort(key=lambda x: x["games"], reverse=reverse)
        elif sort_criteria == SortingCriteria.LOADOUT:
             results.sort(key=lambda x: (x.get("loadout", 0), x["count"]), reverse=reverse)
        elif sort_criteria == SortingCriteria.NAME:
             results.sort(key=lambda x: x["name"], reverse=reverse)
        else: # Popularity (Default)
             results.sort(key=lambda x: x["count"], reverse=reverse)
            
        return results
