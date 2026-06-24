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
) -> str:
    """
    Build a WHERE-clause fragment that matches `column` (default `l.ship_list`,
    a sorted comma-joined ship string) when it contains any of the given ships.

    A ship is considered contained if it appears at the start, middle, or end
    of the comma-joined list. The generated SQL uses an OR over per-ship
    equality and three LIKE patterns, all OR'd together.

    Mutates `params` in place with the bound parameters. Returns an empty
    string if no ships are provided (caller can decide to skip the clause).
    """
    if not ships:
        return ""
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
    return "(" + " OR ".join(parts) + ")"


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
