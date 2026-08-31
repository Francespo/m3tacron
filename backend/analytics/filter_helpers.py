"""
Shared SQL filter-clause helpers used by list/squadron analytics and detail
endpoints. Centralises the ship and format filter fragments so the same
behaviour is reused across files.
"""
from typing import Iterable


def ship_list_filter_clause(
    ships: Iterable[str] | None,
    params: dict,
    param_prefix: str = "ship",
    column: str = "l.ship_list",
    mode: str = "any",
) -> str:
    """
    Build a WHERE-clause fragment that matches `column` (default `l.ship_list`,
    a sorted comma-joined ship string) against the given ships.

    A ship is considered contained if it appears at the start, middle, or end
    of the comma-joined list (4 LIKE patterns).

    `mode` controls how the per-ship containment predicates are combined:
      - "any" (default): OR'd — matches when at least one selected ship is
        present in the column. Used by the ships page (chassis catalog
        "is one of" semantics).
      - "all": AND'd — matches only when every selected ship is present.
        Used by the squadrons and lists pages, where a squadron/list may
        contain multiple chassis and the user wants the intersection.

    Mutates `params` in place with the bound parameters. Returns an empty
    string if no ships are provided (caller can decide to skip the clause).
    """
    if not ships:
        return ""
    if mode not in ("any", "all"):
        raise ValueError(f"ship_list_filter_clause: mode must be 'any' or 'all', got {mode!r}")
    parts = []
    for i, s in enumerate(ships):
        key = f"{param_prefix}_{i}"
        parts.append(
            f"({column} = :{key} "
            f"OR {column} LIKE :{key}_start "
            f"OR {column} LIKE :{key}_mid "
            f"OR {column} LIKE :{key}_end)"
        )
        params[key] = s
        params[f"{key}_start"] = f"{s},%"
        params[f"{key}_mid"] = f"%,{s},%"
        params[f"{key}_end"] = f"%,{s}"
    joiner = " AND " if mode == "all" else " OR "
    return "(" + joiner.join(parts) + ")"


def pilot_filter_clause(
    pilots: Iterable[str] | None,
    params: dict,
    mode: str = "any",
) -> str:
    """Build a WHERE fragment that matches lists containing pilot ids.

    `mode="any"` → at least one of the pilots (OR).
    `mode="all"` → every pilot must be present (AND of EXISTS).
    Uses jsonb_array_elements on l.list_json->'pilots'.
    Mutates `params`.
    """
    if not pilots:
        return ""
    if mode not in ("any", "all"):
        raise ValueError(f"pilot_filter_clause: mode must be 'any' or 'all', got {mode!r}")
    pilots = list(pilots)
    if mode == "any":
        params["pilots_any"] = pilots
        return "EXISTS (SELECT 1 FROM jsonb_array_elements(l.list_json::jsonb->'pilots') sp WHERE sp->>'id' = ANY(:pilots_any))"
    # mode == "all": one EXISTS per pilot
    parts = []
    for i, p in enumerate(pilots):
        key = f"pilot_all_{i}"
        params[key] = p
        parts.append(f"EXISTS (SELECT 1 FROM jsonb_array_elements(l.list_json::jsonb->'pilots') sp WHERE sp->>'id' = :{key})")
    return "(" + " AND ".join(parts) + ")"


def format_filter_clause(
    formats,
    params: dict,
    table_alias: str = "t",
    leading_and: bool = True,
) -> str:
    """
    Build a WHERE-clause fragment for format filtering on `table_alias.format`.

    `formats` may be a list, set, or None. Returns an empty string when no
    formats are provided. The fragment is prefixed with " AND " by default
    so it can be appended to an existing WHERE expression; pass
    `leading_and=False` to omit the leading " AND " (e.g. for use in
    `where_clauses` lists that are later joined with " AND ").

    Mutates `params` in place with the bound parameter.
    """
    if not formats:
        return ""
    if isinstance(formats, (list, set)) and formats:
        params["formats"] = list(formats)
        prefix = " AND " if leading_and else ""
        return f"{prefix}{table_alias}.format = ANY(:formats)"
    return ""


def epic_ships_exclusion_clause(
    include_epic: bool,
    source,
    params: dict,
    column: str = "l.ship_list",
) -> str:
    """
    Build a WHERE-clause fragment to exclude lists/squadrons containing Epic-only
    ships (ships that have no standard-legal pilots) when include_epic is False.
    """
    if include_epic:
        return ""

    from ..utils.xwing_data.ships import load_all_ships
    from ..utils.xwing_data.pilots import load_all_pilots
    ships = load_all_ships(source)
    pilots = load_all_pilots(source)

    epic_ships = []
    for xws in ships:
        ship_pilots = [p for p in pilots.values() if p.get("ship_xws") == xws]
        if not any(p.get("valid_in_standard") for p in ship_pilots):
            epic_ships.append(xws)

    if not epic_ships:
        return ""

    parts = []
    for i, s in enumerate(epic_ships):
        key = f"epic_ship_{i}"
        parts.append(
            f"({column} = :{key} "
            f"OR {column} LIKE :{key}_start "
            f"OR {column} LIKE :{key}_mid "
            f"OR {column} LIKE :{key}_end)"
        )
        params[key] = s
        params[f"{key}_start"] = f"{s},%"
        params[f"{key}_mid"] = f"%,{s},%"
        params[f"{key}_end"] = f"%,{s}"

    return "NOT (" + " OR ".join(parts) + ")"


huge_ships_exclusion_clause = epic_ships_exclusion_clause
