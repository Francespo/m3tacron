from fastapi import APIRouter, Query
from ..analytics.squadrons import aggregate_squadron_stats
from ..data_structures.data_source import DataSource
from ..data_structures.sorting_order import SortingCriteria, SortDirection
from ..cache import get_cached_or_compute
from ..utils.xwing_data.ships import load_all_ships

router = APIRouter(prefix="/api/squadrons", tags=["Squadrons"])


def _apply_stat_ranges(rows: list[dict], filters: dict) -> list[dict]:
    def _num(v):
        try:
            return float(v)
        except Exception:
            return None
    lists_min = _num(filters.get("lists_min"))
    lists_max = _num(filters.get("lists_max"))
    entries_min = _num(filters.get("entries_min"))
    entries_max = _num(filters.get("entries_max"))
    games_min = _num(filters.get("games_min"))
    games_max = _num(filters.get("games_max"))
    wr_min = _num(filters.get("win_rate_min"))
    wr_max = _num(filters.get("win_rate_max"))
    if all(x is None for x in [lists_min, lists_max, entries_min, entries_max, games_min, games_max, wr_min, wr_max]):
        return rows
    out = []
    for r in rows:
        lists_v = float(r.get("different_lists_count", r.get("count", 0)) or 0)
        entries_v = float(r.get("count", r.get("popularity", 0)) or 0)
        games_v = float(r.get("games", 0) or 0)
        wr_v = float(r.get("win_rate", 0) or 0)
        if lists_min is not None and lists_v < lists_min: continue
        if lists_max is not None and lists_v > lists_max: continue
        if entries_min is not None and entries_v < entries_min: continue
        if entries_max is not None and entries_v > entries_max: continue
        if games_min is not None and games_v < games_min: continue
        if games_max is not None and games_v > games_max: continue
        if wr_min is not None and wr_v < wr_min: continue
        if wr_max is not None and wr_v > wr_max: continue
        out.append(r)
    return out


def _compute_squadrons(
    data_source: str,
    filters: dict,
) -> dict:
    try:
        ds_enum = DataSource(data_source)
    except ValueError:
        ds_enum = DataSource.XWA
    factions = filters.get("factions")
    min_games = filters.get("min_games", 0)
    raw_data = aggregate_squadron_stats(
        filters,
        sort_metric=SortingCriteria.GAMES,
        sort_direction=SortDirection.DESCENDING,
        data_source=ds_enum,
    )
    filtered_data = []
    for row in raw_data:
        if factions and row["faction"] not in factions:
            continue
        if row["games"] < min_games:
            continue
        filtered_data.append(row)
    filtered_data = _apply_stat_ranges(filtered_data, filters)
    return {"filtered": filtered_data, "total": len(filtered_data)}


def _sort_squadron_stats(data: list[dict], sort_metric: str, sort_direction: str) -> list[dict]:
    reverse = sort_direction == "desc"
    if sort_metric == "Win Rate":
        return sorted(data, key=lambda x: x["win_rate"], reverse=reverse)
    elif sort_metric == "Lists":
        return sorted(data, key=lambda x: x.get("different_lists_count", 0), reverse=reverse)
    elif sort_metric == "Entries":
        return sorted(data, key=lambda x: x.get("popularity", x.get("count", 0)), reverse=reverse)
    return sorted(data, key=lambda x: x["games"], reverse=reverse)


@router.get("")
def get_squadrons(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    data_source: str = Query("xwa"),
    sort_metric: str = Query("Games"),
    sort_direction: str = Query("desc"),
    epic: bool = Query(False),
    formats: list[str] | None = Query(None),
    factions: list[str] | None = Query(None),
    ships: list[str] | None = Query(None),
    ship_mode: str = Query("all"),
    platforms: list[str] | None = Query(None),
    continent: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: list[str] | None = Query(None),
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    player_count_min: int | None = Query(None),
    player_count_max: int | None = Query(None),
    min_games: int = Query(0, ge=0),
    lists_min: str | None = Query(None),
    lists_max: str | None = Query(None),
    entries_min: str | None = Query(None),
    entries_max: str | None = Query(None),
    games_min: str | None = Query(None),
    games_max: str | None = Query(None),
    win_rate_min: str | None = Query(None),
    win_rate_max: str | None = Query(None),
):
    if ship_mode not in ("any", "all"): ship_mode = "all"
    filters: dict = {}
    if formats: filters["allowed_formats"] = formats
    if factions: filters["factions"] = factions
    if ships: filters["ships"] = ships
    filters["ship_mode"] = ship_mode
    filters["platforms"] = platforms
    filters["continent"] = continent
    filters["country"] = country
    filters["city"] = city
    filters["date_start"] = date_start
    filters["date_end"] = date_end
    filters["player_count_min"] = player_count_min
    filters["player_count_max"] = player_count_max
    filters["min_games"] = min_games
    filters["epic"] = epic
    filters["lists_min"] = lists_min
    filters["lists_max"] = lists_max
    filters["entries_min"] = entries_min
    filters["entries_max"] = entries_max
    filters["games_min"] = games_min
    filters["games_max"] = games_max
    filters["win_rate_min"] = win_rate_min
    filters["win_rate_max"] = win_rate_max

    # Build a stable cache key from all inputs that affect the response.
    # page/size excluded — pagination is done AFTER caching.
    # sort_metric/sort_direction excluded — sorting is done AFTER caching.
    cache_key = (
        f"squadrons|{data_source}|"
        f"{','.join(sorted(formats or []))}|"
        f"{','.join(sorted(factions or []))}|"
        f"{','.join(sorted(ships or []))}|sm={ship_mode}|"
        f"{','.join(sorted(platforms or []))}|"
        f"{','.join(sorted(continent or []))}|"
        f"{','.join(sorted(country or []))}|"
        f"{','.join(sorted(city or []))}|"
        f"{date_start or ''}|{date_end or ''}|"
        f"{player_count_min}|{player_count_max}|"
        f"{min_games}|lmin={lists_min}|lmax={lists_max}|emin={entries_min}|emax={entries_max}|"
        f"gmin={games_min}|gmax={games_max}|wrmin={win_rate_min}|wrmax={win_rate_max}|{epic}"
    )

    def compute():
        return _compute_squadrons(
            data_source=data_source,
            filters=filters,
        )

    cached = get_cached_or_compute(cache_key, compute)

    # Sort AFTER the cache lookup — the heavy aggregation is sort-independent.
    filtered = _sort_squadron_stats(cached["filtered"], sort_metric, sort_direction)

    # Paginate + enrich AFTER cache (only enriches the current page slice)
    total = cached["total"]
    items_raw = filtered[page * size : (page + 1) * size]

    all_ships = load_all_ships(DataSource(data_source) if data_source in ("xwa", "legacy") else DataSource.XWA)
    items = []
    for s in items_raw:
        pilots = []
        for ship_xws in s["ships"]:
            s_info = all_ships.get(ship_xws, {})
            pilots.append({
                "ship_name": s_info.get("name", ship_xws),
                "ship_icon": ship_xws,
            })
        items.append({
            "signature": s["signature"],
            "faction": s["faction"],
            "faction_key": s["faction"],
            "games": s["games"],
            "win_rate": s["win_rate"],
            "count": s["popularity"],
            "different_lists_count": s.get("different_lists_count", s["popularity"]),
            "pilots": pilots,
        })

    return {"items": items, "total": total, "page": page, "size": size}
