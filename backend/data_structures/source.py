"""
Source definitions for tournament data origins.
"""
from enum import StrEnum

class Source(StrEnum):
    LONGSHANKS = "longshanks"
    LISTFORTRESS = "listfortress"
    ROLLBETTER = "rollbetter"
    UNKNOWN = "unknown"

    @property
    def label(self) -> str:
        """Human-readable source name."""
        match self:
            case Source.LONGSHANKS: return "Longshanks"
            case Source.LISTFORTRESS: return "ListFortress"
            case Source.ROLLBETTER: return "Rollbetter"
            case _: return "Unknown"
