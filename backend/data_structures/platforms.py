"""
Platform definitions for tournament sources.
"""
from enum import StrEnum

class Platform(StrEnum):
    LONGSHANKS = "longshanks"
    LISTFORTRESS = "listfortress"
    ROLLBETTER = "rollbetter"
    UNKNOWN = "unknown"

    @property
    def label(self) -> str:
        """Human-readable platform name."""
        match self:
            case Platform.LONGSHANKS: return "Longshanks"
            case Platform.LISTFORTRESS: return "ListFortress"
            case Platform.ROLLBETTER: return "Rollbetter"
