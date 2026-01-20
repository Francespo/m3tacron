import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from m3tacron.pages.squadrons import SquadronsState
from m3tacron.backend.database import create_db_and_tables

# Initialize DB (if needed, or just rely on existing connection from engine)
# create_db_and_tables()

print("Initializing SquadronsState...")
state = SquadronsState()

print("Loading Squadrons (Default parameters)...")
state.load_squadrons()
print(f"Total Squadrons: {state.total_squadrons}")
print(f"Total Lists: {state.total_lists}")

if state.squadrons_data:
    top_squadron = state.squadrons_data[0]
    print(f"Top Squadron: {top_squadron['signature']} ({top_squadron['count']} lists)")
    print(f"Win Rate: {top_squadron['win_rate']}%")
    
    # Test Detail View
    print(f"Opening details for: {top_squadron['signature']}")
    state.open_detail(top_squadron['signature'])
    
    details = state.squadron_details
    print(f"Detail Subtitle: {details.get('subtitle')}")
    print("Common Pilot Configurations:")
    for conf in details.get("common_pilots", []):
        print(f" - {conf['pilots']} ({conf['count']}x)")

print("\nTesting Filters...")
# Test Faction Filter
state.set_faction_filter("rebelalliance")
print(f"Rebel Squadrons: {state.total_squadrons}")

# Test Sorting
state.set_sort_mode("win_rate")
if state.squadrons_data:
    top_win = state.squadrons_data[0]
    print(f"Top Win Rate Squadron: {top_win['signature']} ({top_win['win_rate']}%)")
    
print("Verification Complete.")
