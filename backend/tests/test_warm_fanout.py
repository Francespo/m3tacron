from backend.main import _partition_lists_by_ship


def test_partitions_lists_under_every_ship_they_contain():
    items = [{"signature": "sig-a"}, {"signature": "sig-b"}, {"signature": "sig-c"}]
    ships = {"sig-a": "t65xwing,ywing", "sig-b": "t65xwing", "sig-c": "tieadvancedx1"}

    by_ship = _partition_lists_by_ship(items, ships)

    assert [i["signature"] for i in by_ship["t65xwing"]] == ["sig-a", "sig-b"]
    assert [i["signature"] for i in by_ship["ywing"]] == ["sig-a"]
    assert [i["signature"] for i in by_ship["tieadvancedx1"]] == ["sig-c"]


def test_partition_skips_lists_without_a_known_ship_list():
    # Regression: the aggregations do not expose ship_list, so looking it up on
    # the item returned "" and every ship got an empty list (blank Top lists).
    items = [{"signature": "missing"}]
    assert _partition_lists_by_ship(items, {}) == {}
