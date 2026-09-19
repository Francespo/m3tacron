"""Regression tests for the generic XWA ship-split alias resolver.

Covers the BTA-NR2 Y-Wing split: the pre-split ``btanr2ywing`` chassis carrying
the ``wartimeloadout`` configuration versus the integrated ``btanr2wywing``
chassis whose pilots carry the ``-wartime`` suffix. Both encodings are in the
wild and must resolve to one identity at read time; nothing is rewritten.
"""

import copy
import json

from backend.api.formatters import enrich_list_data
from backend.data_structures.data_source import DataSource
from backend.utils.list_keys import get_list_key, get_ship_list, iter_upgrade_ids
from backend.utils.xwing_data.aliases import (
    SHIP_SPLIT_ALIASES,
    get_ship_split_alias,
    resolve_pilot_reference,
    resolve_ship_id,
)
from backend.utils.xwing_data.labels import SHIP_DISPLAY_LABELS, ship_display_name
from backend.utils.xwing_data.parser import parse_xws
from backend.utils.xwing_data.pilots import get_pilot_info, load_all_pilots
from backend.utils.xwing_data.ships import get_ship_info, load_all_ships
from backend.utils.yasb import get_xws_string

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
            {"id": PILOT_PLAIN, "ship": PLAIN, "points": 11, "upgrades": upgrades}
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


# --- generic mechanism (one map entry, no id hardcoding) --------------------


def test_split_is_declared_as_one_alias_map_entry():
    aliases = {a.deprecated_id: a for a in SHIP_SPLIT_ALIASES}
    alias = aliases[PLAIN]
    assert alias.variant_id == INTEGRATED
    assert TRIGGER in alias.absorbed_upgrades
    # The variant is not itself a deprecated id (no self-referential rule).
    assert INTEGRATED not in aliases
    assert get_ship_split_alias("t65xwing") is None


def test_resolve_ship_id_is_contextual_and_passes_unknown_ids_through():
    assert resolve_ship_id(PLAIN, [TRIGGER]) == INTEGRATED
    assert resolve_ship_id(PLAIN, []) == PLAIN
    assert resolve_ship_id(PLAIN, ["deadeyeshot"]) == PLAIN
    assert resolve_ship_id("t65xwing", [TRIGGER]) == "t65xwing"


# --- (a) legacy reference WITH wartimeloadout -> integrated variant ---------


def test_legacy_reference_with_trigger_resolves_to_integrated_variant():
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


def test_legacy_reference_without_trigger_stays_on_the_plain_chassis():
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


# --- (c) old and new encodings collapse to one identity ---------------------


def test_old_and_new_encodings_share_one_canonical_signature():
    """`get_list_key` is the value stored in list.canonical_signature."""
    assert get_list_key(_legacy_list(with_trigger=True)) == get_list_key(
        _canonical_list()
    )


def test_old_and_new_encodings_share_one_ship_list():
    assert get_ship_list(_legacy_list(with_trigger=True)) == INTEGRATED
    assert get_ship_list(_legacy_list(with_trigger=True)) == get_ship_list(
        _canonical_list()
    )


def test_plain_encoding_keeps_its_own_identity():
    assert get_ship_list(_legacy_list(with_trigger=False)) == PLAIN
    assert get_list_key(_legacy_list(with_trigger=False)) != get_list_key(
        _canonical_list()
    )


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


def test_ship_list_falls_back_to_the_pilot_chassis():
    payload = {"pilots": [{"id": PILOT_PLAIN, "upgrades": {"configuration": [TRIGGER]}}]}
    assert get_ship_list(payload) == INTEGRATED


# --- (d) export guard: read-time resolution never mutates stored XWS --------


def test_export_emits_raw_stored_ids_and_nothing_is_mutated():
    legacy = _legacy_list(with_trigger=True)
    snapshot = copy.deepcopy(legacy)

    exported = get_xws_string(legacy)
    assert PILOT_PLAIN in exported
    assert TRIGGER in exported
    assert PILOT_INTEGRATED not in exported, "export must not rewrite stored XWS"

    # Every read-time hook must leave the stored payload byte-identical.
    parse_xws(legacy)
    get_list_key(legacy)
    get_ship_list(legacy)
    enrich_list_data(
        {
            "signature": "sig",
            "faction": "resistance",
            "points": 11,
            "pilots": legacy["pilots"],
        },
        DataSource.XWA,
    )
    assert legacy == snapshot


def test_export_of_the_post_split_encoding_is_also_untouched():
    canonical = _canonical_list()
    snapshot = copy.deepcopy(canonical)
    exported = get_xws_string(canonical)
    assert PILOT_INTEGRATED in exported
    get_list_key(canonical)
    get_ship_list(canonical)
    assert canonical == snapshot


def test_iter_upgrade_ids_handles_every_stored_shape():
    assert iter_upgrade_ids({"talent": ["a", "b"]}) == ["a", "b"]
    assert iter_upgrade_ids(["a", "b"]) == ["a", "b"]
    assert iter_upgrade_ids({"talent": "a"}) == ["a"]
    assert iter_upgrade_ids([{"xws": "a"}, {"id": "b"}]) == ["a", "b"]
    assert iter_upgrade_ids(None) == []


