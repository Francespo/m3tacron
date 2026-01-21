"""
Verification script for Card Analytics.
"""
import sys
import os

# Add project root to path (3 levels up from test/script.py)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from m3tacron.backend.card_analytics import aggregate_card_stats
# We assume DB is initialized by running app usually, but we need to ensure engine is ready
from m3tacron.backend.database import engine, create_db_and_tables 

def verify_pilots_simple():
    print(f"DB Engine: {engine.url}")
    create_db_and_tables()
    print("Verifying Pilot Aggregation (No filters)...")
    results = aggregate_card_stats({}, mode="pilots")
    print(f"Loaded {len(results)} pilots")
    if results:
        top = results[0]
        print(f"Top Pilot: {top['name']} (Count: {top['count']}, WR: {top['win_rate']}%)")
    else:
        print("No results found - is DB empty?")

if __name__ == "__main__":
    try:
        verify_pilots_simple()
        print("\nVerification Complete.")
    except Exception as e:
        print(f"\nVerification Failed: {e}")
        import traceback
        traceback.print_exc()
