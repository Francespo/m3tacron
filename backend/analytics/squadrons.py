"""
Squadron Analytics - Aggregation Logic for Squadron (Ship Composition).
"""
from sqlmodel import Session, select
from ..database import engine
from ..models import PlayerStanding, Tournament
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..utils.list_keys import coerce_list_json
from ..utils.stats import normalize_stat_count
from .filters import filter_query, get_active_formats
import json

def aggregate_squadron_stats(
    filters: dict,
    sort_metric: SortingCriteria = SortingCriteria.GAMES,
    sort_direction: SortDirection = SortDirection.DESCENDING,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for squadrons (combinations of ship chassis).
    """
    with Session(engine) as session:
        query = select(PlayerStanding, Tournament).where(
            PlayerStanding.tournament_id == Tournament.id
        )
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        squadron_stats = {}
        
        for result, tournament in rows:
            # Format filter
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "unknown")
            
            allowed_formats = get_active_formats(filters.get("allowed_formats", None))
            if allowed_formats and t_fmt not in allowed_formats:
                continue

            xws = coerce_list_json(result.list_json)
            if not xws:
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
            
            # Simple canonical representation for squadron (ships)
            ships = []
            faction = xws.get("faction", "unknown")
            for p in pilots:
                s_id = p.get("ship") or "unknown"
                ships.append(s_id)
            
            ships.sort()
            signature = ", ".join(ships)
            
            if signature not in squadron_stats:
                squadron_stats[signature] = {
                    "faction": faction,
                    "signature": signature,
                    "wins": 0,
                    "games": 0,
                    "count": 0,
                    "ships": ships
                }
            
            s_wins = normalize_stat_count(result.swiss_wins)
            s_losses = normalize_stat_count(result.swiss_losses)
            s_draws = normalize_stat_count(result.swiss_draws)
            c_wins = normalize_stat_count(result.cut_wins)
            c_losses = normalize_stat_count(result.cut_losses)
            c_draws = normalize_stat_count(result.cut_draws)
            
            wins = s_wins + c_wins
            games = wins + s_losses + s_draws + c_losses + c_draws
            
            squadron_stats[signature]["wins"] += wins
            squadron_stats[signature]["games"] += games
            squadron_stats[signature]["count"] += 1
            
        results = []
        for key, data in squadron_stats.items():
            win_rate = round((data["wins"] / data["games"]) * 100, 1) if data["games"] > 0 else 0.0
            
            results.append({
                "signature": data["signature"],
                "faction": data["faction"],
                "win_rate": win_rate,
                "popularity": data["count"],
                "games": data["games"],
                "wins": data["wins"],
                "count": data["count"],
                "ships": data["ships"]
            })
            
        # Defaults to sorting by popularity
        results.sort(key=lambda x: x["games"], reverse=True)
        return results
