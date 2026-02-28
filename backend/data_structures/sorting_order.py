"""
Sorting criteria and direction for game content.
"""
from enum import StrEnum

class SortDirection(StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"

class SortingCriteria(StrEnum):
    POPULARITY = "popularity"
    NAME = "name"
    WINRATE = "win_rate"
    COST = "cost"
    GAMES = "games"
    LOADOUT = "loadout"

    @property
    def label(self) -> str:
        """Human-readable sorting name."""
        match self:
            case SortingCriteria.POPULARITY: return "Popularity"
            case SortingCriteria.NAME: return "Name"
            case SortingCriteria.WINRATE: return "Win Rate"
            case SortingCriteria.COST: return "Cost"
            case SortingCriteria.GAMES: return "Games"
            case SortingCriteria.LOADOUT: return "Loadout"
            
    @classmethod
    def from_label(cls, label: str) -> "SortingCriteria":
        for member in cls:
            if member.label == label:
                return member
        return cls.POPULARITY # Default
            
    def __str__(self) -> str:
        return self.value