"""Unit tests for the Lists page current-point-cost range filter.

The filter must agree with the value the list row displays:
- XWA rows display the sum of the pilots' manifest costs, falling back to the
  stored `list.points` when no pilot resolves.
- Legacy rows always display the stored `list.points`.

`_apply_current_points_range` takes an injectable lookup so these tests do not
need a database or the game-data manifest.
"""

from backend.api.lists import _apply_current_points_range


def _row(signature: str, points: int) -> dict:
    return {"signature": signature, "points": points}


def test_no_bounds_is_a_noop_and_skips_lookup():
    rows = [_row("a", 50), _row("b", 20)]

    def lookup(signatures, data_source):  # pragma: no cover - must not run
        raise AssertionError("lookup must not be called without bounds")

    out = _apply_current_points_range(rows, {}, "xwa", points_lookup=lookup)
    assert out is rows


def test_empty_string_bounds_are_unbounded():
    rows = [_row("a", 50)]
    filters = {"cost_min": "", "cost_max": ""}
    out = _apply_current_points_range(rows, filters, "xwa", points_lookup=lambda s, d: {})
    assert out == rows


def test_xwa_inclusive_bounds_use_computed_points():
    rows = [_row("low", 20), _row("mid", 20), _row("high", 20)]
    computed = {"low": 48, "mid": 50, "high": 52}

    out = _apply_current_points_range(
        rows,
        {"cost_min": "50", "cost_max": "50"},
        "xwa",
        points_lookup=lambda signatures, ds: computed,
    )
    assert [r["signature"] for r in out] == ["mid"]


def test_xwa_min_only_and_max_only():
    rows = [_row("a", 20), _row("b", 20), _row("c", 20)]
    computed = {"a": 48, "b": 50, "c": 52}

    only_min = _apply_current_points_range(
        rows, {"cost_min": "50"}, "xwa", points_lookup=lambda s, d: computed
    )
    assert [r["signature"] for r in only_min] == ["b", "c"]

    only_max = _apply_current_points_range(
        rows, {"cost_max": "50"}, "xwa", points_lookup=lambda s, d: computed
    )
    assert [r["signature"] for r in only_max] == ["a", "b"]


def test_xwa_zero_computed_falls_back_to_stored_points():
    """Mirrors ListRowCard: computed > 0 wins, otherwise list.points is shown."""
    rows = [_row("resolved", 10), _row("unresolved", 55)]
    computed = {"resolved": 50, "unresolved": 0}

    out = _apply_current_points_range(
        rows,
        {"cost_min": "50", "cost_max": "50"},
        "xwa",
        points_lookup=lambda s, d: computed,
    )
    assert [r["signature"] for r in out] == ["resolved"]

    out = _apply_current_points_range(
        rows,
        {"cost_min": "55", "cost_max": "55"},
        "xwa",
        points_lookup=lambda s, d: computed,
    )
    assert [r["signature"] for r in out] == ["unresolved"]


def test_legacy_filters_on_stored_points_without_lookup():
    rows = [_row("a", 20), _row("b", 50), _row("c", 80)]

    def lookup(signatures, data_source):  # pragma: no cover - must not run
        raise AssertionError("legacy rows must not consult the manifest")

    out = _apply_current_points_range(
        rows, {"cost_min": "25", "cost_max": "60"}, "legacy", points_lookup=lookup
    )
    assert [r["signature"] for r in out] == ["b"]
