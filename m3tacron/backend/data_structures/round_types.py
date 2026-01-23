"""
Tournament round types.
"""
from enum import StrEnum

class RoundType(StrEnum):
    SWISS = "swiss"
    CUT = "cut"

    @property
    def label(self) -> str:
        """Human-readable round type name."""
        match self:
            case RoundType.SWISS: return "Swiss"
            case RoundType.CUT: return "Cut"

