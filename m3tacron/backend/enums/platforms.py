"""
Platform definitions for tournament sources.
"""
from enum import Enum

class Platform(str, Enum):
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
    def __str__(self) -> str:
        return self.value
