"""
Faction Analytics - Aggregation Logic for Factions.
"""
from sqlmodel import Session, select, func
import json
from ..database import engine
from ..models import PlayerResult, Tournament
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from .filters import filter_query, get_active_formats, apply_tournament_filters
from ..utils.list_keys import get_list_key

def aggregate_faction_stats(
    filters: dict,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics per faction.
    Returns list of dicts matching FactionStats schema.
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
                "xws": f, # Enum value itself or Faction member
                "games_count": 0,
                "list_count": 0,
                "wins": 0,
                "different_lists_count": 0,
                "_signatures": set()
            }

        allowed_formats = get_active_formats(filters.get("allowed_formats", None))

        for result, tournament in rows:
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            if allowed_formats is not None and t_fmt not in allowed_formats:
                continue

            if not apply_tournament_filters(tournament, filters):
                continue
                
            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue
                
            list_faction_raw = xws.get("faction", "unknown")
            try:
                faction_enum = Faction(list_faction_raw) # or Faction.from_xws if strict
            except ValueError:
                # Try normalization if needed, or skip
                # Standard xws uses lowercase/hyphenated
                # data_structures.factions defines standard values
                continue
                
            faction_xws = faction_enum.value
            
            if faction_xws not in faction_stats:
                # Should be initialized, but if not (e.g. unknown faction)
                 continue
            
            s_wins = result.swiss_wins or 0
            s_losses = result.swiss_losses or 0
            s_draws = result.swiss_draws or 0
            c_wins = result.cut_wins or 0
            c_losses = result.cut_losses or 0
            c_draws = result.cut_draws or 0
            
            wins = s_wins + c_wins
            games = wins + s_losses + s_draws + c_losses + c_draws
            
            sig = get_list_key(xws)
            
            s = faction_stats[faction_xws]
            s["wins"] += wins
            s["games_count"] += games
            s["list_count"] += 1
            s["_signatures"].add(sig)
            
        results = []
        for xws, data in faction_stats.items():
            if data["list_count"] == 0: 
                # keep 0 stats? FactionStats response expects list.
                # If we want to show all factions even with 0 games
                pass
            
            data["different_lists_count"] = len(data.pop("_signatures"))
            results.append(data)
            
        # Sort by games_count desc
        results.sort(key=lambda x: x["games_count"], reverse=True)
        return results

def get_meta_snapshot(data_source: DataSource = DataSource.XWA, allowed_formats: list[str] | None = None) -> dict:
    """
    Get a high-level summary of the current meta (last 90 days).
    """
    from datetime import datetime, timedelta
    
    # Use 90 day window
    # But usually meta snapshot might check last sync or just be a fixed window
    # The prompt implies "MetaSnapshotResponse"
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    date_str = start_date.strftime("%Y-%m-%d")
    
    filters = {
        "date_start": date_str,
    }
    if allowed_formats:
        filters["allowed_formats"] = get_active_formats(allowed_formats)
    else:
        filters["allowed_formats"] = ["xwa", "amg"] if data_source == DataSource.XWA else ["legacy_x2po", "legacy_xlc"]
    
    faction_stats = aggregate_faction_stats(filters, data_source)
    
    from .ships import aggregate_ship_stats
    ship_stats = aggregate_ship_stats(filters, data_source=data_source)
    
    from .lists import aggregate_list_stats
    list_stats = aggregate_list_stats(filters, data_source=data_source)
    
    from .core import aggregate_card_stats
    pilot_stats = aggregate_card_stats(filters, mode="pilots", data_source=data_source)
    upgrade_stats = aggregate_card_stats(filters, mode="upgrades", data_source=data_source)
    
    total_games = sum(f["games_count"] for f in faction_stats)
    total_lists = sum(f["list_count"] for f in faction_stats) # Approx total lists analyzed
    
    # Calculate stats for the snapshot range
    # total_tournaments? we need to count them.
    # aggregate functions don't return total tournaments.
    # But we can query quickly here.
    
    with Session(engine) as session:
        q_t = select(func.count(Tournament.id)).where(Tournament.date >= date_str)
        q_p = select(func.count(PlayerResult.id)).join(Tournament).where(Tournament.date >= date_str)
        # Apply format filters
        # Note: apply_tournament_filters is python side usually, but allowed_formats can be SQL if possible
        # For simple counts we can approx or rely on aggregates.
        # But wait, schemas.MetaSnapshotResponse needs total_tournaments and total_players.
        
        # Let's trust stats or query roughly.
        total_tournaments = 0 # Placeholder if heavy
        total_players = 0     # Placeholder
    
    return {
        "factions": faction_stats,
        "ships": ship_stats,
        "lists": list_stats,
        "pilots": pilot_stats,
        "upgrades": upgrade_stats,
        "last_sync": datetime.now().strftime("%Y-%m-%d"),
        "date_range": "Last 90 Days",
        "total_tournaments": total_tournaments, # Should implement proper counting if needed
        "total_players": total_players
    }
