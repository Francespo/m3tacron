
# import pytest # Removed to allow running without pytest installed
from m3tacron.backend.analytics.core import aggregate_card_stats
from m3tacron.backend.data_structures.data_source import DataSource
from m3tacron.backend.data_structures.sorting_order import SortingCriteria, SortDirection

def test_aggregate_card_stats_returns_all_cards():
    """
    Test that aggregate_card_stats returns all cards even if they have 0 usage.
    """
    # Use filters that should result in 0 matches from actual tournament data
    filters = {
        "search_text": "NonExistentCardNameThatShouldNeverExistXYZ",
        "date_start": "1900-01-01",
        "date_end": "1900-01-02" 
    }
    
    # But wait, search_text filters the initialization too! 
    # So we should use a date range that has no tournaments, but NO text filter.
    filters_no_matches = {
        "date_start": "2099-01-01",
        "date_end": "2099-01-02"
    }

    results = aggregate_card_stats(
        filters=filters_no_matches,
        sort_criteria=SortingCriteria.POPULARITY,
        sort_direction=SortDirection.DESCENDING,
        mode="pilots",
        data_source=DataSource.XWA
    )
    
    assert len(results) > 0, "Should return result list > 0 (all pilots)"
    
    # Pick a random result and verify structure
    first = results[0]
    assert first["games"] == 0
    assert first["count"] == 0
    assert first["win_rate"] == "NA"
    
def test_win_rate_logic():
    """
    Test that win rate is NA for 0 games.
    """
    filters = {
        "date_start": "2099-01-01",
        "date_end": "2099-01-02"
    }
    
    results = aggregate_card_stats(filters=filters, mode="pilots")
    
    for r in results:
        assert r["games"] == 0
        assert r["win_rate"] == "NA"

if __name__ == "__main__":
    # Manually run if pytest fails
    try:
        test_aggregate_card_stats_returns_all_cards()
        print("test_aggregate_card_stats_returns_all_cards passed")
        test_win_rate_logic()
        print("test_win_rate_logic passed")
    except Exception as e:
        print(f"FAILED: {e}")
