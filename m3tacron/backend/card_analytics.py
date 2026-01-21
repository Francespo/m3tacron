"""
Card Analytics - Aggregation Logic for Pilots and Upgrades.
"""
from collections import Counter
from sqlmodel import Session, select

from .database import engine
from .models import PlayerResult, Tournament
from .xwing_data import get_pilot_name, get_upgrade_name, get_pilot_info, load_all_pilots, load_all_upgrades
from .enums.factions import Faction
from .enums.formats import Format, MacroFormat

def filter_query(query, filters: dict):
    """
    Apply filters to the query.
    filters:Dictionary containing:
        - formats: list[str] (e.g. ["2.5", "amg"]) -> hierarchical logic handled by caller or simple list
        - date_start: str (YYYY-MM-DD)
        - date_end: str (YYYY-MM-DD)
    """
    if not filters:
        return query

    # Date Filters (Applied on Tournament)
    if filters.get("date_start"):
        query = query.where(Tournament.date >= filters["date_start"])
    if filters.get("date_end"):
        query = query.where(Tournament.date <= filters["date_end"])
        
    return query

def check_format_filter(tournament: Tournament, format_selection: dict[str, bool] | None) -> bool:
    """
    Check if a tournament matches the hierarchical format filter.
    format_selection: dict mapping format/macro values to boolean (active)
                      e.g. {"2.5": True, "amg": True, "2.0": False}
    """
    if not format_selection:
        return True # specific format filter behavior: empty means all? or none? usually all.
    
    # Check Macro Format
    macro = tournament.macro_format
    
    # If Macro is explicitly False, we might still include specific children if they are True?
    # Requirement: "Attivare il toggle principale significa che tutti i sotto-formati corrispondenti sono inclusi"
    # So if Macro is True, satisfy.
    # But user can select "soltanto un sotto-formato".
    # So: if Macro is True AND (subformat is not explicitly False?) -> Actually, standard hierarchical filter:
    # A tournament has a specific 'format'.
    # We check if that specific format is enabled.
    
    t_format_val = tournament.format.value if tournament.format else "other"
    
    # Check if specific format is enabled
    is_enabled = format_selection.get(t_format_val)
    
    # If text format not found directly, check macro?
    # The UI will likely pass a flat list of ALL allowed specific formats, 
    # OR a mixed dict.
    # Simplest approach: The UI calculates the effective allowed list of specific formats.
    # But here we might receive the raw toggle state.
    
    # Let's assume the UI resolves logic and passes a set of ALLOWED FORMAT STRINGS.
    # If format_selection is a list/set of strings:
    if isinstance(format_selection, (list, set)):
        return t_format_val in format_selection
        
    # If dict (toggles)
    return format_selection.get(t_format_val, False)


def aggregate_card_stats(
    filters: dict,
    sort_mode: str = "popularity", # popularity, win_rate
    mode: str = "pilots", # pilots, upgrades
    data_source: str = "xwa" # xwa, legacy
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
        
        # Pre-process initiative filter (e.g., "3" or "3+")
        # Pre-process initiative filter (list[str] or single string "all")
        # Filters now come as list[str] of allowed values. "all" is not used if list is provided, default to empty/all behavior.
        # But legacy call might still pass string "all".
        # Let's handle both.
        
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
        
        # Ship Filter Logic (Comma Separated)
        ship_search_terms = []
        if ship_filter and ship_filter != "all":
            ship_search_terms = [s.strip().lower() for s in ship_filter.split(",") if s.strip()]

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
            
            # Format
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            if allowed_formats: # Only filter if list is not empty
                if t_fmt not in allowed_formats:
                    # Fallback: check if macro is in allowed? 
                    # Assuming allowed_formats is exhaustive list of specific formats
                    continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            
            # Process List
            # Calculate wins/games for this result
            wins = result.swiss_wins + result.cut_wins
            games = wins + result.swiss_losses + result.cut_losses + result.swiss_draws
            
            if mode == "pilots":
                list_faction = xws.get("faction", "unknown")
                # Faction Filter (Applies to List Faction or Pilot Faction? Usually List Faction for Pilots tab filter)
                if allowed_factions:
                    # Normalize list faction
                    current_faction = Faction.from_xws(list_faction).value
                    if current_faction not in allowed_factions:
                        continue
                
                for p in xws.get("pilots", []):
                    pid = p.get("id") or p.get("name")
                    if not pid: continue
                    
                    # Ship Filter
                    if ship_search_terms:
                        p_info = all_pilots.get(pid, {})
                        p_ship = p_info.get("ship", "").lower()
                        # Check if matches ANY term
                        # Strict match or substring? User said "input di più valori".
                        # Suggest matching behavior: substring ok? Or user expects precise filter?
                        # Given "x-wing, y-wing", likely expects match.
                        match_ship = False
                        for term in ship_search_terms:
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
                # Upgrade Logic
                # Needs to iterate all pilots, then all upgrades
                for p in xws.get("pilots", []):
                    # We don't filter by Pilot Faction per se, but user might want to?
                    # Request says "Per le migliorie... filtrare per tipo". 
                    # Faction filter is mentioned for pilots ("Per i piloti c'è bisogno di un filtro per fazione").
                    # So Upgrade tab might not need faction filter, but maybe beneficial? 
                    # Let's ignore faction filter for upgrades unless requested.
                    
                    upgrades = p.get("upgrades", {}) or {}
                    for u_type, u_list in upgrades.items():
                        
                        # Type Filter
                        if allowed_types and u_type.lower() not in allowed_types:
                            continue
                            
                        for u_xws in u_list:
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
                                    "type": u_type, # This might vary if an upgrade has multiple sides/types? simple for now
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
        for v in stats.values():
            if v["games"] > 0:
                v["win_rate"] = (v["wins"] / v["games"]) * 100
            else:
                v["win_rate"] = 0.0
            results.append(v)
            
        # Sorting
        if sort_mode == "win_rate":
            # Sort by WR desc, then games desc
            results.sort(key=lambda x: (x["games"] > 5, x["win_rate"], x["count"]), reverse=True)
        else: # popularity
            results.sort(key=lambda x: x["count"], reverse=True)
            
        return results

