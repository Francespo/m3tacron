from collections import OrderedDict
from typing import Any, Iterable


def normalize_stat_count(value) -> int:
    try:
        count = int(value)
    except Exception:
        return 0

    return count if count > 0 else 0


def merge_ship_faction_rows(rows: Iterable[dict]) -> list[dict]:
    """
    Merge per-(ship, faction) aggregated rows into per-ship stats.

    ``rows`` come from the ships aggregation SQL, which groups by
    (ship_xws, faction) and returns one row per (ship, faction) with:

        ship_xws, faction, list_count, different_lists_count, wins, games

    The SQL guarantees the counting rules before this merge runs:

      1. A ship appearing multiple times in the SAME list counts as ONE
         list (the query de-duplicates by (playerstanding, ship)).
      2. Games/wins are counted once per list-side (each playerstanding's
         record is summed exactly once, i.e. one count per (match, list)
         pair). A list containing N copies of a ship that played M matches
         contributes exactly M games.
      3. If both opposing lists in a match contain the same ship, the
         match counts twice — once per side — because each side is its
         own playerstanding row.

    A playerstanding belongs to exactly one list with exactly one faction,
    so the per-faction rows for a given ship are disjoint: ship-level
    totals are exact sums of the per-faction values, and per-faction
    breakdowns are preserved for the ships-page faction toggle.

    Returns a list of dicts matching the ShipStats schema (plus the
    ``faction_stats`` per-faction breakdown).
    """
    ships: "OrderedDict[str, dict]" = OrderedDict()

    for row in rows:
        ship_xws = row["ship_xws"]
        faction = row.get("faction") or "unknown"

        ship = ships.setdefault(ship_xws, {
            "xws": ship_xws,
            "factions": [],
            "games_count": 0,
            "list_count": 0,
            "different_lists_count": 0,
            "entries_count": 0,
            "squadron_count": 0,
            "wins": 0,
            "faction_stats": {},
        })

        if faction not in ship["factions"]:
            ship["factions"].append(faction)

        faction_stats = ship["faction_stats"].setdefault(faction, {
            "games_count": 0,
            "list_count": 0,
            "wins": 0,
            "entries_count": 0,
            "squadron_count": 0,
        })

        games = row.get("games") or 0
        wins = row.get("wins") or 0
        list_count = row.get("list_count") or 0
        different_lists = row.get("different_lists_count") or 0
        entries = row.get("entries_count") or 0
        squadrons = row.get("squadron_count") or 0

        faction_stats["games_count"] += games
        faction_stats["list_count"] += list_count
        faction_stats["entries_count"] += entries
        faction_stats["squadron_count"] += squadrons
        faction_stats["wins"] += wins

        ship["games_count"] += games
        ship["list_count"] += list_count
        ship["different_lists_count"] += different_lists
        ship["entries_count"] += entries
        ship["squadron_count"] += squadrons
        ship["wins"] += wins

    return list(ships.values())
