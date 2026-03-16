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



    @classmethod
    def from_xws(cls, value: str) -> "Faction":
        """
        Convert any faction string (alias, label, or XWS ID) to official Faction enum.
        """
        if not value:
            return cls.UNKNOWN
            
        # Standard normalization: lowercase and remove spaces, dashes, underscores
        clean = value.lower().replace(" ", "").replace("-", "").replace("_", "")
        
        # 1. Check direct value matches (e.g. "rebelalliance")
        for faction in cls.__members__.values():
            if faction.value == clean:
                return faction
                
        # 2. Check common aliases and partial terms
        # Keys are normalized versions of potential inputs
        alias_map = {
            "rebel": cls.REBEL,
            "rebels": cls.REBEL,
            "rebelalliance": cls.REBEL,
            
            "empire": cls.EMPIRE,
            "galacticempire": cls.EMPIRE,
            "imperial": cls.EMPIRE,
            
            "scum": cls.SCUM,
            "scumandvillainy": cls.SCUM,
            "bountyhunter": cls.SCUM,
            
            "resistance": cls.RESISTANCE,
            
            "firstorder": cls.FIRST_ORDER,
            
            "republic": cls.REPUBLIC,
            "galacticrepublic": cls.REPUBLIC,
            
            "separatist": cls.SEPARATIST,
            "separatistalliance": cls.SEPARATIST,
            "cis": cls.SEPARATIST,
        }
        
        # Check for exact alias match
        if clean in alias_map:
            return alias_map[clean]
            
        # Check if any alias is contained within the string
        for alias, faction in alias_map.items():
            if alias in clean:
                return faction
                
        return cls.UNKNOWN
