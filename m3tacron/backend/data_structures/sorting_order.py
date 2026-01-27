"""
Sorting orders for game content.
"""
from enum import StrEnum

class SortingOrder(StrEnum):
    POPULARITY_ASCENDING = "popularity_asc"
    POPULARITY_DESCENDING = "popularity_desc"
    NAME_ASCENDING = "name_asc"
    NAME_DESCENDING = "name_desc"
    WINRATE_ASCENDING = "winrate_asc"
    WINRATE_DESCENDING = "winrate_desc"

    @property
    def label(self) -> str:
        """Human-readable sorting order name."""
        match self:
            case SortingOrder.POPULARITY_ASCENDING: return "Popularity Ascending"
            case SortingOrder.POPULARITY_DESCENDING: return "Popularity Descending"
            case SortingOrder.NAME_ASCENDING: return "Name Ascending"
            case SortingOrder.NAME_DESCENDING: return "Name Descending"
            case SortingOrder.WINRATE_ASCENDING: return "Winrate Ascending"
            case SortingOrder.WINRATE_DESCENDING: return "Winrate Descending"
            
    def __str__(self) -> str:
        return self.value