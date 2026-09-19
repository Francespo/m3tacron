"""Regression tests for the generic XWA ship-split alias resolver.

Covers the BTA-NR2 Y-Wing split: pre-split ``btanr2ywing`` carrying the
``wartimeloadout`` upgrade versus the integrated ``btanr2wywing`` chassis whose
pilots carry the ``-wartime`` suffix. Resolution is read-time only.
"""

from backend.api.formatters import enrich_list_data
from backend.data_structures.data_source import DataSource
from backend.utils.list_keys import get_list_key, get_ship_list, iter_upgrade_ids
from backend.utils.xwing_data.aliases import (
    SHIP_SPLIT_ALIASES,
    resolve_pilot_reference,
    resolve_ship_id,
)
from backend.utils.xwing_data.parser import parse_xws
from backend.utils.xwing_data.pilots import get_pilot_info
from backend.utils.xwing_data.ships import get_ship_info

PLAIN = "btanr2ywing"
INTEGRATED = "btanr2wywing"
TRIGGER = "wartimeloadout"

PILOT_PLAIN = "zoriibliss"
PILOT_INTEGRATED = "zoriibliss-wartime"


def _legacy_list(with_trigger: bool) -> dict:
    """Pre-split XWS encoding: base pilot id, optional Wartime Loadout upgrade."""
    upgrades = {"talent": ["deadeyeshot"]}
    if with_trigger:
        upgrades["configuration"] = [TRIGGER]
    return {
        "faction": "resistance",
        "pilots": [
            {"id": PILOT_PLAIN, "ship": PLAIN, "points": 4, "upgrades": upgrades}
        ],
    }


def _canonical_list() -> dict:
    """Post-split XWS encoding: -wartime pilot on the integrated chassis."""
    return {
        "faction": "resistance",
        "pilots": [
            {
                "id": PILOT_INTEGRATED,
                "ship": INTEGRATED,
                "points": 12,
                "upgrades": {"talent": ["deadeyeshot"]},
            }
        ],
    }


# --- alias map / generic mechanism -----------------------------------------


def test_alias_map_drives_the_split_without_id_hardcoding():
    aliases = {a.deprecated_id: a for a in SHIP_SPLIT_ALIASES}
    alias = aliases[PLAIN]
    assert alias.variant_id == INTEGRATED
    assert TRIGGER in alias.trigger_upgrades
    # The variant itself is not a deprecated id (no self-referential rule).
    assert INTEGRATED not in aliases


def test_resolve_ship_id_is_contextual():
    assert resolve_ship_id(PLAIN, [TRIGGER]) == INTEGRATED
    assert resolve_ship_id(PLAIN, []) == PLAIN
    assert resolve_ship_id(PLAIN, ["deadeyeshot"]) == PLAIN
    # Unknown ids pass through untouched.
    assert resolve_ship_id("t65xwing", [TRIGGER]) == "t65xwing"


def test_unrelated_trigger_does_not_change_ship_resolution():
    assert resolve_ship_id(PLAIN, ["integratedsfoils"]) == PLAIN


# --- (a) legacy reference WITH wartimeloadout -> integrated variant ---------


def test_legacy_reference_with_trigger_resolves_to_integrated():
    ship = get_ship_info(PLAIN, upgrades=[TRIGGER])
    assert ship is not None
    assert ship["xws"] == INTEGRATED
    assert {s["value"] for s in ship["stats"] if s["type"] == "shields"} == {5}

    pilot = get_pilot_info(PILOT_PLAIN, upgrades=[TRIGGER])
    assert pilot is not None
    assert pilot["ship_xws"] == INTEGRATED
    assert pilot["cost"] == 12

    resolution = resolve_pilot_reference(PILOT_PLAIN, [TRIGGER])
    assert resolution.pilot_xws == PILOT_INTEGRATED
    assert resolution.ship_xws == INTEGRATED
    assert resolution.absorbed_upgrades == frozenset({TRIGGER})


# --- (b) legacy reference WITHOUT wartimeloadout -> plain chassis -----------


def test_legacy_reference_without_trigger_stays_plain():
    ship = get_ship_info(PLAIN, upgrades=[])
    assert ship is not None
    assert ship["xws"] == PLAIN
    assert {s["value"] for s in ship["stats"] if s["type"] == "shields"} == {3}

    pilot = get_pilot_info(PILOT_PLAIN, upgrades=["deadeyeshot"])
    assert pilot is not None
    assert pilot["ship_xws"] == PLAIN
    assert pilot["cost"] == 11

    resolution = resolve_pilot_reference(PILOT_PLAIN, ["deadeyeshot"])
    assert resolution.pilot_xws == PILOT_PLAIN
    assert resolution.ship_xws == PLAIN
    assert resolution.absorbed_upgrades == frozenset()


