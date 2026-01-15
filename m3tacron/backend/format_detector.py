"""
Format Detector for M3taCron.

Analyzes XWS list data to determine the game format (2.0 vs 2.5 and sub-variants).
"""
from datetime import datetime
from .models import MacroFormat, SubFormat


def detect_format_from_xws(xws: dict) -> tuple[str | None, str | None]:
    """
    Analyzes an XWS squad list to determine the game format.
    
    Inspects builder strings and vendor metadata to classify into
    2.0 (FFG, X2PO, XLC) or 2.5 (AMG, XWA) categories.
    """
    if not xws:
        return (None, None)
    
    builder = str(xws.get("builder", "")).lower()
    
    # Extract builder info from 'vendor' field (XWS standard)
    vendor = xws.get("vendor", {})
    if isinstance(vendor, dict):
        if "yasb" in vendor:
            yasb_data = vendor["yasb"]
            if isinstance(yasb_data, dict):
                builder += " " + str(yasb_data.get("builder", ""))
                builder += " " + str(yasb_data.get("link", ""))
        
        if "lbn" in vendor or "launchbaynext" in vendor:
            lbn_data = vendor.get("lbn") or vendor.get("launchbaynext")
            if isinstance(lbn_data, dict):
                builder += " launchbaynext " + str(lbn_data.get("ruleset", ""))
    
    # xwingsquaddesigner cannot be used for format detection
    if "xwingsquaddesigner" in builder or "squaddesigner" in builder:
        return (None, None)
    
    # LaunchBayNext detection via ruleset field
    if "launchbaynext" in builder or "lbn" in builder:
        ruleset = str(xws.get("ruleset", "")).lower()
        
        if ruleset == "xwa":
            return (MacroFormat.V2_5.value, SubFormat.XWA.value)
        elif ruleset == "amg":
            return (MacroFormat.V2_5.value, SubFormat.AMG.value)
        elif ruleset == "legacy":
            return (MacroFormat.V2_0.value, SubFormat.X2PO.value)
        
        if "xwa" in builder:
            return (MacroFormat.V2_5.value, SubFormat.XWA.value)
    
    # YASB detection via keywords in builder/URL
    if "yasb" in builder:
        if "xwa" in builder or "2.5" in builder:
            return (MacroFormat.V2_5.value, SubFormat.XWA.value)
        
        if "2.0" in builder:
            if "legacy" in builder:
                return (MacroFormat.V2_0.value, SubFormat.X2PO.value)
            elif "raithos" in builder:
                return (MacroFormat.V2_0.value, SubFormat.FFG.value)
            elif "lorenzosanti" in builder:
                return (MacroFormat.V2_0.value, SubFormat.XLC.value)
            
            return (MacroFormat.V2_0.value, SubFormat.UNKNOWN.value)
    
    # Direct keyword fallback
    if "x2po" in builder:
        return (MacroFormat.V2_0.value, SubFormat.X2PO.value)
    if "raithos" in builder:
        return (MacroFormat.V2_0.value, SubFormat.FFG.value)
    
    return (None, None)


def detect_format_from_tournament_lists(
    xws_lists: list[dict],
    sample_size: int = 10
) -> tuple[str, str]:
    """
    Determines format by sampling XWS lists and using majority voting.
    """
    if not xws_lists:
        return (MacroFormat.OTHER.value, SubFormat.UNKNOWN.value)
    
    sample = xws_lists[:sample_size]
    format_votes: dict[tuple[str, str], int] = {}
    
    for xws in sample:
        macro, sub = detect_format_from_xws(xws)
        if macro and sub:
            key = (macro, sub)
            format_votes[key] = format_votes.get(key, 0) + 1
    
    if not format_votes:
        return (MacroFormat.OTHER.value, SubFormat.UNKNOWN.value)
    
    winner = max(format_votes.items(), key=lambda x: x[1])
    return winner[0]


def detect_format_from_listfortress(
    format_field: str,
    tournament_name: str,
    tournament_date: str,
    xws_lists: list[dict] | None = None
) -> tuple[str, str]:
    """
    Detects format for ListFortress tournaments using heuristics.
    
    Falls back to XWS analysis, then name keywords, then recency inference.
    """
    format_lower = format_field.lower() if format_field else ""
    name_lower = tournament_name.lower() if tournament_name else ""
    
    # Primary: XWS-based detection
    if xws_lists:
        macro, sub = detect_format_from_tournament_lists(xws_lists)
        if macro and sub != SubFormat.UNKNOWN.value:
            return (macro, sub)
    
    # Standard/Extended are legacy AMG labels
    if format_lower in ("standard", "extended"):
        if "xwa" in name_lower or "alliance" in name_lower:
            return (MacroFormat.V2_5.value, SubFormat.XWA.value)
        return (MacroFormat.V2_5.value, SubFormat.AMG.value)
    
    # "Other" category requires deeper heuristics
    if format_lower == "other":
        if "xwa" in name_lower or "alliance" in name_lower:
            return (MacroFormat.V2_5.value, SubFormat.XWA.value)
        if "epic" in name_lower:
            return (MacroFormat.OTHER.value, SubFormat.EPIC.value)
        if "legacy" in name_lower or "2.0" in name_lower:
            return (MacroFormat.V2_0.value, SubFormat.X2PO.value)
        if "x2po" in name_lower:
            return (MacroFormat.V2_0.value, SubFormat.X2PO.value)
        if "xlc" in name_lower or "lorenzosanti" in name_lower:
            return (MacroFormat.V2_0.value, SubFormat.XLC.value)
        
        # Recent "Other" tournaments are typically XWA
        if tournament_date:
            try:
                date = datetime.strptime(tournament_date[:10], "%Y-%m-%d")
                cutoff = datetime(2025, 1, 1)
                if date >= cutoff:
                    return (MacroFormat.V2_5.value, SubFormat.XWA.value)
            except ValueError:
                pass
    
    return (MacroFormat.OTHER.value, SubFormat.UNKNOWN.value)


def get_format_display(macro: str, sub: str) -> str:
    """Formats the macro/sub tuple as a display string."""
    if sub == SubFormat.UNKNOWN.value:
        return macro
    return f"{macro} {sub}"
