"""Regression tests for human-readable ship labels and chassis abilities.

The two halves of the BTA-NR2 Y-Wing split share the same vendored ``name``
("BTA-NR2 Y-Wing"), so the display layer overlays a distinct label on each.
These tests pin the labels, the untouched internal ids, and the chassis
ability that the split exposes.
"""

from backend.data_structures.data_source import DataSource
from backend.utils.xwing_data.labels import (
    SHIP_DISPLAY_LABELS,
    get_ship_display_name,
)
from backend.utils.xwing_data.pilots import load_all_pilots
from backend.utils.xwing_data.ships import get_ship_info, load_all_ships

PLAIN = "btanr2ywing"
INTEGRATED = "btanr2wywing"

PLAIN_LABEL = "Y-wing"
INTEGRATED_LABEL = "Y-wing (Wartime Loadout)"

PLAIN_ABILITY = "Intuitive Interface"
INTEGRATED_ABILITY = "Devastating Barrage"


class TestDisplayLabels:
    def test_both_halves_of_the_split_have_distinct_labels(self):
        assert get_ship_display_name(PLAIN) == PLAIN_LABEL
        assert get_ship_display_name(INTEGRATED) == INTEGRATED_LABEL
        assert PLAIN_LABEL != INTEGRATED_LABEL

    def test_unmapped_ship_keeps_vendored_name(self):
        assert get_ship_display_name("t65xwing", "T-65 X-Wing") == "T-65 X-Wing"
        # No fallback: the xws id is the last resort, never a fabricated name.
        assert get_ship_display_name("t65xwing") == "t65xwing"

    def test_label_map_only_covers_the_split(self):
        assert set(SHIP_DISPLAY_LABELS) == {PLAIN, INTEGRATED}

    def test_load_all_ships_applies_labels(self):
        ships = load_all_ships(DataSource.XWA)
        assert ships[PLAIN]["name"] == PLAIN_LABEL
        assert ships[INTEGRATED]["name"] == INTEGRATED_LABEL

    def test_load_all_ships_labels_legacy_plain_chassis(self):
        # Legacy has no integrated variant; the plain chassis is still labelled.
        ships = load_all_ships(DataSource.LEGACY)
        assert ships[PLAIN]["name"] == PLAIN_LABEL
        assert INTEGRATED not in ships

    def test_get_ship_info_returns_labelled_name(self):
        assert get_ship_info(PLAIN)["name"] == PLAIN_LABEL
        assert get_ship_info(INTEGRATED)["name"] == INTEGRATED_LABEL


class TestIdsAreUntouched:
    """Labels must never become identity: ids, xws codes and suffixes stay."""

    def test_ship_xws_codes_unchanged(self):
        ships = load_all_ships(DataSource.XWA)
        assert ships[PLAIN]["xws"] == PLAIN
        assert ships[INTEGRATED]["xws"] == INTEGRATED

    def test_variant_pilots_keep_wartime_suffix(self):
        pilots = load_all_pilots(DataSource.XWA)
        assert "zoriibliss-wartime" in pilots
        # The pre-split pilot id still exists and is a different entry.
        assert "zoriibliss" in pilots
        assert (
            pilots["zoriibliss"]["ship_xws"]
            != pilots["zoriibliss-wartime"]["ship_xws"]
        )

    def test_internal_pilot_ship_field_stays_raw_for_search(self):
        # Free-text pilot search matches on this field, so it keeps the vendored
        # name rather than the display label.
        pilots = load_all_pilots(DataSource.XWA)
        assert pilots["zoriibliss"]["ship"] == "BTA-NR2 Y-Wing"
        assert pilots["zoriibliss-wartime"]["ship"] == "BTA-NR2 Y-Wing"


class TestChassisAbility:
    def test_plain_chassis_ability(self):
        assert load_all_ships(DataSource.XWA)[PLAIN]["ship_ability"]["name"] == (
            PLAIN_ABILITY
        )

    def test_integrated_chassis_ability_differs(self):
        ability = load_all_ships(DataSource.XWA)[INTEGRATED]["ship_ability"]
        assert ability["name"] == INTEGRATED_ABILITY
        assert ability["name"] != PLAIN_ABILITY
        # Own statline too: the integrated variant carries 5 shields vs 3.
        integrated_shields = [
            s["value"]
            for s in load_all_ships(DataSource.XWA)[INTEGRATED]["stats"]
            if s["type"] == "shields"
        ]
        plain_shields = [
            s["value"]
            for s in load_all_ships(DataSource.XWA)[PLAIN]["stats"]
            if s["type"] == "shields"
        ]
        assert integrated_shields == [5]
        assert plain_shields == [3]

    def test_legacy_plain_chassis_ability(self):
        assert load_all_ships(DataSource.LEGACY)[PLAIN]["ship_ability"]["name"] == (
            PLAIN_ABILITY
        )
