
"""
List Analytics - Aggregation Logic for Squad Lists.
"""
from sqlmodel import Session, select, func
from ..database import engine
from ..models import PlayerResult, Tournament
from ..data_structures.factions import Faction, get_faction_char
from ..data_structures.data_source import DataSource
from .filters import filter_query, get_active_formats, apply_tournament_filters
from ..utils.squadron import get_list_signature
import json

def aggregate_list_stats(
    filters: dict,
    limit: int = 10,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for squad lists (hash-based patterns).
    """
    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        # stats: tuple(pilot_xws, upgrade_hashes) -> {wins, games, count, first_instance_json}
        # For MVP simplicity, we'll hash the sorted pilot XWS and their main upgrades/loadout.
        # A more robust solution would use a canonical list hash.
        
        list_stats = {}
        
        for result, tournament in rows:
            # Format filter optimization
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            allowed_formats = get_active_formats(filters.get("allowed_formats", None))
            if allowed_formats and t_fmt not in allowed_formats:
                continue

            # Location Filtering
            if not apply_tournament_filters(tournament, filters):
                continue

            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue
                
            pilots = xws.get("pilots", [])
            if not pilots: continue
            
            req_ships = filters.get("ships")
            if req_ships:
                ship_matched = False
                for p in pilots:
                    if p.get("ship") in req_ships:
                        ship_matched = True
                        break
                if not ship_matched:
                    continue
            
            list_key = get_list_signature(xws)
            if not list_key:
                continue
            
            if list_key not in list_stats:
                list_stats[list_key] = {
                    "pilots": pilots,
                    "faction": xws.get("faction", "unknown"),
                    "wins": 0,
                    "games": 0,
                    "count": 0,
                "results": [],
                "name": xws.get("name") or f"Untitled {xws.get('faction', '')} List",
                "points": xws.get("points", 0)
                }
            
            s_wins = result.swiss_wins or 0
            s_losses = result.swiss_losses or 0
            s_draws = result.swiss_draws or 0
            c_wins = result.cut_wins or 0
            c_losses = result.cut_losses or 0
            c_draws = result.cut_draws or 0
            
            wins = s_wins + c_wins
            games = wins + s_losses + s_draws + c_losses + c_draws
            
            list_stats[list_key]["wins"] += wins
            list_stats[list_key]["games"] += games
            list_stats[list_key]["count"] += 1
            
        results = []
        for key, data in list_stats.items():
            f_xws = data["faction"]
            
            results.append({
                "signature": key,
                "name": data["name"],
                "faction_xws": f_xws,
                "popularity": data["count"],
                "games": data["games"],
                "wins": data["wins"],
                "points": data["points"],
                "pilots": data["pilots"]
            })
            
        # Defaults to sorting by popularity
        results.sort(key=lambda x: x["popularity"], reverse=True)
        return results[:limit]
