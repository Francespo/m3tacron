"""
Card Usage Charts Analytics.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from sqlmodel import Session, select
from ..database import engine
from ..models import PlayerResult, Tournament
from ..data_structures.formats import Format
from .filters import filter_query

def get_card_usage_history(
    filters: dict,
    main_card_xws: str,
    comparison_xws_list: list[str] = [],
    is_upgrade: bool = False # False = Pilot, True = Upgrade
) -> list[dict]:
    """
    Get usage history for a main card and optional comparison cards.
    Aggregates by month.
    
    Returns list of dicts:
    [
      {"date": "2023-01", "main_card": 10, "comp1": 5, ...},
      ...
    ]
    """
    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        # Structure: date_key -> {card_xws -> count}
        # Date key: YYYY-MM
        history = defaultdict(lambda: defaultdict(int))
        
        all_tracked_cards = {main_card_xws} | set(comparison_xws_list)
        
        allowed_formats = filters.get("allowed_formats")

        for result, tournament in rows:
            # Format Check
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            if allowed_formats and t_fmt not in allowed_formats:
                continue
                
            date_key = tournament.date.strftime("%Y-%m")
            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            
            # Check presence of tracked cards in the list
            found_cards = set()
            
            for p in xws.get("pilots", []):
                pid = p.get("id") or p.get("name")
                
                # Check Pilot
                if not is_upgrade:
                    if pid in all_tracked_cards:
                        found_cards.add(pid)
                        
                # Check Upgrade (if main card is upgrade OR we are comparing upgrades)
                # Actually, complexity:
                # 1. Main card is Pilot -> Comparisons are upgrades (usage on that pilot?) or other pilots?
                # Assumption: Comparisons are of the SAME type generally, but user asked for "combination".
                # If Pilot Page: Chart shows Pilot Usage. Comparison? 
                # User request: "having the possibility to select other cards, I would like to see how much the selected cards were used in time... in combination with the card of which the page is open".
                # Ah! So if I am on Pilot X page.
                # Chart Line 1: Pilot X usage total? Or just Pilot X?
                # User: "graph of how much that card (upgrade/pilot) was used over time" -> Base line.
                # "select other cards... see how much they were used... in combination with the card".
                # So Line 2 (Upgrade Y): Usage of Pilot X + Upgrade Y.
                
                # Implementation Logic:
                # 1. Always check if Main Card is present.
                # 2. If Main Card is present, increment "Usage".
                # 3. If Main Card is present, Check for Comparison Cards in the SAME list.
                # 4. If Comparison Card is present (AND Main Card is present), increment "Combo Usage".
                
                # We need to scan the whole list first to confirm Main Card presence.
                pass
            
            # Efficient Scan
            # Flatten List to set of XWS IDs
            list_pilots = set()
            list_upgrades = set()
            
            for p in xws.get("pilots", []):
                pid = p.get("id") or p.get("name")
                if pid: list_pilots.add(pid)
                
                upgrades = p.get("upgrades", {}) or {}
                for u_list in upgrades.values():
                    for u in u_list:
                        list_upgrades.add(u)
                        
            # Check Main Card Presence
            main_present = False
            if not is_upgrade:
                main_present = main_card_xws in list_pilots
            else:
                main_present = main_card_xws in list_upgrades
            
            if main_present:
                # Increment Main Card
                history[date_key][main_card_xws] += 1
                
                # Check Comparisons
                for comp_xws in comparison_xws_list:
                    # Comparison could be pilot or upgrade. Check both.
                    if comp_xws in list_pilots or comp_xws in list_upgrades:
                        history[date_key][comp_xws] += 1
                        
        # Format for Recharts
        # Sort by date
        sorted_dates = sorted(history.keys())
        chart_data = []
        for d in sorted_dates:
            entry = {"date": d}
            counts = history[d]
            entry[main_card_xws] = counts[main_card_xws]
            for comp in comparison_xws_list:
                entry[comp] = counts[comp]
            chart_data.append(entry)
            
        return chart_data
