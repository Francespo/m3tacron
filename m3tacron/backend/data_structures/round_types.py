"""
Tournament round types.
"""
from enum import Enum

class RoundType(str, Enum):
    SWISS = "swiss"
    CUT = "cut"

    @property
    def label(self) -> str:
        """Human-readable round type name."""
        match self:
            case RoundType.SWISS: return "Swiss"
            case RoundType.CUT: return "Cut"

    def __str__(self) -> str:
        return self.value
