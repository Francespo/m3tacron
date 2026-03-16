
"""
Faction Analytics - Aggregation Logic for Factions.
"""
from sqlmodel import Session, select, func
from ..database import engine
from ..models import PlayerResult, Tournament
from ..data_structures.factions import Faction
from ..data_structures.formats import Format
from ..data_structures.data_source import DataSource
from .filters import filter_query, get_active_formats, apply_tournament_filters




def aggregate_faction_stats(
    filters: dict,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics per faction.
    """
    with Session(engine) as session:
        # Load tournament results
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        faction_stats = {}
        
        # Init all known factions
        for f in Faction:
            if f == Faction.UNKNOWN: continue
            faction_stats[f.value] = {
                "xws": f.value,
                "wins": 0,
                "games": 0,
                "popularity": 0, # total lists
            }

        allowed_formats = get_active_formats(filters.get("allowed_formats", None))

        for result, tournament in rows:
            # Format filter (Python side for safety if not in query)
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            if allowed_formats is not None and t_fmt not in allowed_formats:
                continue

            # Location Filtering
            if not apply_tournament_filters(tournament, filters):
                continue
                
            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue
                
            list_faction_raw = xws.get("faction", "unknown")
            faction_enum = Faction.from_xws(list_faction_raw)
            faction_xws = faction_enum.value
            
            if faction_xws == "unknown":
                continue
            
            if faction_xws not in faction_stats:
                 faction_stats[faction_xws] = {
                    "xws": faction_xws,
                    "wins": 0,
                    "games": 0,
                    "popularity": 0,
                }
            
            s_wins = result.swiss_wins or 0
            s_losses = result.swiss_losses or 0
            s_draws = result.swiss_draws or 0
            
            c_wins = result.cut_wins or 0
            c_losses = result.cut_losses or 0
            c_draws = result.cut_draws or 0
            
            wins = s_wins + c_wins
            games = wins + s_losses + s_draws + c_losses + c_draws
            
            faction_stats[faction_xws]["wins"] += wins
            faction_stats[faction_xws]["games"] += games
            faction_stats[faction_xws]["popularity"] += 1
            
        results = []
        for xws, data in faction_stats.items():
            if data["popularity"] == 0: continue
            
            win_rate = round((data["wins"] / data["games"]) * 100, 1) if data["games"] > 0 else 0.0
            
            results.append({
                "xws": data["xws"],
                "win_rate": win_rate,
                "popularity": data["popularity"],
                "games": data["games"],
                "wins": data["wins"]
            })
            
        # Default sort by popularity
        results.sort(key=lambda x: x["popularity"], reverse=True)
        return results

def get_meta_snapshot(data_source: DataSource = DataSource.XWA, allowed_formats: list[str] | None = None) -> dict:
    """
    Get a high-level summary of the current meta (last 90 days).
    """
    from datetime import datetime, timedelta
    
    # Use 90 day window
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    date_str = start_date.strftime("%Y-%m-%d")
    
    filters = {
        "date_start": date_str,
    }
    if allowed_formats:
        filters["allowed_formats"] = get_active_formats(allowed_formats)
    else:
        # Default fallback if none provided (though HomeState should provide them)
        if data_source == DataSource.XWA:
             filters["allowed_formats"] = ["xwa", "amg"]
        else:
             filters["allowed_formats"] = ["legacy_x2po", "legacy_xlc"]
    
    faction_stats = aggregate_faction_stats(filters, data_source)
    from .ships import aggregate_ship_stats
    ship_stats = aggregate_ship_stats(filters, data_source=data_source)
    
    from .lists import aggregate_list_stats
    list_stats = aggregate_list_stats(filters, data_source=data_source)
    
    from .core import aggregate_card_stats
    pilot_stats = aggregate_card_stats(filters, mode="pilots", data_source=data_source)
    upgrade_stats = aggregate_card_stats(filters, mode="upgrades", data_source=data_source)
    
    # Calculate Total Games for Pie Chart (Distribution)
    total_games = sum(f["games"] for f in faction_stats)
    faction_distribution = []
    
    for f in faction_stats:
        percentage = round((f["games"] / total_games) * 100, 1) if total_games > 0 else 0
        faction_distribution.append({
            "xws": f["xws"],
            "win_rate": f["win_rate"],
            "popularity": f["popularity"],
            "games": f["games"],
            "wins": f["wins"],
            "percentage": percentage
        })
    
    # Helper to filter and sort
    def filter_and_sort(items, min_games):
        filtered = [x for x in items if x.get("games", 0) >= min_games and x.get("win_rate") != "NA"]
        filtered.sort(key=lambda x: float(x.get("win_rate", 0)), reverse=True)
        return filtered

    # Get last tournament date
    with Session(engine) as session:
        last_tournament = session.exec(select(Tournament).order_by(Tournament.date.desc())).first()
        last_sync = last_tournament.date.strftime("%Y-%m-%d") if last_tournament else "Never"
        
    top_ships = filter_and_sort(ship_stats, 100)
    top_lists = filter_and_sort(list_stats, 10)
    top_pilots = filter_and_sort(pilot_stats, 30)
    top_upgrades = filter_and_sort(upgrade_stats, 150)
    
    return {
        "factions": faction_stats[:10],
        "faction_distribution": faction_distribution,
        "ships": top_ships[:10],
        "lists": top_lists[:10],
        "pilots": top_pilots[:10],
        "upgrades": top_upgrades[:10],
        "last_sync": last_sync,
        "date_range": f"{date_str} to {end_date.strftime('%Y-%m-%d')}"
    }
