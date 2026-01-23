"""
Faction definitions and utilities.
"""
from enum import StrEnum

class Faction(StrEnum):
    """
    X-Wing faction identifiers.
    """
    REBEL = "rebelalliance"
    EMPIRE = "galacticempire"
    SCUM = "scumandvillainy"
    RESISTANCE = "resistance"
    FIRST_ORDER = "firstorder"
    REPUBLIC = "galacticrepublic"
    SEPARATIST = "separatistalliance"
    UNKNOWN = "unknown"

    @property
    def label(self) -> str:
        """
        Human-readable faction name.
        """
        match self:
            case Faction.REBEL:
                return "Rebel Alliance"
            case Faction.EMPIRE:
                return "Galactic Empire"
            case Faction.SCUM:
                return "Scum and Villainy"
            case Faction.RESISTANCE:
                return "Resistance"
            case Faction.FIRST_ORDER:
                return "First Order"
            case Faction.REPUBLIC:
                return "Galactic Republic"
            case Faction.SEPARATIST:
                return "Separatist Alliance"
            case _:
                return "Unknown"


    @classmethod
    def from_xws(cls, value: str):
        """
        Convert raw XWS faction string to Faction enum.
        Handles labels, XWS IDs, and common aliases.
        """
        if not value:
            return cls.UNKNOWN
            
        # Normalize: lowercase and remove spaces/dashes
        normalized = value.lower().replace(" ", "").replace("-", "")
        
        # Check direct value match
        for faction in cls:
            if faction.value == normalized:
                return faction
        
        # Check common aliases/partial matches
        alias_map = {
            "rebel": cls.REBEL,
            "empire": cls.EMPIRE,
            "scum": cls.SCUM,
            "separatist": cls.SEPARATIST,
            "republic": cls.REPUBLIC,
            "firstorder": cls.FIRST_ORDER,
            "resistance": cls.RESISTANCE,
        }
        
        for alias, faction in alias_map.items():
            if alias in normalized:
                return faction
                
        return cls.UNKNOWN
