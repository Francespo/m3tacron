from enum import Enum

class RoundType(str, Enum):
    SWISS = "swiss"
    CUT = "cut"

    @property
    def label(self) -> str:
        match self:
            case RoundType.SWISS: return "Swiss"
            case RoundType.CUT: return "Cut"

    def __str__(self) -> str:
        return self.value
