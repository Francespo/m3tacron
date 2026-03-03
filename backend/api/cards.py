from fastapi import APIRouter, Query, Depends
from typing import Optional, List, Dict, Any
from ..analytics.core import aggregate_card_stats
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from .schemas import PaginatedPilotsResponse, PaginatedUpgradesResponse

router = APIRouter(prefix="/api/cards", tags=["Cards"])

def _build_filters(
    formats: Optional[List[str]] = None,
    factions: Optional[List[str]] = None,
    ships: Optional[List[str]] = None,
    initiatives: Optional[List[int]] = None,
    upgrade_types: Optional[List[str]] = None,
    search_text: str = "",
    points_min: Optional[int] = None,
    points_max: Optional[int] = None,
    loadout_min: Optional[int] = None,
    loadout_max: Optional[int] = None,
    hull_min: Optional[int] = None,
    hull_max: Optional[int] = None,
    shields_min: Optional[int] = None,
    shields_max: Optional[int] = None,
    agility_min: Optional[int] = None,
    agility_max: Optional[int] = None,
    attack_min: Optional[int] = None,
    attack_max: Optional[int] = None,
    init_min: Optional[int] = None,
    init_max: Optional[int] = None,
    is_unique: bool = False,
    is_limited: bool = False,
    is_not_limited: bool = False,
    base_sizes: Optional[List[str]] = None,
    continent: Optional[List[str]] = None,
    country: Optional[List[str]] = None,
    city: Optional[List[str]] = None,
) -> dict:
    
    # Base sizes mapping
    sizes_dict = {}
    if base_sizes:
        for s in base_sizes:
            sizes_dict[s] = True

    return {
        "allowed_formats": formats,
        "search_text": search_text,
        "faction": factions,
        "ship": ships,
        "initiative": initiatives,
        "upgrade_type": upgrade_types,
        "points_min": points_min,
        "points_max": points_max,
        "loadout_min": loadout_min,
        "loadout_max": loadout_max,
        "hull_min": hull_min,
        "hull_max": hull_max,
        "shields_min": shields_min,
        "shields_max": shields_max,
        "agility_min": agility_min,
        "agility_max": agility_max,
        "attack_min": attack_min,
        "attack_max": attack_max,
        "init_min": init_min,
        "init_max": init_max,
        "is_unique": is_unique,
        "is_limited": is_limited,
        "is_not_limited": is_not_limited,
        "base_sizes": sizes_dict,
        "continent": continent,
        "country": country,
        "city": city,
        "include_epic": False
    }


@router.get("/pilots", response_model=PaginatedPilotsResponse)
def get_pilots(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Popularity"),
    sort_direction: str = Query("desc"),
    
    formats: Optional[List[str]] = Query(None),
    factions: Optional[List[str]] = Query(None),
    ships: Optional[List[str]] = Query(None),
    initiatives: Optional[List[int]] = Query(None),
    search_text: str = Query(""),
    points_min: Optional[int] = Query(None),
    points_max: Optional[int] = Query(None),
    loadout_min: Optional[int] = Query(None),
    loadout_max: Optional[int] = Query(None),
    hull_min: Optional[int] = Query(None),
    hull_max: Optional[int] = Query(None),
    shields_min: Optional[int] = Query(None),
    shields_max: Optional[int] = Query(None),
    agility_min: Optional[int] = Query(None),
    agility_max: Optional[int] = Query(None),
    attack_min: Optional[int] = Query(None),
    attack_max: Optional[int] = Query(None),
    init_min: Optional[int] = Query(None),
    init_max: Optional[int] = Query(None),
    is_unique: bool = Query(False),
    is_limited: bool = Query(False),
    is_not_limited: bool = Query(False),
    base_sizes: Optional[List[str]] = Query(None),
    continent: Optional[List[str]] = Query(None),
    country: Optional[List[str]] = Query(None),
    city: Optional[List[str]] = Query(None),
):
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    criteria_map = {
        "Cost": SortingCriteria.COST,
        "Games": SortingCriteria.GAMES,
        "Name": SortingCriteria.NAME,
        "Popularity": SortingCriteria.POPULARITY,
        "Win Rate": SortingCriteria.WINRATE,
        "Loadout": SortingCriteria.LOADOUT
    }
    criteria = criteria_map.get(sort_metric, SortingCriteria.POPULARITY)
    s_dir = SortDirection.DESCENDING if sort_direction == "desc" else SortDirection.ASCENDING

    filters = _build_filters(
        formats=formats, factions=factions, ships=ships, initiatives=initiatives,
        search_text=search_text, points_min=points_min, points_max=points_max,
        loadout_min=loadout_min, loadout_max=loadout_max, hull_min=hull_min,
        hull_max=hull_max, shields_min=shields_min, shields_max=shields_max,
        agility_min=agility_min, agility_max=agility_max, attack_min=attack_min,
        attack_max=attack_max, init_min=init_min, init_max=init_max,
        is_unique=is_unique, is_limited=is_limited, is_not_limited=is_not_limited,
        base_sizes=base_sizes, continent=continent, country=country, city=city
    )

    data = aggregate_card_stats(filters, criteria, s_dir, "pilots", ds_enum)
    total = len(data)
    items = data[page * size : (page + 1) * size]
    
    return PaginatedPilotsResponse(items=items, total=total, page=page, size=size)


@router.get("/upgrades", response_model=PaginatedUpgradesResponse)
def get_upgrades(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Popularity"),
    sort_direction: str = Query("desc"),
    
    formats: Optional[List[str]] = Query(None),
    factions: Optional[List[str]] = Query(None),
    upgrade_types: Optional[List[str]] = Query(None),
    search_text: str = Query(""),
    points_min: Optional[int] = Query(None),
    points_max: Optional[int] = Query(None),
    continent: Optional[List[str]] = Query(None),
    country: Optional[List[str]] = Query(None),
    city: Optional[List[str]] = Query(None),
):
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    criteria_map = {
        "Cost": SortingCriteria.COST,
        "Games": SortingCriteria.GAMES,
        "Name": SortingCriteria.NAME,
        "Popularity": SortingCriteria.POPULARITY,
        "Win Rate": SortingCriteria.WINRATE,
    }
    criteria = criteria_map.get(sort_metric, SortingCriteria.POPULARITY)
    s_dir = SortDirection.DESCENDING if sort_direction == "desc" else SortDirection.ASCENDING

    filters = _build_filters(
        formats=formats, factions=factions, upgrade_types=upgrade_types,
        search_text=search_text, points_min=points_min, points_max=points_max,
        continent=continent, country=country, city=city
    )

    data = aggregate_card_stats(filters, criteria, s_dir, "upgrades", ds_enum)
    total = len(data)
    items = data[page * size : (page + 1) * size]
    
    return PaginatedUpgradesResponse(items=items, total=total, page=page, size=size)
