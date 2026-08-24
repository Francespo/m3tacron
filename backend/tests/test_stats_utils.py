"""
Unit + integration tests for ship stats counting.

Counting rules under test (the /ships page stats contract):

1. A ship appearing multiple times in the SAME list counts the list ONCE
   (distinct lists per ship).
2. A ship appearing multiple times in the SAME match counts the match once
   per list-side — distinct (match, list) pairs per ship. A list with N
   copies of a ship that played M matches contributes exactly M games.
3. If two opposing lists in one match both contain the same ship, that
   match counts twice for that ship (once per side).
"""
import os
from collections import defaultdict
from datetime import date
from uuid import uuid4

import pytest
from sqlmodel import Session

from backend.utils.stats import normalize_stat_count, merge_ship_faction_rows
from backend.analytics.ships import aggregate_ship_stats
from backend.data_structures.data_source import DataSource
from backend.data_structures.formats import Format
from backend.data_structures.source import Source


# ---------------------------------------------------------------------------
# normalize_stat_count (existing behaviour — keep green)
# ---------------------------------------------------------------------------

def test_normalize_stat_count_treats_missing_and_negative_as_zero():
    assert normalize_stat_count(None) == 0
    assert normalize_stat_count(-1) == 0
    assert normalize_stat_count("-1") == 0


def test_normalize_stat_count_keeps_positive_values():
    assert normalize_stat_count(0) == 0
    assert normalize_stat_count(3) == 3
    assert normalize_stat_count("7") == 7


# ---------------------------------------------------------------------------
# merge_ship_faction_rows (production merge of per-faction SQL rows)
# ---------------------------------------------------------------------------

def test_merge_ship_faction_rows_sums_across_factions_and_keeps_breakdown():
    rows = [
        {
            "ship_xws": "t65xwing",
            "faction": "rebelalliance",
            "list_count": 2,
            "different_lists_count": 1,
            "wins": 3,
            "games": 6,
        },
        {
            "ship_xws": "t65xwing",
            "faction": "galacticrepublic",
            "list_count": 1,
            "different_lists_count": 1,
            "wins": 1,
            "games": 2,
        },
    ]
    merged = merge_ship_faction_rows(rows)
    assert len(merged) == 1
    ship = merged[0]
    assert ship["xws"] == "t65xwing"
    assert set(ship["factions"]) == {"rebelalliance", "galacticrepublic"}
    assert ship["games_count"] == 8
    assert ship["list_count"] == 3
    assert ship["different_lists_count"] == 2
    assert ship["wins"] == 4
    assert ship["faction_stats"] == {
        "rebelalliance": {"games_count": 6, "list_count": 2, "wins": 3, "entries_count": 0, "squadron_count": 0},
        "galacticrepublic": {"games_count": 2, "list_count": 1, "wins": 1, "entries_count": 0, "squadron_count": 0},
    }


def test_merge_ship_faction_rows_keeps_ships_with_zero_games():
    # A ship with a faction row but no tournament data must still appear
    # (no-data ships are shown on the ships page under restrictive filters).
    rows = [
        {
            "ship_xws": "tierainbow",
            "faction": "galacticempire",
            "list_count": 0,
            "different_lists_count": 0,
            "wins": 0,
            "games": 0,
        },
    ]
    merged = merge_ship_faction_rows(rows)
    assert len(merged) == 1
    assert merged[0]["xws"] == "tierainbow"
    assert merged[0]["games_count"] == 0
    assert merged[0]["faction_stats"]["galacticempire"]["games_count"] == 0


def test_merge_ship_faction_rows_returns_one_entry_per_ship():
    rows = [
        {"ship_xws": "t65xwing", "faction": "rebelalliance", "list_count": 1, "different_lists_count": 1, "wins": 1, "games": 2},
        {"ship_xws": "t65xwing", "faction": "rebelalliance", "list_count": 1, "different_lists_count": 1, "wins": 0, "games": 1},
        {"ship_xws": "z95af4headhunter", "faction": "scumandvillainy", "list_count": 1, "different_lists_count": 1, "wins": 1, "games": 3},
    ]
    merged = merge_ship_faction_rows(rows)
    assert len(merged) == 2
    by_xws = {s["xws"]: s for s in merged}
    assert by_xws["t65xwing"]["games_count"] == 3
    assert by_xws["z95af4headhunter"]["games_count"] == 3


