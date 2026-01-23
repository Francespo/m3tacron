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
            case MacroFormat.V2_5: return [Format.AMG, Format.XWA, Format.XWA_EPIC]
            case MacroFormat.V2_0: return [Format.LEGACY_X2PO, Format.LEGACY_XLC, Format.FFG, Format.WILDSPACE, Format.LEGACY_EPIC]
            case MacroFormat.OTHER: return [Format.OTHER]

class Format(StrEnum):
    # 2.5 Group
    AMG = "amg"
    XWA = "xwa"
    XWA_EPIC = "xwa_epic"
    
    # 2.0 Group
    FFG = "ffg"
    LEGACY_X2PO = "legacy_x2po"
    LEGACY_XLC = "legacy_xlc"
    WILDSPACE = "wildspace"
    LEGACY_EPIC = "legacy_epic"
    
    # Other
    OTHER = "other"

    @property
    def label(self) -> str:
        """Human-readable format name."""
        match self:
            case Format.AMG: return "AMG"
            case Format.XWA: return "XWA"
            case Format.XWA_EPIC: return "XWA Epic"
            case Format.LEGACY_X2PO: return "Legacy (X2PO)"
            case Format.LEGACY_XLC: return "Legacy (XLC)"
            case Format.FFG: return "FFG"
            case Format.WILDSPACE: return "Wildspace"
            case Format.LEGACY_EPIC: return "Legacy Epic"
            case _: return "Other"
            
            
    @property
    def macro(self) -> MacroFormat:
        """High-level format category."""
        match self:
            case Format.AMG | Format.XWA | Format.XWA_EPIC:
                return MacroFormat.V2_5
            case Format.LEGACY_X2PO | Format.LEGACY_XLC | Format.FFG | Format.WILDSPACE | Format.LEGACY_EPIC:
                return MacroFormat.V2_0
            case _:
                return MacroFormat.OTHER

def infer_format_from_xws(xws: dict) -> Format:
    """
    Infer format ID from XWS data.
    """
    if not xws:
        return Format.OTHER

    # Check explicit format field
    fmt = xws.get("format", "").upper()
    if fmt == "EPIC":
        # Determine Epic variant
        vendor = xws.get("vendor", {})
        yasb = vendor.get("yasb", {})
        if yasb:
            builder = yasb.get("builder", "").lower()
            combined = f"{builder} {yasb.get('builder_url', '').lower()}"
            if "yasb.app" in combined: return Format.XWA_EPIC
            if "legacy" in combined or "xwing-legacy" in combined: return Format.LEGACY_EPIC
        
        ruleset = xws.get("ruleset", "").upper()
        if ruleset in ["LEGACY", "X2PO"]: return Format.LEGACY_EPIC
        if ruleset == "XWA": return Format.XWA_EPIC
        return Format.LEGACY_EPIC

    # Check explicit ruleset
    ruleset = xws.get("ruleset", "").upper()
    if ruleset == "XWA": return Format.XWA
    if ruleset == "AMG": return Format.AMG
    if ruleset in ["LEGACY", "X2PO"]: return Format.LEGACY_X2PO

    # Fallback to vendor metadata logic (re-using previous logic structure but returning Enums)
    vendor = xws.get("vendor", {})
    yasb = vendor.get("yasb", {})
    if yasb:
        combined = f"{yasb.get('builder', '')} {yasb.get('link', '')} {yasb.get('builder_url', '')}".lower()
        if "xwing-legacy.com" in combined or "yasb-legacy" in combined: return Format.LEGACY_X2PO
        if "lorenzosanti" in combined: return Format.LEGACY_XLC
        if "raithos" in combined: return Format.FFG
        if "yasb.app" in combined: return Format.XWA

    lbn = vendor.get("lbn", {})
    if lbn:
        combined = f"{lbn.get('builder', 'Launch Bay Next')} {lbn.get('link', '')}".lower()
        if "legacy" in combined: return Format.LEGACY_X2PO
        return Format.XWA
        
    return Format.OTHER

