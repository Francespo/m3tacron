import pytest
from backend.data.points_history import (
    get_latest_points_date,
    get_points_updates,
    load_points_history,
)


def test_points_history_loading():
    for system in ["legacy", "xwa", "amg", "ffg"]:
        data = load_points_history(system)
        assert data is not None, f"Failed to load points history for {system}"
        assert "updates" in data
        assert len(data["updates"]) > 0
        assert "latest_date" in data
        assert data["latest_date"] == data["updates"][0]["date"]


def test_latest_points_date():
    assert get_latest_points_date("legacy") == "2026-03-31"
    assert get_latest_points_date("legacy_x2po") == "2026-03-31"
    assert get_latest_points_date("xwa") == "2026-08-16"
    assert get_latest_points_date("amg") == "2024-09-06"
    assert get_latest_points_date("ffg") == "2020-11-24"


def test_points_updates_content():
    updates = get_points_updates("legacy")
    assert len(updates) >= 9
    first = updates[0]
    assert first["date"] == "2026-03-31"
    assert "March 2026" in first["version"]

    xwa_updates = get_points_updates("xwa")
    assert len(xwa_updates) >= 7
    first_xwa = xwa_updates[0]
    assert first_xwa["date"] == "2026-08-16"
    assert "50P 2.1" in first_xwa["version"]
