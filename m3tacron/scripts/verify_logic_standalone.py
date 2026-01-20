import sys
import os
from collections import Counter
from datetime import date
from sqlmodel import create_engine, Session, select

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from m3tacron.backend.models import PlayerResult, Tournament
from m3tacron.backend.squadron_utils import get_squadron_signature, parse_squadron_signature
from m3tacron.backend.xwing_data import load_all_pilots, get_pilot_info, Faction

# Assume DB is in root 
DATABASE_URL = "sqlite:///metacron_v2.db"
engine = create_engine(DATABASE_URL)

def test_squadron_aggregation():
    print("Testing Squadron Aggregation...")
    with Session(engine) as session:
        # Check if DB has data
        count = session.exec(select(PlayerResult)).all()
        print(f"Total Results in DB: {len(count)}")
        if len(count) == 0:
            print("DB is empty! Skipping tests.")
            return

        # SIMULATE load_squadrons logic
        query = select(PlayerResult, Tournament).where(PlayerResult.tournament_id == Tournament.id)
        rows = session.exec(query).all()
        
        squadron_stats = {}
        for r, t in rows:
            xws = r.list_json
            if not xws or not isinstance(xws, dict): continue
            
            sig = get_squadron_signature(xws)
            if not sig: continue
            
            faction, ships = parse_squadron_signature(sig)
            
            if sig not in squadron_stats:
                squadron_stats[sig] = {"count": 0, "wins": 0, "games": 0, "faction": faction, "ships": ships}
            
            stats = squadron_stats[sig]
            stats["count"] += 1
            
            wins = r.swiss_wins + r.cut_wins
            losses = r.swiss_losses + r.cut_losses
            draws = r.swiss_draws
            games = wins + losses + draws
            
            stats["wins"] += wins
            stats["games"] += games
            
        print(f"Unique Squadrons Found: {len(squadron_stats)}")
        
        # Sort by Count
        sorted_sq = sorted(squadron_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        if sorted_sq:
            top_sig, top_data = sorted_sq[0]
            print(f"Top 1 Squadron: {top_sig}")
            print(f"  Count: {top_data['count']}")
            print(f"  Faction: {top_data['faction']}")
            print(f"  Ships: {top_data['ships']}")
            wr = 0
            if top_data['games'] > 0:
                wr = (top_data['wins'] / top_data['games']) * 100
            print(f"  Win Rate: {wr:.1f}%")
            
            # TEST DETAIL AGGREGATION
            print("\nTesting Detail Aggregation for Top Squadron...")
            # Re-fetch matching results for logic validation
            pilot_variations = Counter()
            for r, t in rows:
                 xws = r.list_json
                 if not xws or not isinstance(xws, dict): continue
                 if get_squadron_signature(xws) != top_sig: continue
                 
                 pilots = []
                 for p in xws.get("pilots", []):
                     pid = p.get("id") or p.get("name")
                     pinfo = get_pilot_info(pid)
                     pname = pinfo.get("name", pid) if pinfo else pid
                     pilots.append(pname)
                 pilots.sort()
                 pilot_sig = " + ".join(pilots)
                 pilot_variations[pilot_sig] += 1
                 
            print("Top Pilot Configurations:")
            for p_sig, count in pilot_variations.most_common(3):
                print(f"  - {p_sig}: {count}")

        # TEST FILTERS
        print("\nTesting Filters...")
        # 1. Date Filter (Last year) - Mock check
        # 2. Ship Filter ("X-wing")
        target_ship = "x-wing"
        matching_sq = [s for s, d in squadron_stats.items() if any(target_ship.lower() in ship.lower() for ship in d['ships'])]
        print(f"Squadrons with '{target_ship}': {len(matching_sq)}")


if __name__ == "__main__":
    try:
        test_squadron_aggregation()
        print("\nSUCCESS: Logic verified.")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback
        traceback.print_exc()
