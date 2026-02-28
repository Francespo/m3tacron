"""
Game format definitions and logic.
"""
from enum import StrEnum

class MacroFormat(StrEnum):
    V2_5 = "2.5"
    V2_0 = "2.0"
    OTHER = "other"

    @property
    def label(self) -> str:
        """Human-readable format name."""
        match self:
            case MacroFormat.V2_5: return "2.5"
            case MacroFormat.V2_0: return "2.0"
            case MacroFormat.OTHER: return "Unknown/Other"


    def formats(self) -> list[str]:
        """Return list of corresponding formats."""
        match self:
            case MacroFormat.V2_5: return [Format.AMG, Format.XWA]
            case MacroFormat.V2_0: return [Format.LEGACY_X2PO, Format.LEGACY_XLC, Format.FFG]
            case MacroFormat.OTHER: return [Format.OTHER]

class Format(StrEnum):
    # 2.5 Group
    AMG = "amg"
    XWA = "xwa"
    
    # 2.0 Group
    FFG = "ffg"
    LEGACY_X2PO = "legacy_x2po"
    LEGACY_XLC = "legacy_xlc"
    
    # Other
    OTHER = "other"

    @property
    def label(self) -> str:
        """Human-readable format name."""
        match self:
            case Format.AMG: return "AMG"
            case Format.XWA: return "XWA"
            case Format.LEGACY_X2PO: return "Legacy (X2PO)"
            case Format.LEGACY_XLC: return "Legacy (XLC)"
            case Format.FFG: return "FFG"
            case _: return "Other"
            
            
    @property
    def macro(self) -> MacroFormat:
        """High-level format category."""
        match self:
            case Format.AMG | Format.XWA:
                return MacroFormat.V2_5
            case Format.LEGACY_X2PO | Format.LEGACY_XLC | Format.FFG:
                return MacroFormat.V2_0
            case _:
                return MacroFormat.OTHER

def infer_format_from_xws(xws: dict) -> Format:
    """
    Infer format ID from XWS data based on vendor specific logic.
    """
    if not xws:
        return Format.OTHER

    vendor = xws.get("vendor", {})
    
    # 1. Check LBN (Launch Bay Next)
    if "lbn" in vendor:
        # LBN logic: check "ruleset" (field not inside vendor, but likely top level or implied?)
        # User said: "se è lbn deve guardare il 'ruleset'(il campo non è contenuto nel vendor)"
        # This implies checking xws['ruleset']?? Or xws['format']?
        # User said: "se è lbn deve guardare il "ruleset"(il campo non è contenuto nel vendor)" -> So look at xws.get("ruleset")? or xws.get("format")?
        # Usually XWS has a top level 'format' or 'ruleset' key.
        # User instructions: "Legacy = Legacy (X2PO), AMG = amg, xwa = XWA"
        
        # Checking top-level fields
        # Note: LBN often puts format info in 'description' or just implies it via points. 
        # But let's follow user instruction: check "ruleset" (outside vendor).
        
        ruleset = xws.get("ruleset", "").lower()
        # Fallback to 'format' if ruleset is empty? User said "ruleset".
        if not ruleset: 
            ruleset = xws.get("format", "").lower()

        if "legacy" in ruleset: return Format.LEGACY_X2PO
        if "amg" in ruleset: return Format.AMG
        if "xwa" in ruleset: return Format.XWA
        
        # Default for LBN if unclear? Maybe AMG?
        return Format.AMG 

    # 2. Check YASB
    if "yasb" in vendor:
        yasb = vendor["yasb"]
        combined = f"{yasb.get('builder', '')} {yasb.get('link', '')} {yasb.get('builder_url', '')}".lower()
        
        # Logic:
        # xwing-legacy.com = legacy x2po
        if "xwing-legacy.com" in combined: return Format.LEGACY_X2PO
        
        # lorenzosanti = legacy xlc
        if "lorenzosanti" in combined: return Format.LEGACY_XLC
        
        # raithos = FFG
        if "raithos" in combined: return Format.FFG
        
        # yasb.app
        if "yasb.app" in combined:
            # Check ruleset (outside vendor)
            ruleset = xws.get("ruleset", "").upper() # User said check "ruleset"
            if ruleset == "XWA": return Format.XWA
            return Format.AMG

    # 3. Fallback: Check top-level 'link', 'builder', or 'description' (Common in Longshanks XWS)
    combined_top = f"{xws.get('builder', '')} {xws.get('link', '')} {xws.get('description', '')}".lower()
    
    if "xwing-legacy.com" in combined_top: return Format.LEGACY_X2PO
    if "lorenzosanti" in combined_top: return Format.LEGACY_XLC
    if "raithos" in combined_top: return Format.FFG
    if "yasb.app" in combined_top:
        ruleset = xws.get("ruleset", "").upper()
        if ruleset == "XWA": return Format.XWA
        return Format.AMG
    
    if "launchbaynext.app" in combined_top or "lbn-xwing.web.app" in combined_top:
        ruleset = xws.get("ruleset", "").lower() or xws.get("format", "").lower()
        if "legacy" in ruleset: return Format.LEGACY_X2PO
        if "amg" in ruleset: return Format.AMG
        if "xwa" in ruleset: return Format.XWA
        return Format.AMG

    return Format.OTHER