# --- (c) old and new references collapse to one identity --------------------


def test_old_and_new_encoding_share_canonical_signature():
    assert get_list_key(_legacy_list(with_trigger=True)) == get_list_key(
        _canonical_list()
    )


def test_old_and_new_encoding_share_ship_list():
    assert get_ship_list(_legacy_list(with_trigger=True)) == get_ship_list(
        _canonical_list()
    )
    assert get_ship_list(_legacy_list(with_trigger=True)) == INTEGRATED


def test_plain_encoding_keeps_its_own_identity():
    assert get_list_key(_legacy_list(with_trigger=False)) != get_list_key(
        _canonical_list()
    )
    assert get_ship_list(_legacy_list(with_trigger=False)) == PLAIN


def test_mixed_old_and_new_references_yield_one_identity():
    def pilot(pid, ship, upgrades):
        return {"id": pid, "ship": ship, "points": 0, "upgrades": upgrades}

    old = {
        "pilots": [
            pilot(PILOT_PLAIN, PLAIN, {"configuration": [TRIGGER]}),
            pilot("tezanasz-wartime", INTEGRATED, {"missile": ["ionmissiles"]}),
        ]
    }
    new = {
        "pilots": [
            pilot(PILOT_INTEGRATED, INTEGRATED, {}),
            pilot("tezanasz-wartime", INTEGRATED, {"missile": ["ionmissiles"]}),
        ]
    }
    assert get_list_key(old) == get_list_key(new)
    assert get_ship_list(old) == get_ship_list(new) == f"{INTEGRATED},{INTEGRATED}"


def test_ship_list_derives_ship_from_pilot_when_absent():
    payload = {
        "pilots": [
            {"id": PILOT_PLAIN, "upgrades": {"configuration": [TRIGGER]}},
        ]
    }
    assert get_ship_list(payload) == INTEGRATED


# --- import path (parse_xws) and API enrichment -----------------------------


def test_parse_xws_import_normalises_legacy_code():
    parsed = parse_xws(_legacy_list(with_trigger=True))
    assert len(parsed["pilots"]) == 1
    pilot = parsed["pilots"][0]
    assert pilot["xws"] == PILOT_INTEGRATED
    assert pilot["ship"] == "BTA-NR2 Y-Wing"
    assert TRIGGER not in [u["xws"] for u in pilot["upgrades"]]


def test_parse_xws_import_keeps_plain_code_plain():
    parsed = parse_xws(_legacy_list(with_trigger=False))
    pilot = parsed["pilots"][0]
    assert pilot["xws"] == PILOT_PLAIN
    assert TRIGGER not in [u["xws"] for u in pilot["upgrades"]]


def test_enrich_list_data_resolves_legacy_reference_and_drops_absorbed_upgrade():
    stats = {
        "signature": "sig",
        "faction": "resistance",
        "points": 4,
        "pilots": [
            {
                "id": PILOT_PLAIN,
                "ship": PLAIN,
                "points": 4,
                "upgrades": {"configuration": [TRIGGER], "talent": ["deadeyeshot"]},
            }
        ],
    }
    out = enrich_list_data(stats, DataSource.XWA)
    assert out.pilots[0].xws == PILOT_INTEGRATED
    assert out.pilots[0].ship_xws == INTEGRATED
    assert [u.xws for u in out.pilots[0].upgrades] == ["deadeyeshot"]


# --- Legacy source: documented open question, not a fix ---------------------


def test_legacy_source_leaves_pre_split_ids_unchanged():
    """The Legacy source has no integrated variant, so nothing is rewritten."""
    ship = get_ship_info(PLAIN, DataSource.LEGACY, upgrades=[TRIGGER])
    assert ship is not None
    assert ship["xws"] == PLAIN

    resolution = resolve_pilot_reference(PILOT_PLAIN, [TRIGGER], DataSource.LEGACY)
    assert resolution.pilot_xws == PILOT_PLAIN
    assert resolution.ship_xws == PLAIN
    assert resolution.absorbed_upgrades == frozenset()


# --- upgrade id extraction --------------------------------------------------


def test_iter_upgrade_ids_handles_all_stored_shapes():
    assert iter_upgrade_ids({"talent": ["a", "b"]}) == ["a", "b"]
    assert iter_upgrade_ids(["a", "b"]) == ["a", "b"]
    assert iter_upgrade_ids({"talent": ["a"]}) == ["a"]
    assert iter_upgrade_ids([{"xws": "a"}, {"id": "b"}]) == ["a", "b"]
    assert iter_upgrade_ids(None) == []
