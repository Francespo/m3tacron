import sys
import os

# Ensure we can import m3tacron
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from m3tacron.backend.analytics.core import aggregate_card_stats
from m3tacron.backend.data_structures.formats import Format
from m3tacron.backend.data_structures.data_source import DataSource

def test_filtering():
    print("Testing Filtering Logic...")
    
    # 1. No Filter (Should show everything if logic allows, or nothing?)
    # Based on code: if allowed_formats is None/Empty, it shows ALL.
    filters_all = {} 
    stats_all = aggregate_card_stats(filters_all, data_source=DataSource.XWA)
    print(f"Total entries (No Filter): {sum(s['count'] for s in stats_all)}")
    
    # 2. Filter ONLY XWA
    filters_xwa = {"allowed_formats": ["xwa"]}
    stats_xwa = aggregate_card_stats(filters_xwa, data_source=DataSource.XWA)
    print(f"Total entries (Only XWA): {sum(s['count'] for s in stats_xwa)}")

    # 3. Filter ONLY Legacy
    filters_legacy = {"allowed_formats": ["legacy_x2po", "legacy_xlc"]}
    stats_legacy = aggregate_card_stats(filters_legacy, data_source=DataSource.XWA)
    print(f"Total entries (Only Legacy): {sum(s['count'] for s in stats_legacy)}")
    
    # 4. Filter Non-Existent
    filters_none = {"allowed_formats": ["dummy_format"]}
    stats_none = aggregate_card_stats(filters_none, data_source=DataSource.XWA)
    print(f"Total entries (Dummy Format): {sum(s['count'] for s in stats_none)}")

    # 5. Filter Empty List (Should be 0 after fix)
    filters_empty = {"allowed_formats": []}
    stats_empty = aggregate_card_stats(filters_empty, data_source=DataSource.XWA)
    print(f"Total entries (Empty List): {sum(s['count'] for s in stats_empty)}")


if __name__ == "__main__":
    test_filtering()
