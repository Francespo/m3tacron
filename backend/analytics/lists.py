
"""
List Analytics - Aggregation Logic for Squad Lists.
"""
from sqlmodel import Session, select, func
from ..database import engine
from ..models import PlayerResult, Tournament
from ..data_structures.data_source import DataSource
from .filters import filter_query, get_active_formats
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

            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue
                
            pilots = xws.get("pilots", [])
            if not pilots: continue
            
            # Simple canonical representation for grouping
            pilot_list = []
            for p in pilots:
                p_id = p.get("id") or p.get("name") or "unknown"
                # Sort upgrades to make it stable
                upgrades = []
                upgrade_data = p.get("upgrades", {})
                if isinstance(upgrade_data, dict):
                    for slot, items in upgrade_data.items():
                        if isinstance(items, list):
                            upgrades.extend([str(i) for i in items])
                elif isinstance(upgrade_data, list):
                    upgrades.extend([str(i) for i in upgrade_data])
                
                upgrades.sort()
                pilot_list.append(f"{p_id}({','.join(upgrades)})")
            
            pilot_list.sort()
            list_key = "|".join(pilot_list)
            
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
            win_rate = round((data["wins"] / data["games"]) * 100, 1) if data["games"] > 0 else 0.0
            
            results.append({
                "name": data["name"],
                "faction": data["faction"],
                "win_rate": win_rate,
                "popularity": data["count"],
                "games": data["games"],
                "wins": data["wins"],
                "points": data["points"],
                "pilots": data["pilots"]
            })
            
        # Defaults to sorting by popularity
        results.sort(key=lambda x: x["popularity"], reverse=True)
        return results[:limit]
