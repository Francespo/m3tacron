"""Card cost/loadout fields exposed to the cards and ship-pilot endpoints.

The cards browser and the ship page must display the server-side manifest
costs, not a browser-cached copy. These tests cover the pure sorting helpers;
the SQL aggregation is exercised by the API suite when PostgreSQL is
available.
"""

from backend.analytics.core import _finalize_results
from backend.api.cards import _sort_card_stats
from backend.data_structures.sorting_order import SortingCriteria, SortDirection


def _row(xws: str, cost: int, loadout: int) -> dict:
    return {
        "xws": xws,
        "list_count": 0,
        "games_count": 0,
        "different_lists_count": 0,
        "wins": 0,
        "cost": cost,
        "loadout": loadout,
    }


def test_finalize_results_sorts_by_cost_and_loadout():
    stats = {
        "a": _row("a", 20, 10),
        "b": _row("b", 11, 20),
        "c": _row("c", 5, 0),
    }

    by_cost = _finalize_results(stats, SortingCriteria.COST, SortDirection.ASCENDING)
    assert [r["xws"] for r in by_cost] == ["c", "b", "a"]

    by_loadout = _finalize_results(stats, SortingCriteria.LOADOUT, SortDirection.DESCENDING)
    assert [r["xws"] for r in by_loadout] == ["b", "a", "c"]


def test_cards_sort_helper_uses_cost_and_loadout():
    rows = [_row("a", 20, 10), _row("b", 11, 20), _row("c", 5, 0)]

    assert [r["xws"] for r in _sort_card_stats(rows, "Cost", "asc")] == ["c", "b", "a"]
    assert [r["xws"] for r in _sort_card_stats(rows, "Loadout", "desc")] == ["b", "a", "c"]