# --- (e) display labels, and ids that must never move -----------------------


def test_display_labels_differ_and_preserve_the_full_plain_name():
    assert ship_display_name(PLAIN) == "BTA-NR2 Y-Wing"
    assert ship_display_name(INTEGRATED) == "BTA-NR2 Y-Wing (Wartime Loadout)"
    assert ship_display_name("t65xwing", "X-wing") == "X-wing"
    assert set(SHIP_DISPLAY_LABELS) == {PLAIN, INTEGRATED}

    ships = load_all_ships(DataSource.XWA)
    assert ships[PLAIN]["name"] == "BTA-NR2 Y-Wing"
    assert ships[INTEGRATED]["name"] == "BTA-NR2 Y-Wing (Wartime Loadout)"


def test_display_labels_do_not_touch_xws_or_pilot_ids():
    ships = load_all_ships(DataSource.XWA)
    assert PLAIN in ships and INTEGRATED in ships
    assert ships[PLAIN]["xws"] == PLAIN
    assert ships[INTEGRATED]["xws"] == INTEGRATED

    pilots = load_all_pilots(DataSource.XWA)
    assert PILOT_PLAIN in pilots and PILOT_INTEGRATED in pilots
    assert pilots[PILOT_INTEGRATED]["ship_xws"] == INTEGRATED
    # A pilot's ship label goes through the same display layer. Without it the
    # variant pilot would read "BTA-NR2 Y-Wing" on its detail page.
    assert pilots[PILOT_PLAIN]["ship"] == "BTA-NR2 Y-Wing"
    assert pilots[PILOT_INTEGRATED]["ship"] == "BTA-NR2 Y-Wing (Wartime Loadout)"


def test_wartime_pilot_ids_keep_their_suffix_and_are_the_only_variant_ids():
    pilots = load_all_pilots(DataSource.XWA)
    wartime = {
        xws for xws, info in pilots.items() if info.get("ship_xws") == INTEGRATED
    }
    assert len(wartime) == 10
    assert all(xws.endswith("-wartime") for xws in wartime)


# --- import and API enrichment put the absorbed upgrade back into the chassis


def test_parse_xws_import_resolves_and_drops_the_absorbed_upgrade():
    parsed = parse_xws(_legacy_list(with_trigger=True))
    assert len(parsed["pilots"]) == 1
    pilot = parsed["pilots"][0]
    assert pilot["xws"] == PILOT_INTEGRATED
    assert pilot["ship"] == "BTA-NR2 Y-Wing (Wartime Loadout)"
    assert [u["xws"] for u in pilot["upgrades"]] == ["deadeyeshot"]


def test_parse_xws_import_keeps_a_plain_reference_plain():
    parsed = parse_xws(_legacy_list(with_trigger=False))
    pilot = parsed["pilots"][0]
    assert pilot["xws"] == PILOT_PLAIN
    assert pilot["ship"] == "BTA-NR2 Y-Wing"
    assert [u["xws"] for u in pilot["upgrades"]] == ["deadeyeshot"]


def test_enrich_list_data_resolves_and_drops_the_absorbed_upgrade():
    out = enrich_list_data(
        {
            "signature": "sig",
            "faction": "resistance",
            "points": 11,
            "pilots": [
                {
                    "id": PILOT_PLAIN,
                    "ship": PLAIN,
                    "points": 11,
                    "upgrades": {"configuration": [TRIGGER], "talent": ["deadeyeshot"]},
                }
            ],
        },
        DataSource.XWA,
    )
    assert out.pilots[0].xws == PILOT_INTEGRATED
    assert out.pilots[0].ship_xws == INTEGRATED
    assert [u.xws for u in out.pilots[0].upgrades] == ["deadeyeshot"]


def test_enrich_list_data_of_the_post_split_encoding_matches():
    legacy = enrich_list_data(
        {
            "signature": "sig",
            "faction": "resistance",
            "points": 11,
            "pilots": _legacy_list(with_trigger=True)["pilots"],
        },
        DataSource.XWA,
    )
    canonical = enrich_list_data(
        {
            "signature": "sig",
            "faction": "resistance",
            "points": 12,
            "pilots": _canonical_list()["pilots"],
        },
        DataSource.XWA,
    )
    # `original_points` intentionally keeps the raw stored squad points, which
    # legitimately differ between the two encodings; identity must not.
    assert legacy.points == canonical.points
    assert json.dumps([p.model_dump() for p in legacy.pilots], sort_keys=True) == (
        json.dumps([p.model_dump() for p in canonical.pilots], sort_keys=True)
    )


# --- Legacy source has no integrated variant: nothing is rewritten ---------


def test_legacy_source_leaves_pre_split_ids_unchanged():
    ship = get_ship_info(PLAIN, DataSource.LEGACY, upgrades=[TRIGGER])
    assert ship is not None
    assert ship["xws"] == PLAIN

    resolution = resolve_pilot_reference(PILOT_PLAIN, [TRIGGER], DataSource.LEGACY)
    assert resolution.pilot_xws == PILOT_PLAIN
    assert resolution.ship_xws == PLAIN
    assert resolution.absorbed_upgrades == frozenset()
