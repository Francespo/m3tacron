"""
Ship Analytics - Aggregation Logic for Ships.

Aggregates statistics (win rate, popularity, games) per ship per faction.
"""
from sqlmodel import Session, select
from ..database import engine
from ..models import PlayerResult, Tournament
from ..utils.xwing_data.pilots import load_all_pilots
from ..data_structures.factions import Faction
from ..data_structures.formats import Format
from ..data_structures.data_source import DataSource
from .filters import filter_query
from ..data_structures.sorting_order import SortingCriteria, SortDirection


def aggregate_ship_stats(
    filters: dict,
    sort_criteria: SortingCriteria = SortingCriteria.POPULARITY,
    sort_direction: SortDirection = SortDirection.DESCENDING,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics for ships grouped by faction.
    
    Args:
        filters: Dict with optional keys:
            - allowed_formats: list of format strings
            - date_start, date_end: date range strings
            - faction: list of faction labels to filter by
            - ship: list of ship XWS to filter by
            - continent: list of continents
            - country: list of countries
            - city: list of cities
        sort_criteria: How to sort results (POPULARITY, WINRATE, GAMES)
        sort_direction: ASC or DESC
        data_source: XWA or Legacy
        
    Returns:
        List of dicts with ship stats per faction:
        {ship_name, ship_xws, faction, faction_xws, win_rate, popularity, games, wins}
    """
    with Session(engine) as session:
        # Load tournament results
        query = select(PlayerResult, Tournament).where(
            PlayerResult.tournament_id == Tournament.id
        )
        query = filter_query(query, filters)
        rows = session.exec(query).all()
        
        # Load all pilots to build ship-faction mapping
        all_pilots = load_all_pilots(data_source)
        
        
        allowed_formats = filters.get("allowed_formats", None)
        allowed_date_start = filters.get("date_start", None)
        allowed_date_end = filters.get("date_end", None)
        
        # Location Filters
        allowed_continents = set(filters.get("continent", []))
        allowed_countries = set(filters.get("country", []))
        allowed_cities = set(filters.get("city", []))
        
        # Build ship stats: key = (ship_xws, faction_xws)
        # Value = {ship_name, ship_xws, faction, faction_xws, wins, games, lists}
        ship_stats: dict[tuple[str, str], dict] = {}
        
        # Initialize from pilot data to get all ships
        for pid, p_info in all_pilots.items():
            ship_xws = p_info.get("ship_xws", "")
            ship_name = p_info.get("ship", "Unknown Ship")
            faction = p_info.get("faction", "")
            
            if not ship_xws or not faction:
                continue
                
            # Normalize faction to xws format
            try:
                faction_enum = Faction.from_xws(faction)
                faction_xws = faction_enum.xws  
                faction_display = faction_enum.value
            except (ValueError, AttributeError):
                faction_xws = faction.lower().replace(" ", "")
                faction_display = faction
            
            key = (ship_xws, faction_xws)
            if key not in ship_stats:
                ship_stats[key] = {
                    "ship_name": ship_name,
                    "ship_xws": ship_xws,
                    "faction": faction_display,
                    "faction_xws": faction_xws,
                    "wins": 0,
                    "games": 0,
                    "lists": set(),  # Track unique lists
                }
        
        # Aggregate stats from tournament data
        for result, tournament in rows:
            # Format filter
            t_fmt_raw = tournament.format
            t_fmt = t_fmt_raw.value if hasattr(t_fmt_raw, 'value') else (t_fmt_raw or "other")
            
            if allowed_formats is not None and t_fmt not in allowed_formats:
                continue
            
            # Date Filter
            t_date = str(tournament.date) if tournament.date else ""
            if allowed_date_start and t_date < allowed_date_start:
                continue
            if allowed_date_end and t_date > allowed_date_end:
                continue

            # Location Filtering
            if allowed_continents or allowed_countries or allowed_cities:
                loc = tournament.location
                if not loc:
                    continue
                if allowed_continents and (not loc.continent or loc.continent not in allowed_continents):
                    continue
                if allowed_countries and (not loc.country or loc.country not in allowed_countries):
                    continue
                if allowed_cities and (not loc.city or loc.city not in allowed_cities):
                    continue
            
            xws = result.list_json
            if not xws or not isinstance(xws, dict):
                continue
            
            # Get list faction
            list_faction = xws.get("faction", "unknown")
            try:
                faction_enum = Faction.from_xws(list_faction)
                faction_xws = faction_enum.xws
            except (ValueError, AttributeError):
                faction_xws = list_faction.lower().replace(" ", "")
            
            s_wins = result.swiss_wins or 0
            s_losses = result.swiss_losses or 0
            s_draws = result.swiss_draws or 0
            
            c_wins = result.cut_wins or 0
            c_losses = result.cut_losses or 0
            c_draws = result.cut_draws or 0
            
            wins = s_wins + c_wins
            games = wins + s_losses + c_losses + s_draws + c_draws

            
            # Track which ships appeared in this list
            list_id = (result.tournament_id, result.player_name)
            ships_in_list = set()
            
            # Track which ships appeared in this list
            list_id = (result.tournament_id, result.player_name)
            ships_in_list = set()
            
            for pilot in xws.get("pilots", []):
                pid = pilot.get("id") or pilot.get("name")
                if not pid:
                    continue
                    
                p_info = all_pilots.get(pid, {})
                ship_xws = p_info.get("ship_xws", "")
                
                if not ship_xws:
                    continue

                # Legality check to match Cards Browser visibility
                is_legal = p_info.get("valid_in_standard", False)
                is_wild = p_info.get("wildspace", False)
                is_epic = p_info.get("epic", False)
                
                show_pilot = False
                if allowed_formats:
                    if "xwa" in allowed_formats or "amg" in allowed_formats:
                        if is_legal:
                            show_pilot = True
                    if "wildspace" in allowed_formats and is_wild:
                        show_pilot = True
                    if ("xwa_epic" in allowed_formats or "legacy_epic" in allowed_formats) and is_epic:
                        show_pilot = True
                    
                    if data_source == DataSource.LEGACY:
                        legacy_keys = {"legacy_x2po", "legacy_xlc", "ffg"}
                        if not legacy_keys.isdisjoint(allowed_formats):
                            show_pilot = True
                else:
                    # Fallback visibility if no formats selected
                    show_pilot = is_legal or is_wild
                
                if not show_pilot:
                    continue
                
                key = (ship_xws, faction_xws)
                if key in ship_stats:
                    # Add wins/games for each pilot instance
                    ship_stats[key]["wins"] += wins
                    ship_stats[key]["games"] += games
                    ships_in_list.add(key)
            
            # Count unique lists per ship
            for key in ships_in_list:
                ship_stats[key]["lists"].add(list_id)
        
        # Build results
        results = []
        for key, data in ship_stats.items():
            popularity = len(data["lists"])
            games = data["games"]
            wins = data["wins"]
            
            if games > 0:
                win_rate = round((wins / games) * 100, 1)
            else:
                win_rate = "NA"
            
            results.append({
                "ship_name": data["ship_name"],
                "ship_xws": data["ship_xws"],
                "faction": data["faction"],
                "faction_xws": data["faction_xws"],
                "win_rate": win_rate,
                "popularity": popularity,
                "games": games,
            })
        
        # Apply faction filter (filter by faction label)
        faction_filter = filters.get("faction", [])
        if faction_filter:
            # Normalize faction labels for comparison
            def norm_faction(f): 
                return f.lower().replace(" ", "").replace("-", "")
            norm_filter = {norm_faction(f) for f in faction_filter}
            
            filtered_results = []
            for r in results:
                # Match against faction label or xws
                r_faction_norm = norm_faction(r["faction"])
                r_faction_xws_norm = norm_faction(r["faction_xws"])
                if r_faction_norm in norm_filter or r_faction_xws_norm in norm_filter:
                    filtered_results.append(r)
            results = filtered_results
        
        # Apply ship filter (filter by ship XWS)
        ship_filter = filters.get("ship", [])
        if ship_filter:
            results = [r for r in results if r["ship_xws"] in ship_filter]
        
        # Sorting
        reverse = (sort_direction == SortDirection.DESCENDING)
        
        def winrate_sort_key(x):
            wr = x["win_rate"]
            if wr == "NA":
                return -1.0
            return float(wr)
        
        if sort_criteria == SortingCriteria.WINRATE:
            results.sort(key=lambda x: (winrate_sort_key(x), x["games"]), reverse=reverse)
        elif sort_criteria == SortingCriteria.GAMES:
            results.sort(key=lambda x: x["games"], reverse=reverse)
        else:  # POPULARITY (default)
            results.sort(key=lambda x: x["popularity"], reverse=reverse)
        
        return results

