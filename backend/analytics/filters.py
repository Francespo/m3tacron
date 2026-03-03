"""
Filtering logic for card analytics.
"""
from ..models import Tournament

def filter_query(query, filters: dict):
    """
    Apply SQL-level filters to the query.

    Args:
        query: SQLModel select query joining PlayerResult and Tournament.
        filters: Dictionary containing optional keys:
            - date_start: str (YYYY-MM-DD)
            - date_end: str (YYYY-MM-DD)
            - platform: str (e.g. "longshanks") — exact match on Tournament.platform
            - player_count_min: int — minimum Tournament.player_count
            - player_count_max: int — maximum Tournament.player_count
    """
    if not filters:
        return query

    # Date Filters
    if filters.get("date_start"):
        query = query.where(Tournament.date >= filters["date_start"])
    if filters.get("date_end"):
        query = query.where(Tournament.date <= filters["date_end"])

    # Platform Filter
    if filters.get("platform"):
        query = query.where(Tournament.platform == filters["platform"])

    # Player Count Range Filters
    if filters.get("player_count_min") is not None:
        query = query.where(Tournament.player_count >= int(filters["player_count_min"]))
    if filters.get("player_count_max") is not None:
        query = query.where(Tournament.player_count <= int(filters["player_count_max"]))

    return query


def apply_tournament_filters(tournament: Tournament, filters: dict) -> bool:
    """
    Apply Python-level tournament filters that cannot be expressed in SQL
    (e.g. location stored as JSON blob).

    Returns True if the tournament passes all filters, False otherwise.

    Args:
        tournament: Tournament model instance.
        filters: Dictionary containing optional keys:
            - continent: list[str] — allowed continents
            - country: list[str] — allowed countries
            - city: list[str] — allowed cities
    """
    # Location Filters
    filter_continents = filters.get("continent")
    filter_countries = filters.get("country")
    filter_cities = filters.get("city")

    if filter_continents or filter_countries or filter_cities:
        loc = tournament.location
        if not loc:
            return False

        if filter_continents:
            allowed = set(filter_continents)
            if not loc.continent or loc.continent not in allowed:
                return False

        if filter_countries:
            allowed = set(filter_countries)
            if not loc.country or loc.country not in allowed:
                return False

        if filter_cities:
            allowed = set(filter_cities)
            if not loc.city or loc.city not in allowed:
                return False

    return True

def check_format_filter(tournament: Tournament, format_selection: dict[str, bool] | list[str] | None) -> bool:
    """
    Check if a tournament matches the hierarchical format filter.
    format_selection: dict mapping format/macro values to boolean (active)
                      e.g. {"2.5": True, "amg": True, "2.0": False}
                      OR list of strings ["xwa", "amg"]
    """
    if not format_selection:
        return True
    
    t_format_val = tournament.format.value if hasattr(tournament.format, "value") else (tournament.format or "other")
    
    if isinstance(format_selection, (list, set)):
        return t_format_val in format_selection
        
    return format_selection.get(t_format_val, False)

def get_active_formats(format_selection: dict[str, bool] | list[str] | None) -> list[str]:
    """
    Normalize format selection to a simple list of active format keys.
    """
    if not format_selection:
        return []
    
    if isinstance(format_selection, (list, set)):
        return list(format_selection)
    
    if isinstance(format_selection, dict):
        return [k for k, v in format_selection.items() if v]
    
    return []
