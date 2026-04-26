"""
Ship Analytics - Aggregation Logic for Ships.

Aggregates statistics (win rate, popularity, games) per ship per faction.
"""
from sqlmodel import Session, select
from ..database import engine
from ..models import PlayerResult, Tournament
from ..utils.xwing_data.pilots import load_all_pilots
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from .filters import filter_query, get_active_formats, apply_tournament_filters
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..utils.list_keys import get_list_key


def aggregate_ship_stats(
    filters: dict,
    sort_criteria: SortingCriteria = SortingCriteria.POPULARITY,
    sort_direction: SortDirection = SortDirection.DESCENDING,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for ships grouped by faction.
    Returns list of dicts matching ShipStats schema.
    """
    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        all_pilots = load_all_pilots(data_source)
        
        allowed_formats = get_active_formats(filters.get("allowed_formats", None))

        requested_ships_raw = filters.get("ship") or []
        requested_ships = set(requested_ships_raw) if isinstance(requested_ships_raw, list) else {requested_ships_raw}

        requested_factions_raw = filters.get("faction") or []
        if not isinstance(requested_factions_raw, list):
            requested_factions_raw = [requested_factions_raw]
        requested_factions = {
            str(f).lower().replace(" ", "").replace("-", "")
            for f in requested_factions_raw
            if f
        }
        
        # Structure: (ship_xws, faction_xws) -> stats
        ship_stats: dict[tuple[str, str], dict] = {}
        
        # Init from pilot data
        for pid, p_info in all_pilots.items():
            ship_xws = p_info.get("ship_xws", "")
            faction = p_info.get("faction", "")
            
            if not ship_xws or not faction:
                continue
            
            try:
                faction_enum = Faction.from_xws(faction)
                faction_xws = faction_enum.value
            except (ValueError, AttributeError):
                continue # Skip unknown factions or handle generic
            
            faction_norm = faction_xws.lower().replace(" ", "").replace("-", "")
            if requested_ships and ship_xws not in requested_ships:
                continue
            if requested_factions and faction_norm not in requested_factions:
                continue

            key = (ship_xws, faction_xws)
            if key not in ship_stats:
                ship_stats[key] = {
                    "xws": ship_xws,
                    "faction_xws": faction_enum, # Enum
                    "games_count": 0,
                    "list_count": 0,
                    "different_lists_count": 0,
                    "wins": 0,
                    "_signatures": set()
                }

        for result, tournament in rows:
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            if allowed_formats and t_fmt not in allowed_formats: continue
            if not apply_tournament_filters(tournament, filters): continue
            
            xws = result.list_json
            if not xws or not isinstance(xws, dict): continue
            
            s_wins = result.swiss_wins or 0
            s_losses = result.swiss_losses or 0
            s_draws = result.swiss_draws or 0
            c_wins = result.cut_wins or 0
            c_losses = result.cut_losses or 0
            c_draws = result.cut_draws or 0
            
            wins = s_wins + c_wins
            games = wins + s_losses + s_draws + c_losses + c_draws
            
            sig = get_list_key(xws)
            
            # Identify ships in this list
            # Ship counts: if list has 2 TIEs, list_count for TIE +1? games_count +games?
            # Or +2?
            # Usually "Ship Stats" means "Performance of this chassis in this faction".
            # If I bring 2 TIEs, TIE Fighter presence is 1 list.
            # So unique ships per list.
            
            unique_ships = set()
            for p in xws.get("pilots", []):
                pid = p.get("id") or p.get("name")
                if not pid: continue
                
                # We need ship_xws for this pilot
                # Lookup in all_pilots
                if pid in all_pilots:
                    p_info = all_pilots[pid]
                    s_xws = p_info.get("ship_xws")
                    f_raw = p_info.get("faction")
                    if s_xws and f_raw:
                        try:
                            f_enum = Faction.from_xws(f_raw)
                            f_norm = f_enum.value.lower().replace(" ", "").replace("-", "")
                            if requested_ships and s_xws not in requested_ships:
                                continue
                            if requested_factions and f_norm not in requested_factions:
                                continue
                            unique_ships.add((s_xws, f_enum.value))
                        except: pass
            
            for s_xws, f_xws in unique_ships:
                key = (s_xws, f_xws)
                if key in ship_stats:
                    s = ship_stats[key]
                    s["games_count"] += games
                    s["list_count"] += 1
                    s["wins"] += wins
                    s["_signatures"].add(sig)

        results = []
        for key, data in ship_stats.items():
            if data["list_count"] > 0:
                data["different_lists_count"] = len(data.pop("_signatures"))
                results.append(data)
                
        # Sort
        def sort_key(item):
            if sort_criteria == SortingCriteria.POPULARITY:
                return (item["list_count"], item["games_count"])
            elif sort_criteria == SortingCriteria.GAMES:
                return item["games_count"]
            elif sort_criteria == SortingCriteria.WINRATE:
                return item["wins"] / item["games_count"] if item["games_count"] > 0 else 0
            elif sort_criteria == SortingCriteria.NAME:
                return item["xws"]
            return 0

        results.sort(key=sort_key, reverse=(sort_direction == SortDirection.DESCENDING))
        return results
