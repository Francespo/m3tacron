"""
Filtering logic for card analytics.
"""
from ..models import Tournament

def filter_query(query, filters: dict):
    """
    Apply filters to the query.
    filters:Dictionary containing:
        - formats: list[str] (e.g. ["2.5", "amg"]) -> hierarchical logic handled by caller or simple list
        - date_start: str (YYYY-MM-DD)
        - date_end: str (YYYY-MM-DD)
    """
    if not filters:
        return query

    # Date Filters (Applied on Tournament)
    if filters.get("date_start"):
        query = query.where(Tournament.date >= filters["date_start"])
    if filters.get("date_end"):
        query = query.where(Tournament.date <= filters["date_end"])
        
    return query

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
