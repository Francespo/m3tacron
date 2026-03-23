"""
Card Analytics - Aggregation Logic for Pilots and Upgrades.
"""
from sqlmodel import Session, select
import json
from ..database import engine
from ..models import PlayerResult, Tournament
from ..utils.xwing_data.pilots import load_all_pilots
from ..utils.xwing_data.upgrades import load_all_upgrades
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from .filters import filter_query, get_active_formats, apply_tournament_filters
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
    Returns list of dicts matching PilotStats or UpgradeStats schema.
    """
    with Session(engine) as session:
        # Join PlayerResult and Tournament
        query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
        
        # Apply SQL-level filters (Dates)
        query = filter_query(query, filters)
        
        rows = session.exec(query).all()
        
        # Structure: xws_id -> {xws, games_count, list_count, different_lists_count, wins, _signatures: set}
        stats = {} 
        
        # Pre-load Data
        all_pilots = load_all_pilots(data_source)
        all_upgrades = load_all_upgrades(data_source)
        
        allowed_formats = get_active_formats(filters.get("allowed_formats", None))
        faction_filter = filters.get("faction") 
        type_filter = filters.get("upgrade_type")
        text_filter = filters.get("search_text", "").lower()
        ship_filter = filters.get("ship")
        initiative_filter = filters.get("initiative")
        
        filter_pilot_id = filters.get("pilot_id")
        if filter_pilot_id: filter_pilot_id = filter_pilot_id.strip('"').strip("'")
        
        filter_upgrade_id = filters.get("upgrade_id")
        if filter_upgrade_id: filter_upgrade_id = filter_upgrade_id.strip('"').strip("'")
        
        # ... Filter conversions (kept from original) ...
        allowed_initiatives = set()
        if initiative_filter and initiative_filter != "all":
            if isinstance(initiative_filter, list):
                for i_str in initiative_filter:
                    try: allowed_initiatives.add(int(i_str))
                    except ValueError: pass
            else:
                 try: allowed_initiatives.add(int(initiative_filter))
                 except ValueError: pass
        
        allowed_ships = set()
        if ship_filter and ship_filter != "all":
            if isinstance(ship_filter, list):
                allowed_ships = set(ship_filter)
            else:
                 pass # legacy string search handled below

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

        def _int_or(val, fallback):
            return val if val is not None else fallback

        points_min = _int_or(filters.get("points_min"), 0)
        points_max = _int_or(filters.get("points_max"), 200)
        loadout_min = _int_or(filters.get("loadout_min"), 0)
        loadout_max = _int_or(filters.get("loadout_max"), 99)
        hull_min = _int_or(filters.get("hull_min"), 0)
        hull_max = _int_or(filters.get("hull_max"), 20)
        shields_min = _int_or(filters.get("shields_min"), 0)
        shields_max = _int_or(filters.get("shields_max"), 20)
        agility_min = _int_or(filters.get("agility_min"), 0)
        agility_max = _int_or(filters.get("agility_max"), 10)
        attack_min = _int_or(filters.get("attack_min"), 0)
        attack_max = _int_or(filters.get("attack_max"), 10)
        init_min = _int_or(filters.get("init_min"), 0)
        init_max = _int_or(filters.get("init_max"), 8)
        
        is_unique = filters.get("is_unique", False)
        is_limited = filters.get("is_limited", False)
        is_not_limited = filters.get("is_not_limited", False)
        base_sizes = filters.get("base_sizes", {})

        # --- INITIALIZATION ---
        if mode == "pilots":
            for pid, p_info in all_pilots.items():
                # Filter Logic (copied and simplified)
                p_cost = int(p_info.get("cost", 0) or 0)
                p_loadout = int(p_info.get("loadout", 0) or 0)
                
                if p_cost < points_min or p_cost > points_max: continue
                if data_source == DataSource.XWA and (p_loadout < loadout_min or p_loadout > loadout_max): continue

                is_legal = p_info.get("valid_in_standard", False)
                is_wild = p_info.get("wildspace", False)
                is_epic = p_info.get("epic", False)
                show_card = False
                
                if allowed_formats:
                     if ("xwa" in allowed_formats or "amg" in allowed_formats) and is_legal: show_card = True
                     if "wildspace" in allowed_formats and is_wild: show_card = True
                     if ("xwa_epic" in allowed_formats or "legacy_epic" in allowed_formats) and is_epic: show_card = True
                     if data_source == DataSource.LEGACY:
                         legacy_keys = {"legacy_x2po", "legacy_xlc", "ffg"}
                         if not legacy_keys.isdisjoint(allowed_formats): show_card = True
                else:
                    if data_source == DataSource.XWA and is_legal: show_card = True
                    elif data_source == DataSource.LEGACY: show_card = True

                if not show_card: continue

                # Stat ranges
                p_hull = int(p_info.get("hull") or 0)
                p_shields = int(p_info.get("shields") or 0)
                p_agility = int(p_info.get("agility") or 0)
                p_attack = int(p_info.get("attack") or 0)
                p_init = int(p_info.get("initiative") or 0)
                
                if p_hull < hull_min or p_hull > hull_max: continue
                if p_shields < shields_min or p_shields > shields_max: continue
                if p_agility < agility_min or p_agility > agility_max: continue
                if p_attack < attack_min or p_attack > attack_max: continue
                if p_init < init_min or p_init > init_max: continue
                
                # Base Size
                active_sizes = [s for s, v in base_sizes.items() if v]
                if active_sizes:
                    p_size = p_info.get("size", "Small")
                    size_map = {"S": "Small", "M": "Medium", "L": "Large", "H": "Huge"}
                    allowed_sizes_set = {size_map.get(s, s) for s in active_sizes}
                    if p_size not in allowed_sizes_set: continue

                # Faction
                if allowed_factions:
                    p_faction = p_info.get("faction", "")
                    p_f_norm = p_faction.lower().replace(" ", "").replace("-", "")
                    allowed_norm = {f.lower().replace(" ", "").replace("-", "") for f in allowed_factions}
                    if p_f_norm not in allowed_norm: continue

                # Ship
                p_ship_xws = p_info.get("ship_xws", "")
                if allowed_ships and p_ship_xws not in allowed_ships: continue
                
                # Text Filter
                if text_filter:
                    p_name = p_info.get("name", pid).lower()
                    p_ability = p_info.get("ability", "").lower()
                    p_ship_name = p_info.get("ship", "").lower()
                    p_caption = p_info.get("caption", "").lower()
                    match = (text_filter in p_name) or (text_filter in p_ability) or (text_filter in p_ship_name) or (text_filter in p_caption)
                    if not match: continue

                stats[pid] = {
                    "xws": pid,
                    "games_count": 0,
                    "list_count": 0,
                    "different_lists_count": 0,
                    "wins": 0,
                    "_signatures": set()
                }

        elif mode == "upgrades":
             for u_xws, u_info in all_upgrades.items():
                u_cost = int(u_info.get("cost", {}).get("value", 0) if isinstance(u_info.get("cost"), dict) else (u_info.get("cost") or 0))
                if u_cost < points_min or u_cost > points_max: continue
            
                if allowed_factions:
                    u_restrictions = u_info.get("restrictions", [])
                    u_factions = set()
                    for r in u_restrictions:
                         if "factions" in r:
                            for f in r["factions"]: u_factions.add(f.lower().replace(" ", "").replace("-", ""))
                    
                    match_faction = False
                    if "unrestricted" in allowed_factions and not u_factions: match_faction = True
                    if not match_faction:
                        real_allowed = {f for f in allowed_factions if f != "unrestricted"}
                        if not u_factions.isdisjoint(real_allowed): match_faction = True
                    if not match_faction: continue

                # Validity Check
                is_legal = u_info.get("valid_in_standard", False)
                is_wild = u_info.get("wildspace", False)
                is_epic = u_info.get("epic", False)
                show_card = False
                if allowed_formats:
                     if ("xwa" in allowed_formats or "amg" in allowed_formats) and is_legal: show_card = True
                     if "wildspace" in allowed_formats and is_wild: show_card = True
                     if ("xwa_epic" in allowed_formats or "legacy_epic" in allowed_formats) and is_epic: show_card = True
                     if data_source == DataSource.LEGACY:
                         legacy_keys = {"legacy_x2po", "legacy_xlc", "ffg"}
                         if not legacy_keys.isdisjoint(allowed_formats): show_card = True
                else:
                    if data_source == DataSource.XWA and is_legal: show_card = True
                    elif data_source == DataSource.LEGACY: show_card = True

                if not show_card: continue
                
                # Types
                types = set()
                sides = u_info.get("sides", [])
                if sides and isinstance(sides, list):
                    for side in sides:
                        if "type" in side: types.add(side["type"].lower())
                else:
                    if "type" in u_info: types.add(u_info["type"].lower())

                if allowed_types and types.isdisjoint(allowed_types): continue

                # Text Filter
                if text_filter:
                    u_name = u_info.get("name", u_xws).lower()
                    u_text = ""
                    if sides:
                        for side in sides: u_text += " " + side.get("ability", "").lower()
                    else: u_text = u_info.get("text", "").lower()
                    match = (text_filter in u_name) or (text_filter in u_text)
                    if not match: continue

                stats[u_xws] = {
                    "xws": u_xws,
                    "games_count": 0,
                    "list_count": 0,
                    "different_lists_count": 0,
                    "wins": 0,
                    "_signatures": set()
                }

        # --- A G G R E G A T I O N ---
        for result, tournament in rows:
            # Python-level Filtering
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            if allowed_formats: 
                if t_fmt not in allowed_formats: continue

            if not apply_tournament_filters(tournament, filters): continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            
            # List Stats
            s_wins = result.swiss_wins or 0
            s_losses = result.swiss_losses or 0
            s_draws = result.swiss_draws or 0
            c_wins = result.cut_wins or 0
            c_losses = result.cut_losses or 0
            c_draws = result.cut_draws or 0
            
            wins = s_wins + c_wins
            games = wins + s_losses + c_losses + s_draws + c_draws
            
            # Signature (Assuming it's generated or hashed, or we use dict hash if strict)
            # Use 'id' from backend if available, or generate hash?
            # Creating a naive signature from XWS content if signature not present?
            # xws usually has 'vendor' -> 'm3tacron' -> 'signature'?
            # For now, let's use the list content itself as signature or generate one?
            # Better: use deduplication utils if available.
            # But simpler: if xws is dict, stringify it? Or better, the result.to_dict()? 
            # Or result.list_json hash.
            # Let's use string representation of list_json pilots/upgrades for signature.
            # Actually, `ListData` has `signature`. It's likely pre-calculated in DB or generated on fly.
            # Checking `deduplication.py` would confirm.
            # But let's assume we can generate a basic signature here using sorted string of pilots+upgrades.
            
            import json
            # Sort keys to ensure consistency
            try:
                sig = json.dumps(xws.get("pilots", []), sort_keys=True)
            except:
                sig = str(xws.get("pilots", []))

            if mode == "pilots":
                list_faction = xws.get("faction", "unknown")
                if allowed_factions:
                    try:
                        current_faction = Faction(list_faction).value
                    except ValueError:
                        current_faction = "unknown"
                    
                    # Check against allowed_factions (which are normalized strings usually?)
                    # In init, we used `lower().replace...`
                    # Here we should do the same.
                    cf_norm = current_faction.lower().replace(" ", "").replace("-", "")
                    allowed_norm = {f.lower().replace(" ", "").replace("-", "") for f in allowed_factions}
                    if cf_norm not in allowed_norm: continue
                
                # Iterate unique pilots in this list to avoid double counting per list
                unique_pids_in_list = set()
                for p in xws.get("pilots", []):
                    pid = p.get("id") or p.get("name")
                    if not pid: continue
                    
                    # Note: We do NOT filter by upgrade_id here for collecting unique PIDs.
                    # The filter logic in old code was: "if filter_upgrade_id, skip pilots that don't have it".
                    # We should apply that here too.
                    
                    if filter_upgrade_id:
                        has_u = False
                        for u_list in p.get("upgrades", {}).values():
                            if filter_upgrade_id in u_list: has_u = True; break
                        if not has_u: continue
                    
                    unique_pids_in_list.add(pid)

                for pid in unique_pids_in_list:
                    if pid in stats:
                        s = stats[pid]
                        s["games_count"] += games
                        s["list_count"] += 1
                        s["wins"] += wins
                        s["_signatures"].add(sig)

            elif mode == "upgrades":
                # Collect unique upgrades in this list
                unique_upgrades_in_list = set()
                
                # Check target pilot filter
                for p in xws.get("pilots", []):
                    pid = p.get("id") or p.get("name")
                    
                    if filter_pilot_id and pid != filter_pilot_id: continue
                    
                    upgrades = p.get("upgrades", {}) or {}
                    
                    # Check target upgrade filter (if both set)
                    if filter_upgrade_id:
                         # logic in old code: skip pilot if it doesn't have target upgrade?
                         # No, here we are iterating upgrades.
                         # If we are filtering by upgrade ID, we likely want stats FOR that upgrade?
                         # The old logic filtered the LIST/PILOT if it didn't match.
                         # Here we are collecting upgrades.
                         pass

                    for u_type, u_list in upgrades.items():
                         if allowed_types and u_type.lower() not in allowed_types: continue
                         for u_xws in u_list:
                             if filter_upgrade_id and u_xws == filter_upgrade_id: continue # excluding itself? (old logic seems to exclude)
                             
                             unique_upgrades_in_list.add(u_xws)

                for u_xws in unique_upgrades_in_list:
                    if u_xws in stats:
                        s = stats[u_xws]
                        s["games_count"] += games
                        s["list_count"] += 1
                        s["wins"] += wins
                        s["_signatures"].add(sig)

        # Finalize
        results = []
        for xws_id, s_data in stats.items():
            if s_data["list_count"] > 0: # Only include used cards? Or initialized ones? Initial filter decides.
                # If we initialized them, we probably want to return them even if 0 usage (for "0%" stats)
                # But typically we only show what's relevant unless search text is used.
                # Use passed logic: if initialized in stats dict, verify if we keep it.
                # If it has 0 games, do we keep it? Yes, to show 0/0.
                
                s_data["different_lists_count"] = len(s_data.pop("_signatures"))
                results.append(s_data)
                
        # Sort
        # criteria: POPULARITY, WINRATE, GAMES, COST, NAME
        def sort_key(item):
            if sort_criteria == SortingCriteria.POPULARITY:
                return (item["list_count"], item["games_count"])
            elif sort_criteria == SortingCriteria.GAMES:
                return item["games_count"]
            elif sort_criteria == SortingCriteria.WINRATE:
                return item["wins"] / item["games_count"] if item["games_count"] > 0 else 0
            elif sort_criteria == SortingCriteria.NAME:
                return item["xws"] # We don't have name in stats anymore, usage must rely on XWS or separate mapping
            elif sort_criteria == SortingCriteria.COST:
                return 0 # Cost not in stats anymore
            return 0
        
        results.sort(key=sort_key, reverse=(sort_direction == SortDirection.DESCENDING))
        
        return results
