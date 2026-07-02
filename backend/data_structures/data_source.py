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


def parse_data_source(value: str) -> DataSource:
    """
    Parse a data source string, falling back to DataSource.XWA on error.

    Centralises the "try DataSource(value) except: XWA" pattern used in
    several endpoints so the fallback behaviour stays consistent.
    """
    try:
        return DataSource(value)
    except (ValueError, KeyError):
        return DataSource.XWA