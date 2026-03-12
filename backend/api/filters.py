from fastapi import Query
from typing import Optional, List
from pydantic import BaseModel, Field

class BaseFilterParams(BaseModel):
    data_source: str = Query("xwa", description="Data source: xwa or legacy")
    page: int = Query(0, ge=0)
    size: int = Query(20, ge=1, le=100)

class TournamentFilterParams(BaseFilterParams):
    sort_metric: str = Query("Date")
    sort_direction: str = Query("desc")
    search: Optional[str] = Query(None)
    formats: Optional[List[str]] = Query(None)
    factions: Optional[List[str]] = Query(None)
    ships: Optional[List[str]] = Query(None)
    continent: Optional[List[str]] = Query(None)
    country: Optional[List[str]] = Query(None)
    city: Optional[List[str]] = Query(None)
    platforms: Optional[List[str]] = Query(None)
    date_start: Optional[str] = Query(None)
    date_end: Optional[str] = Query(None)
    player_count_min: Optional[int] = Query(None)
    player_count_max: Optional[int] = Query(None)

class PilotFilterParams(BaseFilterParams):
    sort_metric: str = Query("Popularity")
    sort_direction: str = Query("desc")
    search: Optional[str] = Query(None)
    formats: Optional[List[str]] = Query(None)
    factions: Optional[List[str]] = Query(None)
    ships: Optional[List[str]] = Query(None)
    continent: Optional[List[str]] = Query(None)
    country: Optional[List[str]] = Query(None)
    city: Optional[List[str]] = Query(None)
    platforms: Optional[List[str]] = Query(None)
    date_start: Optional[str] = Query(None)
    date_end: Optional[str] = Query(None)
    player_count_min: Optional[int] = Query(None)
    player_count_max: Optional[int] = Query(None)
    points_min: Optional[int] = Field(None, ge=0)
    points_max: Optional[int] = Field(None, ge=0)
    ship: Optional[str] = None

class ShipFilterParams(BaseFilterParams):
    sort_metric: str = Query("Popularity")
    sort_direction: str = Query("desc")
    search: Optional[str] = Query(None)
    formats: Optional[List[str]] = Query(None)
    factions: Optional[List[str]] = Query(None)
    ships: Optional[List[str]] = Query(None)
    continent: Optional[List[str]] = Query(None)
    country: Optional[List[str]] = Query(None)
    city: Optional[List[str]] = Query(None)
    platforms: Optional[List[str]] = Query(None)
    date_start: Optional[str] = Query(None)
    date_end: Optional[str] = Query(None)
    player_count_min: Optional[int] = Query(None)
    player_count_max: Optional[int] = Query(None)

class SquadronFilterParams(BaseFilterParams):
    sort_metric: str = Query("Games")
    sort_direction: str = Query("desc")
    formats: Optional[List[str]] = Query(None)
    factions: Optional[List[str]] = Query(None)
    ships: Optional[List[str]] = Query(None)
    min_games: int = Query(0, ge=0)
    ship: Optional[str] = None
