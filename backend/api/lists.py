from fastapi import APIRouter, Query
from ..analytics.lists import aggregate_list_stats, fetch_list_pilots
from ..cache import get_cached_or_compute
from ..data_structures.data_source import DataSource
from ..data_structures.factions import Faction
from .schemas import PaginatedListsResponse

router = APIRouter(prefix="/api/lists", tags=["Lists"])

# Helper to match faction filter
def _match_faction(f_enum: Faction, allowed_list: list[str]) -> bool:
    if not allowed_list: return True
    # allowed_list has strings like "rebelalliance", "rebel", etc.
    # f_enum is normalized.
    # Normalize allowed list
    norm_allowed = {f.lower().replace(" ", "").replace("-", "") for f in allowed_list}
    return f_enum.value.replace("-", "") in norm_allowed


def _build_cache_key(
    data_source: str,
    formats, factions, ships, platforms, continent, country, city,
    date_start, date_end, player_count_min, player_count_max,
    min_games, points_min, points_max, epic: bool = False,
) -> str:
    return (
        f"lists|{data_source}|"
        f"f={','.join(sorted(formats or []))}|"
        f"fa={','.join(sorted(factions or []))}|"
        f"s={','.join(sorted(ships or []))}|"
        f"p={','.join(sorted(platforms or []))}|"
        f"co={','.join(sorted(continent or []))}|"
        f"cn={','.join(sorted(country or []))}|"
        f"ci={','.join(sorted(city or []))}|"
        f"ds={date_start}|de={date_end}|"
        f"pcmin={player_count_min}|pcmax={player_count_max}|"
        f"mg={min_games}|pmin={points_min}|pmax={points_max}|"
        f"epic={epic}"
    )


def _compute_lists(
    data_source: str,
    filters: dict,
) -> list[dict]:
    """Run the expensive aggregation + post-filter.

    Returns a list of rows in neutral games-desc order. The requested sort is
    applied AFTER the cache lookup — see _sort_list_stats.
    """
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA

    formats = filters.get("allowed_formats")
    factions = filters.get("factions")
    ships = filters.get("ships")
    platforms = filters.get("platforms")
    continent = filters.get("continent")
    country = filters.get("country")
    city = filters.get("city")
    date_start = filters.get("date_start")
    date_end = filters.get("date_end")
    player_count_min = filters.get("player_count_min")
    player_count_max = filters.get("player_count_max")
    min_games = filters.get("min_games", 0)
    points_min = filters.get("points_min", 0)
    points_max = filters.get("points_max", 200)

    # Get raw aggregated data (SQL GROUP BY -> ~2K rows max).
    raw_data = aggregate_list_stats(filters, data_source=ds_enum)

    filtered_data: list[dict] = []
    for row in raw_data:
        points = row.get("points") or 0

        # Faction check
        if factions and not _match_faction(row["faction_xws"], factions):
            continue

        if row["games"] < min_games:
            continue
        if points < points_min or points > points_max:
            continue

        row["points"] = points
        filtered_data.append(row)

    # Neutral deterministic order (games desc). The requested sort is applied
    # after the cache lookup so the heavy aggregation is shared across sorts.
    filtered_data.sort(key=lambda x: x["games"], reverse=True)

    return filtered_data


def _sort_list_stats(data: list[dict], sort_metric: str, sort_direction: str) -> list[dict]:
    reverse = sort_direction == "desc"

    def get_win_rate(r):
        return r["wins"] / r["games"] if r["games"] > 0 else 0.0

    if sort_metric == "Win Rate":
        return sorted(data, key=get_win_rate, reverse=reverse)
    elif sort_metric == "Points Cost":
        return sorted(data, key=lambda x: x["points"], reverse=reverse)
    elif sort_metric in ("Entries", "Lists", "Popularity"):
        return sorted(data, key=lambda x: x.get("count", 0), reverse=reverse)
    return sorted(data, key=lambda x: x["games"], reverse=reverse)


@router.get("", response_model=PaginatedListsResponse)
def get_lists(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Games"),
    sort_direction: str = Query("desc"),
    epic: bool = Query(False),

    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    min_games: int = Query(0, ge=0),
    points_min: int = Query(0, ge=0),
    points_max: int = Query(200, ge=0),
    platforms: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
):
    filters = {
        "platforms": platforms,
        "continent": continent,
        "country": country,
        "city": city,
        "date_start": date_start,
        "date_end": date_end,
        "player_count_min": player_count_min,
        "player_count_max": player_count_max,
        "ships": ships,
        "factions": factions,
        "epic": epic,
    }
    if formats:
        filters["allowed_formats"] = formats

    cache_key = _build_cache_key(
        data_source, formats, factions, ships, platforms, continent, country, city,
        date_start, date_end, player_count_min, player_count_max,
        min_games, points_min, points_max, epic=epic,
    )

    def compute():
        return _compute_lists(
            data_source=data_source,
            filters=filters,
        )

    filtered_data = get_cached_or_compute(cache_key, compute)
    # Sort AFTER the cache lookup — the heavy aggregation is sort-independent.
    filtered_data = _sort_list_stats(filtered_data, sort_metric, sort_direction)
    total = len(filtered_data)
    page_items = filtered_data[page * size : (page + 1) * size]

    # Pilots are aggregated lazily (see analytics/lists.py): the stats rows
    # carry empty pilots, so attach them only for the page being returned.
    # Copy each row first — the cached list is shared across requests and
    # must never be mutated.
    signatures: list[str] = [row["signature"] for row in page_items if row.get("signature")]
    pilots_map = fetch_list_pilots(signatures) if signatures else {}
    items = [
        {**row, "pilots": pilots_map.get(row["signature"], [])}
        for row in page_items
        if row.get("signature")
    ]

    return PaginatedListsResponse(items=items, total=total, page=page, size=size)
