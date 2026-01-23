"""
Utility functions for text normalization and transformation.
"""

def normalize_location_string(value: str | None) -> str | None:
    """
    Normalize location strings to Title Case and strip whitespace.
    
    Args:
        value: Raw location string (e.g., city, state, region).
    
    Returns:
        Cleaned string in Title Case, or None if empty/invalid.
    
    Examples:
        >>> normalize_location_string("  roma ")
        'Roma'
        >>> normalize_location_string("ITALY  ")
        'Italy'
        >>> normalize_location_string("")
        None
        >>> normalize_location_string(None)
        None
    """
    if isinstance(value, str):
        cleaned = value.strip().title()
        return cleaned if cleaned else None
    return value
