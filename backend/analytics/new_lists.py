"""
List Analytics - Aggregation Logic for Squad Lists.
"""
from sqlmodel import Session, select
import json
from ..database import engine
from ..models import PlayerResult, Tournament
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from .filters import filter_query, get_active_formats, apply_tournament_filters
from ..api.schemas import ListData, PilotData, UpgradeData # Import schemas to ensure structure matches? Or just dicts.

# Or just assume dicts matching schemas.
# Pydantic models are imported only for type hinting or validation, but here we return list[dict].
# But ListData requires PilotData objects if validation is strict? 
# Usually Pydantic coerces dict -> Model.
# So returning dicts { "pilots": [ { "xws": "...", "upgrades": [...] } ] } works.

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
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        # Key: signature -> { pilots_data, faction, wins, games, name, points }
        list_stats = {}
        
        allowed_formats = get_active_formats(filters.get("allowed_formats", None))

        for result, tournament in rows:
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            if allowed_formats and t_fmt not in allowed_formats: continue
            if not apply_tournament_filters(tournament, filters): continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            
            # Signature Calculation (Canonical List)
            pilots = xws.get("pilots", [])
            if not pilots: continue
            
            # Convert to PilotData structure for easier handling and signature
            # We need standard sorting for signature
            
            temp_pilots = []
            for p in pilots:
                pid = p.get("id") or p.get("name")
                if not pid: continue
                
                # Upgrades
                # p["upgrades"] is dict { "slot": ["u1", "u2"] }
                # Flatten to list of UpgradeData dicts
                u_list = []
                raw_upgrades = p.get("upgrades", {})
                if isinstance(raw_upgrades, dict):
                    for slot, items in raw_upgrades.items():
                        if isinstance(items, list):
                            for u_xws in items: u_list.append(u_xws)
                        else: u_list.append(str(items)) # Should be list usually
                elif isinstance(raw_upgrades, list): 
                     # Legacy format might differ? assuming dict for XWS standard
                     pass

                u_list.sort()
                
                temp_pilots.append({
                    "xws": pid,
                    "upgrades": [{"xws": u} for u in u_list]
                })

            # Sort pilots by XWS to canonicalize list order
            temp_pilots.sort(key=lambda x: x["xws"])
            
            # Simple recursive signature
            try:
                sig = json.dumps(temp_pilots, sort_keys=True)
            except:
                sig = str(temp_pilots)
            
            if sig not in list_stats:
                # Faction
                f_raw = xws.get("faction", "unknown")
                try: f_enum = Faction(f_raw) # or from_xws
                except ValueError: f_enum = Faction.UNKNOWN # or skip?
                
                list_stats[sig] = {
                    "name": xws.get("name") or "",
                    "signature": sig,
                    "points": xws.get("points", 0),
                    "original_points": 0, # Not always available
                    "faction_xws": f_enum,
                    "pilots": temp_pilots, # Already structured correctly
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
            
        # Convert to list and apply limit/sort
        results = list(list_stats.values())
        
        # Sort by popularity (games played) default
        results.sort(key=lambda x: x["games"], reverse=True)
        
        return results[:limit]
