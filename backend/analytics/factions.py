"""
Faction Analytics - Aggregation Logic for Factions.
"""
from sqlalchemy import text
from sqlmodel import Session

from ..database import engine
from ..data_structures.factions import Faction
from ..data_structures.data_source import DataSource
from .filter_helpers import format_filter_clause, huge_ships_exclusion_clause
from .filters import get_active_formats


def aggregate_faction_stats(
    filters: dict,
    data_source: DataSource = DataSource.XWA
) -> list[dict]:
    """
    Aggregate statistics per faction using a single SQL GROUP BY.

    Mirrors the pattern used by ships/lists/squadrons: build WHERE clauses
    in Python, then run one GROUP BY query joining playerstanding -> tournament
    -> list. No Python row iteration, no get_list_key hashing.
    """
    where_clauses: list[str] = []
    params: dict = {}

    if filters.get("date_start"):
        where_clauses.append("t.date >= :date_start")
        params["date_start"] = filters["date_start"]
    if filters.get("date_end"):
        where_clauses.append("t.date <= :date_end")
        params["date_end"] = filters["date_end"]

    sources = filters.get("sources") or filters.get("platforms") or []
    if sources:
        where_clauses.append("t.source = ANY(:sources)")
        params["sources"] = list(sources)

    if filters.get("player_count_min") is not None:
        where_clauses.append("t.player_count >= :pc_min")
        params["pc_min"] = int(filters["player_count_min"])
    if filters.get("player_count_max") is not None:
        where_clauses.append("t.player_count <= :pc_max")
        params["pc_max"] = int(filters["player_count_max"])

    # Location filters (tournament.location JSON)
    if filters.get("continent"):
        where_clauses.append("t.location->>'continent' = ANY(:continents)")
        params["continents"] = list(filters["continent"])
    if filters.get("country"):
        where_clauses.append("t.location->>'country' = ANY(:countries)")
        params["countries"] = list(filters["country"])
    if filters.get("city"):
        where_clauses.append("t.location->>'city' = ANY(:cities)")
        params["cities"] = list(filters["city"])

    fmt_clause = format_filter_clause(filters.get("allowed_formats"), params, leading_and=False)
    if fmt_clause:
        where_clauses.append(fmt_clause)

    # Faction filter (if dashboard ever filters by faction)
    if filters.get("factions"):
        facs = filters["factions"]
        if isinstance(facs, (list, set)) and facs:
            normalized = [f.lower().replace(" ", "").replace("-", "") for f in facs]
            where_clauses.append("l.faction_xws_normalized = ANY(:factions)")
            params["factions"] = normalized

    # Team events: exclude placeholder rows
    where_clauses.append("(NOT t.is_team_event OR ps.is_team_member)")

    # Epic / huge-ship filter
    if not filters.get("epic", False) and not filters.get("include_epic", False):
        huge_clause = huge_ships_exclusion_clause(False, data_source, params)
        if huge_clause:
            where_clauses.append(huge_clause)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = text(f"""
        SELECT
            l.faction_xws_normalized as faction_norm,
            l.faction as faction_raw,
            COUNT(*) as list_count,
            SUM(GREATEST(0, COALESCE(ps.swiss_wins,0)) + GREATEST(0, COALESCE(ps.cut_wins,0))) as wins,
            SUM(
                GREATEST(0, COALESCE(ps.swiss_wins,0)) + GREATEST(0, COALESCE(ps.swiss_losses,0)) + GREATEST(0, COALESCE(ps.swiss_draws,0))
                + GREATEST(0, COALESCE(ps.cut_wins,0)) + GREATEST(0, COALESCE(ps.cut_losses,0)) + GREATEST(0, COALESCE(ps.cut_draws,0))
            ) as games,
            COUNT(DISTINCT l.id) as different_lists
        FROM playerstanding ps
        JOIN tournament t ON t.id = ps.tournament_id
        JOIN list l ON l.id = ps.list_id
        WHERE {where_sql}
        GROUP BY l.faction_xws_normalized, l.faction
    """)

    with Session(engine) as session:
        rows = session.execute(sql, params).fetchall()

    # Map normalized faction -> aggregated row. Multiple raw factions can map to same normalized.
    agg_by_norm: dict[str, dict] = {}
    for faction_norm, faction_raw, list_count, wins, games, different_lists in rows:
        norm = (faction_norm or "").lower().replace(" ", "").replace("-", "")
        if not norm:
            # Fallback: normalize raw
            norm = (faction_raw or "unknown").lower().replace(" ", "").replace("-", "")
        if norm not in agg_by_norm:
            agg_by_norm[norm] = {
                "faction_norm": norm,
                "faction_raw": faction_raw,
                "list_count": 0,
                "wins": 0,
                "games": 0,
                "different_lists": 0,
            }
        agg_by_norm[norm]["list_count"] += int(list_count or 0)
        agg_by_norm[norm]["wins"] += int(wins or 0)
        agg_by_norm[norm]["games"] += int(games or 0)
        # different_lists per normalized group should be distinct list ids; summing groups is approx.
        # For factions, raw factions within same normalized are same faction, so distinct count can be summed.
        # If raw grouping split a faction, we sum (slight overcount if same list id appears with different raw case,
        # which shouldn't happen because list.faction is canonical).
        agg_by_norm[norm]["different_lists"] += int(different_lists or 0)

    # Build results with zero-fill for factions with no data, matching previous Python init.
    results: list[dict] = []
    for f in Faction:
        if f == Faction.UNKNOWN:
            continue
        norm = f.value.lower().replace(" ", "").replace("-", "")
        agg = agg_by_norm.get(norm)
        if agg:
            results.append({
                "xws": f,
                "games_count": agg["games"],
                "list_count": agg["list_count"],
                "wins": agg["wins"],
                "different_lists_count": agg["different_lists"],
            })
        else:
            results.append({
                "xws": f,
                "games_count": 0,
                "list_count": 0,
                "wins": 0,
                "different_lists_count": 0,
            })

    # Unknown bucket: include only if there are rows that didn't map to a known faction
    known_norms = {f.value.lower().replace(" ", "").replace("-", "") for f in Faction if f != Faction.UNKNOWN}
    unknown_list = unknown_wins = unknown_games = unknown_diff = 0
    unknown_found = False
    for norm, agg in agg_by_norm.items():
        if norm not in known_norms:
            unknown_found = True
            unknown_list += agg["list_count"]
            unknown_wins += agg["wins"]
            unknown_games += agg["games"]
            unknown_diff += agg["different_lists"]
    if unknown_found:
        results.append({
            "xws": Faction.UNKNOWN,
            "games_count": unknown_games,
            "list_count": unknown_list,
            "wins": unknown_wins,
            "different_lists_count": unknown_diff,
        })

    results.sort(key=lambda x: x["games_count"], reverse=True)
    return results