# ---------------------------------------------------------------------------
# Counting-rule spec tests
#
# The ships SQL collapses the pilots-array join to DISTINCT
# (playerstanding, ship) pairs before summing record values, so games are
# counted once per list-side and lists once per ship. These tests pin the
# intended semantics with a small reference reducer over raw occurrence
# rows (one row per pilot occurrence × match — i.e. exactly what a naive
# join produces, including the duplicates the production query removes).
# ---------------------------------------------------------------------------

def _reference_ship_counts(occurrences):
    """
    occurrences: iterable of dicts with keys
        ps_id, list_id, match_id, ship_xws, won
    (one entry per pilot occurrence in a list, per match that list played).

    Returns {ship_xws: {"lists": set(ps_id), "games": set((match_id, ps_id)),
                        "wins": set((match_id, ps_id))}} — the canonical
    semantics: list counted once per list, match counted once per
    (match, list-side) pair.
    """
    ships: dict[str, dict] = defaultdict(lambda: {"lists": set(), "games": set(), "wins": set()})
    for occ in occurrences:
        ship = ships[occ["ship_xws"]]
        ship["lists"].add(occ["ps_id"])
        pair = (occ["match_id"], occ["ps_id"])
        ship["games"].add(pair)
        if occ["won"]:
            ship["wins"].add(pair)
    return ships


def _pilot_occurrences(ps_id, list_id, match_ids, pilots, ship_xws):
    """Emit one occurrence per pilot copy per match (the naive-join shape)."""
    rows = []
    for match_id in match_ids:
        for _ in range(pilots):
            rows.append({
                "ps_id": ps_id,
                "list_id": list_id,
                "match_id": match_id,
                "ship_xws": ship_xws,
                "won": False,
            })
    return rows


def test_rule_duplicate_ship_in_same_list_counts_list_once():
    # A list with 4 copies of the same ship counts as ONE list.
    occ = _pilot_occurrences(
        ps_id=1, list_id=10, match_ids=[100, 101, 102, 103], pilots=4, ship_xws="t65xwing"
    )
    counts = _reference_ship_counts(occ)
    assert len(counts["t65xwing"]["lists"]) == 1


def test_rule_distinct_match_list_pairs_per_ship():
    # A list with 4 T-65s that played 4 matches counts as 4 games and 1 list
    # (the match is counted once per list-side, not once per pilot copy).
    occ = _pilot_occurrences(
        ps_id=1, list_id=10, match_ids=[100, 101, 102, 103], pilots=4, ship_xws="t65xwing"
    )
    counts = _reference_ship_counts(occ)
    assert len(counts["t65xwing"]["games"]) == 4
    assert len(counts["t65xwing"]["lists"]) == 1


def test_rule_shared_ship_in_match_counts_twice():
    # Two opposing lists in one match both contain the same ship: the match
    # counts once per side (2 total), on top of each side's other games.
    occ = (
        _pilot_occurrences(ps_id=1, list_id=10, match_ids=[100, 101, 102, 103], pilots=4, ship_xws="t65xwing")
        + _pilot_occurrences(ps_id=2, list_id=20, match_ids=[100, 104, 105, 106], pilots=1, ship_xws="t65xwing")
    )
    counts = _reference_ship_counts(occ)
    games = counts["t65xwing"]["games"]
    assert len(games) == 8  # 4 per side; match 100 appears once per side
    shared = [(m, p) for (m, p) in games if m == 100]
    assert len(shared) == 2  # match 100 counted twice — once per list-side
    assert len(counts["t65xwing"]["lists"]) == 2


# ---------------------------------------------------------------------------
# End-to-end test against a real Postgres (runs against the local dev stack)
# ---------------------------------------------------------------------------

