"""
YASB URL Generator for M3taCron.

Converts XWS squadron data to YASB (Yet Another Squad Builder) URLs
with correct builder version based on format.
"""
from urllib.parse import urlencode, quote
from ..data_structures.formats import Format


def get_yasb_base_url(tournament_format: str | Format) -> str:
    """
    Get the correct YASB base URL for a tournament format.
    
    Args:
        tournament_format: Format enum or string (e.g., "xwa", "legacy_x2po", "legacy_xlc")
    
    Returns:
        Base URL for the appropriate YASB builder
    """
    if isinstance(tournament_format, str):
        tournament_format = tournament_format.lower()
    
    # Map format to YASB version
    if tournament_format in [Format.XWA, Format.AMG, Format.XWA_EPIC, "xwa", "amg", "xwa_epic"]:
        return "https://yasb.app"
    elif tournament_format in [Format.LEGACY_XLC, "legacy_xlc"]:
        return "https://lorenzosanti359-beep.github.io/X-wing-builder-madness"
    else:
        # Legacy X2PO, FFG, Wildspace, Legacy Epic all use xwing-legacy.com
        return "https://xwing-legacy.com"


def xws_to_yasb_url(xws: dict, tournament_format: str | Format) -> str:
    """
    Convert XWS JSON to a YASB URL.
    
    Args:
        xws: XWS dictionary with faction, pilots, etc.
        tournament_format: Format enum or string to determine YASB version
    
    Returns:
        Full YASB URL to view the squadron
    """
    if not xws or not isinstance(xws, dict):
        return ""
    
    base_url = get_yasb_base_url(tournament_format)
    
    # Extract faction from XWS
    faction = xws.get("faction", "")
    if not faction:
        return ""
    
    # Get the raw XWS 'd' parameter from vendor if available, otherwise build it
    # YASB stores the encoded squadron data in vendor.yasb
    vendor = xws.get("vendor", {})
    yasb_vendor = vendor.get("yasb", {})
    
    # Try to get the link directly
    existing_link = yasb_vendor.get("link", "")
    if existing_link and base_url in existing_link:
        return existing_link
    
    # If no direct link, we need to construct the URL
    # YASB uses URL parameters: ?f=Faction&d=encodedData&sn=SquadronName&obs=obstacles
    params = {
        "f": faction
    }
    
    # Add squadron name if available
    squad_name = xws.get("name", "")
    if squad_name:
        params["sn"] = squad_name
    
    # For XWS to YASB, we need the 'd' parameter which is the encoded squadron data
    # This is complex and typically YASB generates this from their builder
    # For now, we'll try to extract it from the vendor data or return empty if not available
    yasb_data = yasb_vendor.get("builder_url", "")
    if yasb_data:
        # Extract the 'd' parameter from builder_url if it exists
        if "d=" in yasb_data:
            import re
            match = re.search(r'd=([^&]+)', yasb_data)
            if match:
                params["d"] = match.group(1)
    
    # If we still don't have the 'd' parameter, we can't build a valid YASB URL
    # Return the vendor link if available
    if "d" not in params:
        link_from_vendor = yasb_vendor.get("link", "")
        if link_from_vendor:
            return link_from_vendor
        # Otherwise return empty - we can't construct a valid YASB URL without the data parameter
        return ""
    
    # Build the full URL
    query_string = urlencode(params, quote_via=quote)
    return f"{base_url}?{query_string}"


def get_xws_string(xws: dict) -> str:
    """
    Convert XWS dict to a formatted JSON string for export.
    
    Args:
        xws: XWS dictionary
    
    Returns:
        Pretty-printed JSON string
    """
    import json
    return json.dumps(xws, indent=2, ensure_ascii=False)
