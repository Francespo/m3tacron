"""Unit tests for the Lists page current-point-cost range filter.

The filter must agree with the value the list row displays. That value is now
computed server-side by `enrich_list_data` (the same helper the list-detail
page uses) and returned as `points`, with the stored total in
`original_points`:

- XWA rows display the sum of the pilots' manifest costs, falling back to each
  pilot's stored points when the manifest has no entry.
- Legacy rows display the stored `list.points` (the card picks
  `original_points`), and the filter uses the stored total too.

`_apply_current_points_range` takes an injectable lookup so the range logic is
tested without a database or the game-data manifest. The lookup itself is
covered separately: `_pilot_costs_json` needs the manifest, and
`_fetch_current_points` needs PostgreSQL for its JSONB aggregation.
"""

import json
import os
from uuid import uuid4

import pytest

from backend.api.lists import _apply_current_points_range, _PACK_SUFFIXES


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
    """A list with no resolvable pilot is shown/filtered on its stored points."""
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


# ---------------------------------------------------------------------------
# The lookup that feeds the filter: manifest costs + the JSONB aggregation.
# ---------------------------------------------------------------------------


def _xwa_pilots_with_cost() -> list[tuple[str, int]]:
    from backend.data_structures.data_source import DataSource
    from backend.utils.xwing_data.pilots import load_all_pilots

    pilots = load_all_pilots(DataSource.XWA)
    return [
        (xws, int(info.get("cost") or 0))
        for xws, info in pilots.items()
        if (info or {}).get("cost")
    ]


def test_pilot_costs_alias_pack_suffixed_pilots():
    """The SQL lookup strips pack suffixes, so the cost map must carry aliases.

    A suffixed pilot that exists in the manifest keeps its own cost: the alias
    is a fallback for `pilot-lsl` ids, not an override.
    """
    from backend.api.lists import _pilot_costs_json
    from backend.data_structures.data_source import DataSource

    priced = _xwa_pilots_with_cost()
    if not priced:
        pytest.skip("XWA manifest is empty (external_data submodule not checked out)")

    costs = json.loads(_pilot_costs_json(DataSource.XWA))
    assert all(xws in costs for xws, _ in priced)

    base = priced[0][0]
    for suffix in _PACK_SUFFIXES:
        assert costs[base + suffix] == costs[base]

    for xws, own_cost in priced:
        suffix = next((s for s in _PACK_SUFFIXES if xws.endswith(s)), None)
        if suffix and xws[: -len(suffix)] in costs:
            assert costs[xws] == own_cost


def test_enrich_list_data_uses_manifest_costs_and_keeps_stored_total():
    """The list page's `points`/`original_points` come from this helper.

    Guards the list browser against re-deriving points from a stale
    browser-cached manifest: the server value is the one the detail page and
    the card both display.
    """
    from backend.api.formatters import enrich_list_data
    from backend.data_structures.data_source import DataSource

    priced = _xwa_pilots_with_cost()
    if len(priced) < 2:
        pytest.skip("XWA manifest is empty (external_data submodule not checked out)")
    (xws_a, cost_a), (xws_b, cost_b) = priced[:2]

    data = enrich_list_data(
        {
            "signature": "sig",
            "name": "Name",
            "faction": "rebelalliance",
            "points": 99,
            "pilots": [{"id": xws_a}, {"id": xws_b}],
            "count": 1,
            "games": 0,
            "wins": 0,
            "win_rate": 0,
        },
        source=DataSource.XWA,
    )

    assert data.points == cost_a + cost_b
    assert data.original_points == 99


def test_enrich_list_data_falls_back_to_stored_pilot_points():
    """Unresolved pilots contribute their stored points, not zero."""
    from backend.api.formatters import enrich_list_data
    from backend.data_structures.data_source import DataSource

    data = enrich_list_data(
        {
            "signature": "sig",
            "name": "Name",
            "faction": "rebelalliance",
            "points": 50,
            "pilots": [
                {"xws": "zz-not-in-manifest", "points": 7},
                {"xws": "zz-also-missing", "points": 11},
            ],
            "count": 1,
            "games": 0,
            "wins": 0,
            "win_rate": 0,
        },
        source=DataSource.XWA,
    )

    assert data.points == 18
    assert data.original_points == 50


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="requires PostgreSQL (set DATABASE_URL)",
)
def test_fetch_current_points_sums_manifest_costs():
    """The raw SQL must reproduce `enrich_list_data`'s XWA point totals.

    Covers what the injected-lookup tests cannot: the JSONB sum itself, the
    `id`/`name` pilot keys, the per-pilot stored-points fallback, and the zero
    total that triggers the stored-points fallback. Expected costs come from
    the manifest, so data syncs don't break this test.
    """
    from sqlmodel import Session, SQLModel

    from backend.api.lists import _fetch_current_points
    from backend.data_structures.data_source import DataSource
    from backend.database import engine
    from backend.models import List

    priced = _xwa_pilots_with_cost()
    if len(priced) < 2:
        pytest.skip("XWA manifest is empty (external_data submodule not checked out)")
    (xws_a, cost_a), (xws_b, cost_b) = priced[:2]

    # Create the schema if the suite's database is still empty, so the test does
    # not depend on another test (or an app startup) having run first.
    SQLModel.metadata.create_all(engine)

    marker = f"zz-cost-{uuid4().hex[:8]}"
    cases = [
        # signature, stored points, pilots as stored in list_json, expected
        (f"{marker}-sum", 999, [{"id": xws_a}, {"id": xws_b}], cost_a + cost_b),
        (f"{marker}-unknown", 55, [{"id": f"{marker}-nope"}], 0),
        (f"{marker}-named", 77, [{"name": xws_a}], cost_a),
        (f"{marker}-empty", 42, [], 0),
        # Unresolved pilot falls back to its stored points, like the detail page.
        (
            f"{marker}-pilot-fallback",
            88,
            [{"id": f"{marker}-nope", "points": 7}, {"id": xws_a}],
            7 + cost_a,
        ),
    ]

    created: list[int] = []
    with Session(engine) as session:
        for signature, points, pilots_json, _ in cases:
            row = List(
                canonical_signature=signature,
                faction="rebelalliance",
                faction_xws_normalized="rebelalliance",
                name=marker,
                points=points,
                pilot_count=len(pilots_json),
                ship_list="x",
                list_json={"faction": "rebelalliance", "pilots": pilots_json},
            )
            session.add(row)
            session.flush()
            created.append(row.id)
        session.commit()

    try:
        found = _fetch_current_points(
            [c[0] for c in cases] + [f"{marker}-missing"], DataSource.XWA
        )
    finally:
        with Session(engine) as session:
            for list_id in created:
                row = session.get(List, list_id)
                if row:
                    session.delete(row)
            session.commit()

    for signature, _, _, expected in cases:
        assert found[signature] == expected
    assert f"{marker}-missing" not in found
