"""
Data sources for game content.
"""
from enum import StrEnum

class DataSource(StrEnum):
    LEGACY = "legacy"
    XWA = "xwa"

    @property
    def label(self) -> str:
        """Human-readable platform name."""
        match self:
            case DataSource.LEGACY: return "Legacy"
            case DataSource.XWA: return "XWA"
            
    def __str__(self) -> str:
        return self.value