def _read_last_scrape_at() -> str | None:
    """Read last scrape timestamp from scrape_meta, if present.

    The scraper writes an ISO-8601 UTC timestamp (e.g. ``2026-08-23T08:00:12+00:00``).
    The dashboard's Last Sync card and period banner expect ``YYYY-MM-DD``,
    so we normalize to the date part for backward compatibility.
    """
    try:
        from sqlalchemy import text as _text
        with engine.connect() as conn:
            row = conn.execute(_text("SELECT value FROM scrape_meta WHERE key = 'last_scrape_at'")).fetchone()
            raw = str(row[0]) if row and row[0] else None
            if not raw:
                row = conn.execute(_text("SELECT value FROM scrape_meta WHERE key = 'last_sync'")).fetchone()
                raw = str(row[0]) if row and row[0] else None
            if raw:
                # Normalize ``2026-08-23T...`` -> ``2026-08-23``. If already YYYY-MM-DD, stays as is.
                raw = raw.strip()
                if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
                    return raw[:10]
                return raw
    except Exception:
        pass
    return None


def get_meta_snapshot(
    data_source: DataSource = DataSource.XWA,
    allowed_formats: list[str] | None = None,
    include_epic: bool = False,
    days_back: int | None = 90,
    date_start: str | None = None,
    date_end: str | None = None,
) -> dict:
    """
    Get meta snapshot data for home page.
    Combines aggregated statistics from factions, ships, lists, pilots, and upgrades.
    """
    from datetime import datetime, timedelta

    filters = {
        "include_epic": include_epic,
        "epic": include_epic,
    }

    resolved_date_start = date_start
    resolved_date_end = date_end
    date_range_label = "All Time"

    if resolved_date_start:
        filters["date_start"] = resolved_date_start
        if resolved_date_end:
            filters["date_end"] = resolved_date_end
            date_range_label = f"{resolved_date_start} → {resolved_date_end}"
        else:
            date_range_label = f"From {resolved_date_start}"
    elif days_back is not None and days_back > 0:
        resolved_date_start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        filters["date_start"] = resolved_date_start
        if days_back == 7:
            date_range_label = "Last 7 Days"
        elif days_back == 30:
            date_range_label = "Last 30 Days"
        elif days_back == 90:
            date_range_label = "Last 90 Days"
        elif days_back == 180:
            date_range_label = "Last 6 Months"
        elif days_back == 365:
            date_range_label = "Last Year"
        else:
            date_range_label = f"Last {days_back} Days"
    else:
        date_range_label = "All Time"

    if allowed_formats:
        filters["allowed_formats"] = get_active_formats(allowed_formats)
    else:
        filters["allowed_formats"] = ["xwa"] if data_source == DataSource.XWA else ["legacy_x2po"]

    # Run heavy aggregations. Sequential for now (could parallelize with ThreadPoolExecutor).
    faction_stats = aggregate_faction_stats(filters, data_source)

    from .ships import aggregate_ship_stats
    ship_stats = aggregate_ship_stats(filters, data_source=data_source)

    from .lists import aggregate_list_stats, fetch_list_pilots
    list_stats = aggregate_list_stats(filters, data_source=data_source)

    # Attach pilots lazily — aggregation returns empty pilots to avoid
    # pulling list_json for every row; the snapshot only ships a handful
    # of lists, so fetch pilots just for those.
    list_signatures: list[str] = [l["signature"] for l in list_stats if l.get("signature")]
    list_pilots = fetch_list_pilots(list_signatures) if list_signatures else {}
    list_stats = [
        {**l, "pilots": list_pilots.get(l["signature"], [])}
        for l in list_stats
        if l.get("signature")
    ]

    from .core import aggregate_card_stats
    pilot_stats = aggregate_card_stats(filters, mode="pilots", data_source=data_source)
    upgrade_stats = aggregate_card_stats(filters, mode="upgrades", data_source=data_source)

    # Last sync is the last scraper run timestamp, not request time.
    last_sync_val = _read_last_scrape_at()
    if not last_sync_val:
        # Fallback to now for fresh DBs that haven't been scraped yet
        last_sync_val = datetime.now().strftime("%Y-%m-%d")

    return {
        "factions": faction_stats,
        "ships": ship_stats,
        "lists": list_stats,
        "pilots": pilot_stats,
        "upgrades": upgrade_stats,
        "last_sync": last_sync_val,
        "date_range": date_range_label,
        "date_start": resolved_date_start,
        "date_end": resolved_date_end,
        "total_tournaments": 0,
        "total_players": 0,
    }
