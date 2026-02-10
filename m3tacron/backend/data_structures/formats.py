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
    Infer format ID from XWS data.
    """
    if not xws:
        return Format.OTHER

    # Check explicit format field
    fmt = xws.get("format", "").upper()
    if fmt == "EPIC":
        return Format.OTHER

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

