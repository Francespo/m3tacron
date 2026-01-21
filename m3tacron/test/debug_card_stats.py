import sys
from pathlib import Path
 # Redirect stdout to file
sys.stdout = open("debug_clean.txt", "w", encoding="utf-8")

from sqlmodel import Session, select

# Add project root to sys.path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from m3tacron.backend.database import engine
from m3tacron.backend.models import Tournament, PlayerResult
from m3tacron.backend.card_analytics import aggregate_card_stats
from m3tacron.backend.enums.formats import Format

def debug_db_content():
    print("--- Debugging Database Content ---")
    with Session(engine) as session:
        # Check Tournaments
        tournaments = session.exec(select(Tournament).limit(5)).all()
        print(f"Total Tournaments: {session.exec(select(Tournament)).all().__len__()}")
        for t in tournaments:
            # Format might be a string or Enum, handle gracefully
            fmt_val = t.format.value if hasattr(t.format, 'value') else t.format
            print(f"Tournament: ID={t.id}, Date={t.date}, Format={fmt_val} (Raw Type: {type(t.format)})")

        # Check Results
        results = session.exec(select(PlayerResult).limit(5)).all()
        print(f"Total Results: {session.exec(select(PlayerResult)).all().__len__()}")
        for r in results:
            print(f"Result: ID={r.id}, TournamentID={r.tournament_id}, List JSON keys: {r.list_json.keys() if r.list_json else 'None'}")
            if r.list_json and "pilots" in r.list_json:
                 print(f"  -> Pilots: {[p.get('id') or p.get('name') for p in r.list_json['pilots']]}")

def test_aggregation():
    print("\n--- Testing Aggregation Logic ---")
    
    # Test 1: No filters (Broadest possible) and Debug Loop
    filters = {
        "allowed_formats": None, # Should allow all
        "date_start": "",
        "date_end": "",
        "faction": "all",
        "search_text": ""
    }
    print("Test 1: No filters")
    
    # Manually check why aggregation might fail using DB directly here
    with Session(engine) as session:
        query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
        rows = session.exec(query).all()
        print(f"  Debug: Found {len(rows)} raw rows (PlayerResult + Tournament).")
        
        count_processed = 0
        for result, tournament in rows[:5]: # Check first 5
             xws = result.list_json
             if not xws:
                 print(f"  Debug: Row {result.id} has empty list_json.")
                 continue
             
             print(f"  Debug: Row {result.id}, Format={tournament.format}, List Faction={xws.get('faction')}")
             pilots = xws.get("pilots", [])
             print(f"    Pilots found: {len(pilots)}")
             for p in pilots:
                 pid = p.get("id") or p.get("name")
                 print(f"      - Pilot ID: {pid}")

    from m3tacron.backend.xwing_data import get_data_dir, ROOT_DIR
    print(f"  Debug: ROOT_DIR calculated as: {ROOT_DIR}")
    print(f"  Debug: XWA Data Dir: {get_data_dir('xwa')}")
    print(f"  Debug: Legacy Data Dir: {get_data_dir('legacy')}")
    print(f"  Debug: XWA Dir Exists? {get_data_dir('xwa').exists()}")
    
    from m3tacron.backend.card_analytics import load_all_pilots
    pilots = load_all_pilots("xwa")
    print(f"  Debug: load_all_pilots('xwa') returned {len(pilots)} pilots.")
    
    pilots_legacy = load_all_pilots("legacy")
    print(f"  Debug: load_all_pilots('legacy') returned {len(pilots_legacy)} pilots.")

    try:
        results = aggregate_card_stats(filters, sort_mode="popularity", mode="pilots", data_source="xwa")
        print(f"  Results count: {len(results)}")
        if results:
            print("  Top 3:", results[:3])
    except Exception as e:
        print(f"  Error: {e}")

    # Test 2: Standard XWA Format Filter (Simulate UI default)
    # Correct value is "xwa" based on formats.py
    filters["allowed_formats"] = ["xwa", "amg", "2.5"] 
    print(f"\nTest 2: With allowed_formats={filters['allowed_formats']}")
    results = aggregate_card_stats(filters, sort_mode="popularity", mode="pilots", data_source="xwa")
    print(f"  Results count: {len(results)}")

    # Test 3: Legacy Source
    print("\nTest 3: Legacy Source")
    results = aggregate_card_stats(filters, sort_mode="popularity", mode="pilots", data_source="legacy")
    print(f"  Results count: {len(results)}")

if __name__ == "__main__":
    try:
        debug_db_content()
        test_aggregation()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
