"""
Format Detector for M3taCron.

Detects X-Wing tournament formats from XWS list data.
"""
from typing import Optional, Tuple, List, Dict, Any


# Format constants
MACRO_2_0 = "2.0"
MACRO_2_5 = "2.5"
MACRO_OTHER = "Other"

# Sub-format constants
SUB_FFG = "FFG"          # Original FFG rules (raithos)
SUB_X2PO = "X2PO"        # Community 2.0 (legacy)
SUB_XLC = "XLC"          # Lorenzo Santi variant
SUB_AMG = "AMG"          # Official AMG (deprecated)
SUB_XWA = "XWA"          # X-Wing Alliance
SUB_EPIC = "Epic"        # Epic battles
SUB_CUSTOM = "Custom"    # Unknown
SUB_UNKNOWN = "Unknown"


def detect_format_from_xws(xws: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Detects the tournament format (Macro/Sub) by analyzing an XWS squad list.
    
    It inspects 'builder' strings and 'vendor' specific metadata to classify the list
    into 2.0 (FFG, X2PO, XLC) or 2.5 (AMG, XWA) hierarchies.
    """
    # Verify input validity to prevent attribute errors
    if not xws:
        return (None, None)
    
    # Extract the builder string from the root dictionary
    # We use string conversion and lower() to allow case-insensitive (robust) matching
    builder = str(xws.get("builder", "")).lower()
    
    # Check the 'vendor' field which contains builder-specific structured data
    # This is the standard XWS way to store metadata, so we check it first for reliability
    vendor = xws.get("vendor", {})
    if isinstance(vendor, dict):
        # YASB specific logic: it places metadata under a 'yasb' key
        if "yasb" in vendor:
            yasb_data = vendor["yasb"]
            if isinstance(yasb_data, dict):
                # Concatenate builder info and link to form a searchable string
                builder += " " + str(yasb_data.get("builder", ""))
                builder += " " + str(yasb_data.get("link", ""))
        
        # LaunchBayNext specific logic: it places metadata under 'lbn' or 'launchbaynext'
        if "lbn" in vendor or "launchbaynext" in vendor:
            lbn_data = vendor.get("lbn") or vendor.get("launchbaynext")
            if isinstance(lbn_data, dict):
                # Explicitly add 'launchbaynext' and the ruleset to the builder string
                # This ensures consistent matching logic downstream
                builder += " launchbaynext " + str(lbn_data.get("ruleset", ""))
    
    # Filter out squad designers that do not carry format information
    # xwingsquaddesigner adds no value for format detection, so we early exit
    if "xwingsquaddesigner" in builder or "squaddesigner" in builder:
        return (None, None)
    
    # Detect Logic for LaunchBayNext
    # We check for explicit ruleset definitions provided by LBN
    if "launchbaynext" in builder or "lbn" in builder:
        ruleset = str(xws.get("ruleset", "")).lower()
        
        # Map specific ruleset strings to our internal format constants
        if ruleset == "xwa":
            return (MACRO_2_5, SUB_XWA)
        elif ruleset == "amg":
            return (MACRO_2_5, SUB_AMG)
        elif ruleset == "legacy":
            return (MACRO_2_0, SUB_X2PO)
            
        # Fallback: Inference from builder string if ruleset field is missing
        # Sometimes 'xwa' is part of the builder name/version string
        if "xwa" in builder:
            return (MACRO_2_5, SUB_XWA)
    
    # Detect Logic for YASB
    # We rely on specific keywords present in the URL or builder version string
    if "yasb" in builder:
        # Check for XWA specific indicators first (Priority detection)
        if "xwa" in builder or "2.5" in builder:
            return (MACRO_2_5, SUB_XWA)
            
        # Check for 2.0 legacy variants
        if "2.0" in builder:
            if "legacy" in builder:
                return (MACRO_2_0, SUB_X2PO)
            elif "raithos" in builder:
                return (MACRO_2_0, SUB_FFG)
            elif "lorenzosanti" in builder:
                return (MACRO_2_0, SUB_XLC)
            
            # Default to generic 2.0 Unknown if no specific link variant is found
            # This handles older YASB 2.0 list exports
            return (MACRO_2_0, SUB_UNKNOWN)
    
    # Fallback: Direct keyword matching for less common builders
    if "x2po" in builder:
        return (MACRO_2_0, SUB_X2PO)
    if "raithos" in builder:
        return (MACRO_2_0, SUB_FFG)
    
    return (None, None)


def detect_format_from_tournament_lists(
    xws_lists: List[Dict[str, Any]],
    sample_size: int = 10
) -> Tuple[str, str]:
    """
    Detect tournament format by sampling XWS lists from participants.
    
    Args:
        xws_lists: List of XWS dictionaries from tournament participants
        sample_size: Maximum number of lists to sample
        
    Returns:
        Tuple of (macro_format, sub_format) using majority voting
    """
    if not xws_lists:
        return (MACRO_OTHER, SUB_UNKNOWN)
    
    # Sample lists
    sample = xws_lists[:sample_size]
    
    format_votes: Dict[Tuple[str, str], int] = {}
    
    for xws in sample:
        macro, sub = detect_format_from_xws(xws)
        if macro and sub:
            key = (macro, sub)
            format_votes[key] = format_votes.get(key, 0) + 1
    
    if not format_votes:
        return (MACRO_OTHER, SUB_UNKNOWN)
    
    # Return most common format
    winner = max(format_votes.items(), key=lambda x: x[1])
    return winner[0]


def detect_format_from_listfortress(
    format_field: str,
    tournament_name: str,
    tournament_date: str,
    xws_lists: List[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    Detect format for ListFortress tournaments with heuristics.
    
    Args:
        format_field: ListFortress format field ("standard", "extended", "other")
        tournament_name: Tournament name for keyword matching
        tournament_date: Tournament date (YYYY-MM-DD) for recency check
        xws_lists: Optional list of XWS data to analyze
        
    Returns:
        Tuple of (macro_format, sub_format)
    """
    format_lower = format_field.lower() if format_field else ""
    name_lower = tournament_name.lower() if tournament_name else ""
    
    # First try XWS detection if available
    if xws_lists:
        macro, sub = detect_format_from_tournament_lists(xws_lists)
        if macro and sub != SUB_UNKNOWN:
            return (macro, sub)
    
    # Standard/Extended → 2.5 AMG (legacy support)
    if format_lower in ("standard", "extended"):
        # Could be mislabeled XWA - check name
        if "xwa" in name_lower or "alliance" in name_lower:
            return (MACRO_2_5, SUB_XWA)
        return (MACRO_2_5, SUB_AMG)
    
    # "Other" heuristics
    if format_lower == "other":
        # Check tournament name for clues
        if "xwa" in name_lower or "alliance" in name_lower:
            return (MACRO_2_5, SUB_XWA)
        if "epic" in name_lower:
            return (MACRO_OTHER, SUB_EPIC)
        if "legacy" in name_lower or "2.0" in name_lower:
            return (MACRO_2_0, SUB_X2PO)
        if "x2po" in name_lower:
            return (MACRO_2_0, SUB_X2PO)
        if "xlc" in name_lower or "lorenzosanti" in name_lower:
            return (MACRO_2_0, SUB_XLC)
        
        # Recent "Other" on ListFortress is ~90% XWA
        if tournament_date:
            try:
                from datetime import datetime
                date = datetime.strptime(tournament_date[:10], "%Y-%m-%d")
                cutoff = datetime(2025, 1, 1)  # Last year
                if date >= cutoff:
                    return (MACRO_2_5, SUB_XWA)
            except:
                pass
    
    return (MACRO_OTHER, SUB_UNKNOWN)


def get_format_display(macro: str, sub: str) -> str:
    """Get display string for format."""
    if sub == SUB_UNKNOWN:
        return macro
    return f"{macro} {sub}"
