"""
List Analytics - Aggregation Logic for Squad Lists.
"""
from sqlmodel import Session, select
import json
from ..database import engine
from ..models import PlayerStanding, Tournament
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from .filters import filter_query, get_active_formats, apply_tournament_filters

def aggregate_list_stats(
    filters: dict,
    limit: int = 10,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for squad lists.
    Returns list of dicts matching ListData schema.
    """
    with Session(engine) as session:
        # Load filtered results
        query = select(PlayerStanding, Tournament).where(
            PlayerStanding.tournament_id == Tournament.id
        )
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        list_stats = {} # signature -> valid ListData dict
        
        allowed_formats = get_active_formats(filters.get("allowed_formats", None))

        for result, tournament in rows:
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "unknown")
            
            if allowed_formats and t_fmt not in allowed_formats: continue
            if not apply_tournament_filters(tournament, filters): continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            
            pilots = xws.get("pilots", [])
            if not pilots: continue
            
            # Ship Filter
            req_ships = filters.get("ships")
            if req_ships:
                match = False
                for p in pilots:
                    # Check 'ship' key (XWS standard)
                    if p.get("ship") in req_ships:
                        match = True
                        break
                if not match: continue
            
            temp_pilots = []
            for p in pilots:
                pid = p.get("id") or p.get("name")
                if not pid: continue
                # Upgrades
                u_xws_list = []
                raw_upgrades = p.get("upgrades", {})
                if isinstance(raw_upgrades, dict):
                    for slot, items in raw_upgrades.items():
                        if isinstance(items, list):
                            for item in items: u_xws_list.append(str(item))
                        else: u_xws_list.append(str(items))
                elif isinstance(raw_upgrades, list):
                    for item in raw_upgrades: u_xws_list.append(str(item))
                
                u_xws_list.sort() # Canonicalize upgrades
                
                temp_pilots.append({
                    "xws": pid,
                    "upgrades": [{"xws": u} for u in u_xws_list]
                })
            
            # Canonicalize Pilots Order
            # Sort by (pilot_xws, upgrades_string)
            temp_pilots.sort(key=lambda x: (x["xws"], str(x["upgrades"])))
            
            # Signature
            try: sig = json.dumps(temp_pilots, sort_keys=True)
            except: sig = str(temp_pilots)
            
            if sig not in list_stats:
                f_enum = Faction.from_xws(xws.get("faction", "unknown"))

                list_stats[sig] = {
                    "signature": sig,
                    "name": xws.get("name") or "",
                    "points": xws.get("points", 0),
                    "original_points": 0,
                    "faction_xws": f_enum,
                    "pilots": temp_pilots,
                    "wins": 0,
                    "games": 0
                }
            
            s = list_stats[sig]
            
            s_wins = result.swiss_wins or 0
            s_losses = result.swiss_losses or 0
            s_draws = result.swiss_draws or 0
            c_wins = result.cut_wins or 0
            c_losses = result.cut_losses or 0
            c_draws = result.cut_draws or 0
            
            wins = s_wins + c_wins
            games = wins + s_losses + s_draws + c_losses + c_draws
            
            s["wins"] += wins
            s["games"] += games
            
        final_list = list(list_stats.values())
        final_list.sort(key=lambda x: x["games"], reverse=True)
        
        return final_list[:limit]
