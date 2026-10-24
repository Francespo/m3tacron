import backend.list_index as li


def test_cte_uses_the_flat_tables_when_ready(monkeypatch):
    monkeypatch.setattr(li, "list_index_ready", lambda: True)
    pilots = li.list_pilots_cte()
    upgrades = li.list_pilot_upgrades_cte()
    assert "FROM list_pilot" in pilots
    assert "FROM list_pilot_upgrade" in upgrades
    assert "jsonb_array_elements" not in pilots
    assert "jsonb_array_elements" not in upgrades


def test_cte_falls_back_to_json(monkeypatch):
    monkeypatch.setattr(li, "list_index_ready", lambda: False)
    pilots = li.list_pilots_cte()
    upgrades = li.list_pilot_upgrades_cte()
    assert "jsonb_array_elements" in pilots
    assert "jsonb_array_elements" in upgrades
    # Same shape in both paths: callers reference these columns.
    for column in ("list_id", "entry_idx", "pilot_xws"):
        assert column in pilots
    for column in ("list_id", "entry_idx", "pilot_xws", "upgrade_xws"):
        assert column in upgrades


def test_ready_requires_the_current_data_version(monkeypatch):
    monkeypatch.setattr(li, "current_version", lambda: "105")
    monkeypatch.setattr(li, "_stored_version", lambda: "104")
    monkeypatch.setattr(li, "_checked_at", 0.0)
    assert li.list_index_ready() is False

    monkeypatch.setattr(li, "_stored_version", lambda: "105")
    monkeypatch.setattr(li, "_checked_at", 0.0)
    assert li.list_index_ready() is True
