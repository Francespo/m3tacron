from backend.tests.test_api import (
    test_root, test_meta_snapshot, test_tournaments, test_tournaments_with_search,
    test_lists, test_pilots, test_upgrades, test_ships
)

tests = [
    test_root, test_meta_snapshot, test_tournaments, test_tournaments_with_search,
    test_lists, test_pilots, test_upgrades, test_ships
]

for t in tests:
    try:
        t()
        print(f"PASS: {t.__name__}")
    except Exception as e:
        import traceback
        print(f"FAIL: {t.__name__}")
        traceback.print_exc()
