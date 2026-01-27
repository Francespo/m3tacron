import sys
import os
# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from m3tacron.backend.analytics.core import aggregate_card_stats
from m3tacron.backend.data_structures.data_source import DataSource

def test_aggregation():
    filters = {
        "allowed_formats": [],
        "search_text": "",
        "faction": [],
        "ship": [],
        "initiative": [],
        "upgrade_type": []
    }
    
    print("Testing Pilots Aggregation...")
    pilots = aggregate_card_stats(filters, sort_mode="popularity", mode="pilots", data_source=DataSource.XWA)
    print(f"Found {len(pilots)} pilots.")
    if pilots:
        print(f"Top Pilot: {pilots[0]['name']} ({pilots[0]['count']} lists)")
        # Check if they have images
        with_image = [p for p in pilots if p.get('image')]
        print(f"Pilots with images: {len(with_image)}/{len(pilots)}")

    print("\nTesting Upgrades Aggregation...")
    upgrades = aggregate_card_stats(filters, sort_mode="popularity", mode="upgrades", data_source=DataSource.XWA)
    print(f"Found {len(upgrades)} upgrades.")
    if upgrades:
        print(f"Top Upgrade: {upgrades[0]['name']} ({upgrades[0].get('type')})")
        # Check if type is formatted
        u_type = upgrades[0].get('type', '')
        print(f"Formatted Type Example: {u_type}")
        
        with_image = [u for u in upgrades if u.get('image')]
        print(f"Upgrades with images: {len(with_image)}/{len(upgrades)}")

if __name__ == "__main__":
    test_aggregation()
