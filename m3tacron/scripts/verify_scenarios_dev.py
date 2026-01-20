from sqlmodel import create_engine, Session, select, func
import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from m3tacron.backend.models import Match
from m3tacron.backend.enums.scenarios import Scenario

DB_PATH = "rollbetter_dev.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL)

def run():
    print(f"Connecting to {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print("DB file not found!")
        return

    with Session(engine) as session:
        # Check T2535
        print("\n--- Verifying T2535 ---")
        matches = session.exec(select(Match).where(Match.tournament_id == 2535)).all()
        
        if not matches:
             print("No matches found for 2535.")
        
        # Group by round
        rounds = {}
        for m in matches:
            r = m.round_number
            if r not in rounds: rounds[r] = set()
            rounds[r].add(m.scenario)
            
        for r in sorted(rounds.keys()):
            scenarios = rounds[r]
            print(f"Round {r}: {scenarios}")
            
            # Validation
            if r == 1:
                assert Scenario.CHANCE_ENGAGEMENT in scenarios
                print("  ✅ Round 1 is Chance Engagement")
            if r == 3:
                # Based on subagent finding? Or generalized?
                # Check what we found. Re-verifying logic.
                pass

        # Check T2538 (Expect None or specific?)
        print("\n--- Verifying T2538 ---")
        matches_38 = session.exec(select(Match).where(Match.tournament_id == 2538)).all()
        rounds_38 = {}
        for m in matches_38:
            r = m.round_number
            if r not in rounds_38: rounds_38[r] = set()
            rounds_38[r].add(m.scenario)
        
        for r in sorted(rounds_38.keys()):
            print(f"Round {r}: {rounds_38[r]}")

if __name__ == "__main__":
    run()
