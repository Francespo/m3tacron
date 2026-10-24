import json
from functools import lru_cache

from fastapi import APIRouter, Query
from sqlalchemy import text
from sqlmodel import Session

from ..analytics.lists import aggregate_list_stats, fetch_list_pilots
from ..cache import get_cached_or_compute
from ..data_structures.data_source import DataSource, parse_data_source
from ..data_structures.factions import Faction
from ..database import engine
from ..utils.xwing_data.pilots import load_all_pilots
from .schemas import PaginatedListsResponse

router = APIRouter(prefix="/api/lists", tags=["Lists"])

# Pack/variant suffixes stripped by both the frontend `xwingData.getPilot()`
# and the backend `get_pilot_info()`. The point-cost filter mirrors that
# lookup so the value it filters on is exactly the value the list row shows.
_PACK_SUFFIXES = (
    "-armedanddangerous",
    "-evacuationofdqar",
    "-battleoverendor",
    "-battleofyavin",
    "-siegeofcoruscant",
    "-alphastrike",
    "-lsl",
)


def _num(v):
    try:
        return float(v)
    except Exception:
        return None

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
    pilots=None, pilot_mode: str = "any", ship_mode: str = "all",
    lists_min=None, lists_max=None, entries_min=None, entries_max=None,
    games_min=None, games_max=None, win_rate_min=None, win_rate_max=None,
) -> str:
    return (
        f"lists|{data_source}|"
        f"f={','.join(sorted(formats or []))}|"
        f"fa={','.join(sorted(factions or []))}|"
        f"s={','.join(sorted(ships or []))}|"
        f"sm={ship_mode}|"
        f"pil={','.join(sorted(pilots or []))}|pm={pilot_mode}|"
        f"p={','.join(sorted(platforms or []))}|"
        f"co={','.join(sorted(continent or []))}|"
        f"cn={','.join(sorted(country or []))}|"
        f"ci={','.join(sorted(city or []))}|"
        f"ds={date_start}|de={date_end}|"
        f"pcmin={player_count_min}|pcmax={player_count_max}|"
        f"mg={min_games}|pmin={points_min}|pmax={points_max}|"
        f"lmin={lists_min}|lmax={lists_max}|emin={entries_min}|emax={entries_max}|"
        f"gmin={games_min}|gmax={games_max}|wrmin={win_rate_min}|wrmax={win_rate_max}|"
        f"epic={epic}"
    )


def _apply_stat_ranges(rows: list[dict], filters: dict) -> list[dict]:
    """Post-aggregation filter on stat ranges (AND between different stats)."""
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
        lists_v = float(r.get("count", r.get("different_lists_count", 0)) or 0)
        entries_v = float(r.get("entries", r.get("count", 0)) or 0)
        games_v = float(r.get("games", 0) or 0)
        wr_v = float(r.get("win_rate", 0) or 0)
        if lists_min is not None and lists_v < lists_min:
            continue
        if lists_max is not None and lists_v > lists_max:
            continue
        if entries_min is not None and entries_v < entries_min:
            continue
        if entries_max is not None and entries_v > entries_max:
            continue
        if games_min is not None and games_v < games_min:
            continue
        if games_max is not None and games_v > games_max:
            continue
        if wr_min is not None and wr_v < wr_min:
            continue
        if wr_max is not None and wr_v > wr_max:
            continue
        out.append(r)
    return out


@lru_cache(maxsize=4)
def _pilot_costs_json(data_source: DataSource) -> str:
    """JSON object mapping pilot XWS -> current point cost for one source.

    Includes pack/variant-suffixed aliases (`pilot-lsl`, ...) so one JSONB
    lookup in SQL reproduces the frontend's suffix-stripping pilot lookup.
    Cached per data source: the manifest only changes on deploy.
    """
    pilots = load_all_pilots(data_source)
    costs: dict[str, int] = {}
    for xws, info in pilots.items():
        try:
            cost = int((info or {}).get("cost") or 0)
        except (TypeError, ValueError):
            cost = 0
        costs[xws] = cost
        for suffix in _PACK_SUFFIXES:
            costs.setdefault(f"{xws}{suffix}", cost)
    return json.dumps(costs)


