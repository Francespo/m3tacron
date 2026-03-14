from fastapi import APIRouter, Query, Depends
from ..analytics.core import aggregate_card_stats
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..data_structures.data_source import DataSource
from .schemas import PaginatedPilotsResponse, PaginatedUpgradesResponse

router = APIRouter(prefix="/api/cards", tags=["Cards"])

def _build_filters(
    formats: list[str] | None = None,
    factions: list[str] | None = None,
    ships: list[str] | None = None,
    initiatives: list[int] | None = None,
    upgrade_types: list[str] | None = None,
    search_text: str = "",
    points_min: int | None = None,
    points_max: int | None = None,
    loadout_min: int | None = None,
    loadout_max: int | None = None,
    hull_min: int | None = None,
    hull_max: int | None = None,
    shields_min: int | None = None,
    shields_max: int | None = None,
    agility_min: int | None = None,
    agility_max: int | None = None,
    attack_min: int | None = None,
    attack_max: int | None = None,
    init_min: int | None = None,
    init_max: int | None = None,
    is_unique: bool = False,
    is_limited: bool = False,
    is_not_limited: bool = False,
    base_sizes: list[str] | None = None,
    platforms: list[str] | None = None,
    continent: list[str] | None = None,
    country: list[str] | None = None,
    city: list[str] | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    player_count_min: int | None = None,
    player_count_max: int | None = None,
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
        "platforms": platforms,
        "continent": continent,
        "country": country,
        "city": city,
        "date_start": date_start,
        "date_end": date_end,
        "player_count_min": player_count_min,
        "player_count_max": player_count_max,
        "include_epic": False
    }


@router.get("/pilots", response_model=PaginatedPilotsResponse)
def get_pilots(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Popularity"),
    sort_direction: str = Query("desc"),
    
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    initiatives: list[int] | None = Query(None),
    search_text: str = Query(""),
    points_min: int | None = Query(None),
    points_max: int | None = Query(None),
    loadout_min: int | None = Query(None),
    loadout_max: int | None = Query(None),
    hull_min: int | None = Query(None),
    hull_max: int | None = Query(None),
    shields_min: int | None = Query(None),
    shields_max: int | None = Query(None),
    agility_min: int | None = Query(None),
    agility_max: int | None = Query(None),
    attack_min: int | None = Query(None),
    attack_max: int | None = Query(None),
    init_min: int | None = Query(None),
    init_max: int | None = Query(None),
    is_unique: bool = Query(False),
    is_limited: bool = Query(False),
    is_not_limited: bool = Query(False),
    base_sizes: list[str] | None = Query(None),
    platforms: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
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
        base_sizes=base_sizes, platforms=platforms, continent=continent, country=country, city=city,
        date_start=date_start, date_end=date_end,
        player_count_min=player_count_min, player_count_max=player_count_max
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
    
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    upgrade_types: list[str] | None = Query(None),
    search_text: str = Query(""),
    points_min: int | None = Query(None),
    points_max: int | None = Query(None),
    platforms: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
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
        platforms=platforms, continent=continent, country=country, city=city,
        date_start=date_start, date_end=date_end,
        player_count_min=player_count_min, player_count_max=player_count_max
    )

    data = aggregate_card_stats(filters, criteria, s_dir, "upgrades", ds_enum)
    total = len(data)
    items = data[page * size : (page + 1) * size]
    
    return PaginatedUpgradesResponse(items=items, total=total, page=page, size=size)