T65_PILOTS = ["biggsdarklighter", "bluesquadronescort", "cavernangelszealot", "edriotwotubes"]
Z95_PILOTS = ["binayrepirate", "blacksunsoldier", "kaatoleeachos"]


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="ship stats counting integration test requires PostgreSQL (jsonb_array_elements)",
)
class TestShipStatsCountingPostgres:
    """Insert a tiny synthetic tournament and verify the aggregation rules."""

    def test_duplicate_ship_and_shared_match_counting(self):
        from backend.database import engine
        from backend.models import Tournament, List, PlayerStanding, Match
        from backend.data_structures.location import Location

        marker = f"zz-ships-count-{uuid4().hex[:8]}"
        t65 = "t65xwing"
        z95 = "z95af4headhunter"

        list_json_1 = {
            "faction": "rebelalliance",
            "pilots": [{"id": pid} for pid in T65_PILOTS],  # 4 copies of t65xwing
        }
        list_json_2 = {
            "faction": "rebelalliance",
            "pilots": [{"id": T65_PILOTS[0]}] + [{"id": pid} for pid in Z95_PILOTS],
        }

        with Session(engine) as session:
            tournament = Tournament(
                name=f"{marker}-tournament",
                date=date(2001, 1, 1),
                location=Location(city="Test", country="Test", continent="Test"),
                player_count=2,
                url="http://localhost/test",
                source=Source.LONGSHANKS,
                format=Format.XWA,
            )
            session.add(tournament)
            session.flush()

            list1 = List(
                canonical_signature=f"{marker}-L1",
                faction="rebelalliance",
                faction_xws_normalized="rebelalliance",
                name="T65 x4",
                points=200,
                pilot_count=4,
                ship_list="t65xwing,t65xwing,t65xwing,t65xwing",
                list_json=list_json_1,
            )
            list2 = List(
                canonical_signature=f"{marker}-L2",
                faction="rebelalliance",
                faction_xws_normalized="rebelalliance",
                name="T65 + 3x Z95",
                points=200,
                pilot_count=4,
                ship_list="t65xwing,z95af4headhunter,z95af4headhunter,z95af4headhunter",
                list_json=list_json_2,
            )
            session.add_all([list1, list2])
            session.flush()

            ps1 = PlayerStanding(
                tournament_id=tournament.id,
                player_name=f"{marker}-p1",
                swiss_rank=1,
                swiss_wins=2,
                swiss_losses=2,
                swiss_draws=0,
                list_json=list_json_1,
                list_id=list1.id,
            )
            ps2 = PlayerStanding(
                tournament_id=tournament.id,
                player_name=f"{marker}-p2",
                swiss_rank=2,
                swiss_wins=2,
                swiss_losses=2,
                swiss_draws=0,
                list_json=list_json_2,
                list_id=list2.id,
            )
            session.add_all([ps1, ps2])
            session.flush()

            match = Match(
                tournament_id=tournament.id,
                round_number=1,
                round_type="swiss",
                player1_id=ps1.id,
                player2_id=ps2.id,
                player1_score=2,
                player2_score=0,
                winner_id=ps1.id,
                is_bye=False,
            )
            session.add(match)
            session.commit()

            try:
                # Filter to the synthetic tournament's date range so real data
                # cannot influence the expected numbers.
                filters = {"date_start": "2000-12-31", "date_end": "2001-01-02"}
                stats = aggregate_ship_stats(
                    filters,
                    data_source=DataSource.XWA,
                )
                by_xws = {s["xws"]: s for s in stats}

                # t65xwing appears 4x in ps1's list and 1x in ps2's list.
                # Both sides played 4 games each (2W 2L).
                ship = by_xws[t65]
                assert ship["list_count"] == 2            # distinct lists per ship
                assert ship["games_count"] == 8           # 4 per side (match counted once per side)
                assert ship["wins"] == 4
                assert ship["faction_stats"]["rebelalliance"] == {
                    "games_count": 8,
                    "list_count": 2,
                    "wins": 4,
                    "entries_count": 2,
                    "squadron_count": 2,
                }
                # The two lists share one match: that match must count twice.
                # (4 + 4 = 8 games total would be impossible if the shared
                # match were counted only once: 4+4 includes it once per side.)

                # z95af4headhunter only appears in ps2's list (3 copies).
                z = by_xws[z95]
                assert z["list_count"] == 1
                assert z["games_count"] == 4
                assert z["wins"] == 2

                # Sanity: the naive (buggy) join would have multiplied ps1's
                # record by the 4 pilot copies -> 16 + 4 = 20 games, not 8.
                assert ship["games_count"] != 20
            finally:
                with Session(engine) as cleanup:
                    match = cleanup.get(Match, match.id)
                    if match:
                        cleanup.delete(match)
                    ps1 = cleanup.get(PlayerStanding, ps1.id)
                    ps2 = cleanup.get(PlayerStanding, ps2.id)
                    if ps1:
                        cleanup.delete(ps1)
                    if ps2:
                        cleanup.delete(ps2)
                    for lst in (list1, list2):
                        lst = cleanup.get(List, lst.id)
                        if lst:
                            cleanup.delete(lst)
                    tournament = cleanup.get(Tournament, tournament.id)
                    if tournament:
                        cleanup.delete(tournament)
                    cleanup.commit()