def _fetch_current_points(signatures: list[str], data_source: DataSource) -> dict[str, int]:
    """Current point cost per list: sum of its pilots' manifest costs.

    Computed in SQL from `list_json` so the full JSON never enters Python
    (the aggregation deliberately avoids that). Mirrors `ListRowCard`'s
    `computedCurrentPoints`; a zero total means no pilot resolved and the
    caller falls back to the stored points.
    """
    sigs = [s for s in set(signatures) if s]
    if not sigs:
        return {}
    sql = text(
        """
        SELECT l.canonical_signature,
               COALESCE((
                   SELECT SUM(COALESCE(NULLIF(
                       CAST(:costs AS jsonb) ->> (COALESCE(p->>'id', p->>'name')), ''
                   )::numeric, 0))
                   FROM jsonb_array_elements(l.list_json::jsonb -> 'pilots') AS p
               ), 0)::int
        FROM list l
        WHERE l.canonical_signature = ANY(:sigs)
        """
    )
    with Session(engine) as session:
        rows = session.execute(
            sql, {"costs": _pilot_costs_json(data_source), "sigs": sigs}
        ).fetchall()
    return {sig: int(points or 0) for sig, points in rows}


def _apply_current_points_range(
    rows: list[dict],
    filters: dict,
    data_source: str,
    points_lookup=_fetch_current_points,
) -> list[dict]:
    """Inclusive min/max filter on each row's *current* point cost.

    "Current" is the value the list card displays, not the stored
    `list.points` column: for XWA that is the sum of the pilots' manifest
    costs, falling back to stored points when no pilot resolves. Legacy
    lists always display stored points, so they filter on it directly. An
    empty bound is unbounded; different bounds are ANDed. `points_lookup`
    is injectable so the logic is testable without a database.
    """
    cost_min = _num(filters.get("cost_min"))
    cost_max = _num(filters.get("cost_max"))
    if cost_min is None and cost_max is None:
        return rows

    ds = parse_data_source(data_source)
    current_points: dict[str, int] = {}
    if ds != DataSource.LEGACY:
        current_points = points_lookup([r.get("signature") or "" for r in rows], ds)

    out: list[dict] = []
    for r in rows:
        if ds == DataSource.LEGACY:
            value = _num(r.get("points")) or 0.0
        else:
            computed = current_points.get(r.get("signature") or "", 0)
            value = float(computed) if computed > 0 else (_num(r.get("points")) or 0.0)
        if cost_min is not None and value < cost_min:
            continue
        if cost_max is not None and value > cost_max:
            continue
        out.append(r)
    return out


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
    ship_mode: str = Query("all"),
    pilots: list[str] | None = Query(None),
    pilot_mode: str = Query("any"),
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
    lists_min: str | None = Query(None),
    lists_max: str | None = Query(None),
    entries_min: str | None = Query(None),
    entries_max: str | None = Query(None),
    games_min: str | None = Query(None),
    games_max: str | None = Query(None),
    win_rate_min: str | None = Query(None),
    win_rate_max: str | None = Query(None),
    cost_min: str | None = Query(None, description="Inclusive min current point cost (empty = unbounded)"),
    cost_max: str | None = Query(None, description="Inclusive max current point cost (empty = unbounded)"),
):
    # pilots + mode + stat ranges are post-aggregation but part of cache key
    # ship_mode controls whether the SQL ships filter is ANY vs ALL
    if ship_mode not in ("any", "all"):
        ship_mode = "all"
    if pilot_mode not in ("any", "all"):
        pilot_mode = "any"
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
        "ship_mode": ship_mode,
        "factions": factions,
        "pilots": pilots,
        "pilot_mode": pilot_mode,
        "epic": epic,
        "lists_min": lists_min,
        "lists_max": lists_max,
        "entries_min": entries_min,
        "entries_max": entries_max,
        "games_min": games_min,
        "games_max": games_max,
        "win_rate_min": win_rate_min,
        "win_rate_max": win_rate_max,
        "cost_min": cost_min,
        "cost_max": cost_max,
    }
    if formats:
        filters["allowed_formats"] = formats

    cache_key = _build_cache_key(
        data_source, formats, factions, ships, platforms, continent, country, city,
        date_start, date_end, player_count_min, player_count_max,
        min_games, points_min, points_max, epic=epic,
        pilots=pilots, pilot_mode=pilot_mode, ship_mode=ship_mode,
        lists_min=lists_min, lists_max=lists_max, entries_min=entries_min, entries_max=entries_max,
        games_min=games_min, games_max=games_max, win_rate_min=win_rate_min, win_rate_max=win_rate_max,
    )

    def compute():
        return _compute_lists(
            data_source=data_source,
            filters=filters,
        )

    filtered_data = get_cached_or_compute(cache_key, compute)
    filtered_data = _apply_stat_ranges(filtered_data, filters)
    # Current point cost is manifest-derived and independent of the cached
    # aggregation, so it is applied post-cache (and stays out of the cache key).
    filtered_data = _apply_current_points_range(filtered_data, filters, data_source)
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
