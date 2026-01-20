"""
Faction definitions and utilities.
"""
from enum import Enum

class Faction(str, Enum):
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

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_xws(cls, value):
        """
        Convert raw XWS faction string to Faction enum.
        """
        if not value:
            return cls.UNKNOWN
            
        # Normalize: lowercase and remove spaces/dashes
        # Why: XWS data can be inconsistent
        normalized = value.lower().replace(" ", "").replace("-", "")
        
        for faction in cls:
            if faction.value == normalized:
                return faction
        return cls.UNKNOWN
