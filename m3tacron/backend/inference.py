"""
Logic for inferring game format from XWS data.
"""

from m3tacron.backend.models import GameFormat

def infer_format_from_xws(xws: dict[str, any]) -> str:
    """
    Infer the game format from XWS data based on vendor/builder info.
    
    Logic:
    - YASB Legacy (xwing-legacy.com) -> X2PO
    - YASB LorenzoSanti (lorenzosanti.github.io) -> XLC
    - YASB Raithos (raithos.github.io) -> FFG
    - YASB 2.5 (yasb.app) -> XWA (or AMG if specified)
    - Launch Bay Next -> Check if 'legacy' tag/text -> X2PO, else likely XWA
    
    Returns:
        One of the GameFormat enum values as string, or GameFormat.OTHER
    """
    if not xws:
        return GameFormat.OTHER.value

    # 0. Check top-level ruleset first (most reliable if present)
    ruleset = xws.get("ruleset", "").upper()
    if ruleset == "XWA":
        return GameFormat.XWA.value
    if ruleset == "AMG":
        return GameFormat.AMG.value
    if ruleset in ["LEGACY", "X2PO"]:
        return GameFormat.LEGACY_X2PO.value

    # Check 'vendor' field
    vendor = xws.get("vendor", {})
    
    # 1. YASB Logic
    yasb = vendor.get("yasb", {})
    if yasb:
        builder = yasb.get("builder", "").lower()
        link = yasb.get("link", "").lower()
        builder_url = yasb.get("builder_url", "").lower()
        
        # Combined string for easier searching
        combined = f"{builder} {link} {builder_url}"
        
        if "xwing-legacy.com" in combined or "yasb-legacy" in combined:
            return GameFormat.LEGACY_X2PO.value
            
        # Matches lorenzosanti.github.io and variants (e.g. lorenzosanti359-beep.github.io)
        if "lorenzosanti" in combined:
            return GameFormat.LEGACY_XLC.value
            
        if "raithos" in combined:
            return GameFormat.FFG.value
            
        if "yasb.app" in combined:
            # Default for yasb.app is XWA/2.5 (ruleset check handled at top)
            return GameFormat.XWA.value

    # 2. Launch Bay Next Logic
    lbn = vendor.get("lbn", {})
    if lbn:
        # LBN links often don't contain domain info in the same way, but let's check keys
        builder = lbn.get("builder", "Launch Bay Next").lower()
        link = lbn.get("link", "").lower()
        
        # Fallback check for "legacy" in LBN builder/link if ruleset wasn't found at top
        if "legacy" in builder or "legacy" in link:
            return GameFormat.LEGACY_X2PO.value
            
        # Default LBN is usually current standard (XWA)
        return GameFormat.XWA.value
        
    return GameFormat.OTHER.value
