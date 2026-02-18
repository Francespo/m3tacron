
import sys
import os

# Ensure backend can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from m3tacron.backend.utils.squadron import get_list_signature

def test_get_list_signature_basic():
    xws = {
        "faction": "rebelalliance",
        "pilots": [
            {
                "id": "luke-skywalker",
                "upgrades": {
                    "force-power": ["instinctive-aim"],
                    "astromech": ["r2-d2"]
                }
            },
            {
                "id": "wedge-antilles",
                "upgrades": {
                    "talent": ["predator"]
                }
            }
        ]
    }
    
    # We expect a signature that encodes faction, ships, pilots, and upgrades
    # Note: get_list_signature implementation details might vary, but it should be consistent
    sig = get_list_signature(xws)
    assert sig is not None
    assert "rebelalliance" in sig
    assert "luke-skywalker" in sig
    assert "wedge-antilles" in sig
    assert "r2-d2" in sig
    assert "predator" in sig

def test_get_list_signature_sorting():
    xws1 = {
        "faction": "rebelalliance",
        "pilots": [
            {"id": "luke-skywalker", "upgrades": {"astromech": ["r2-d2"]}},
            {"id": "wedge-antilles"}
        ]
    }
    
    xws2 = {
        "faction": "rebelalliance",
        "pilots": [
            {"id": "wedge-antilles"},
            {"id": "luke-skywalker", "upgrades": {"astromech": ["r2-d2"]}}
        ]
    }
    
    # Signatures should be identical despite different pilot order
    assert get_list_signature(xws1) == get_list_signature(xws2)

def test_get_list_signature_upgrade_sorting():
    xws1 = {
        "faction": "rebelalliance",
        "pilots": [
            {
                "id": "luke-skywalker",
                "upgrades": {
                    "force-power": ["instinctive-aim", "sense"],
                }
            }
        ]
    }
    
    xws2 = {
        "faction": "rebelalliance",
        "pilots": [
            {
                "id": "luke-skywalker",
                "upgrades": {
                    "force-power": ["sense", "instinctive-aim"],
                }
            }
        ]
    }
    # Signatures should be identical despite different upgrade order within a slot
    assert get_list_signature(xws1) == get_list_signature(xws2)

def test_get_list_signature_different_upgrades():
    xws1 = {
        "faction": "rebelalliance",
        "pilots": [{"id": "luke-skywalker", "upgrades": {"astromech": ["r2-d2"]}}]
    }
    
    xws2 = {
        "faction": "rebelalliance",
        "pilots": [{"id": "luke-skywalker", "upgrades": {"astromech": ["r5-d8"]}}]
    }
    
    
    assert get_list_signature(xws1) != get_list_signature(xws2)

if __name__ == "__main__":
    try:
        test_get_list_signature_basic()
        test_get_list_signature_sorting()
        test_get_list_signature_upgrade_sorting()
        test_get_list_signature_different_upgrades()
        print("All tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
