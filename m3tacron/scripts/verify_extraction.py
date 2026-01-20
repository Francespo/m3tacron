import sqlite3
import os

DB_PATH = "longshanks_dev.db"

# Event IDs
LEGACY_IDS = [30504, 29336, 27819, 26633, 22357, 31423]
XWA_IDS = [30230, 31565, 31461]

def verify():
    if not os.path.exists(DB_PATH):
        print("db missing!")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    with open("final_verification_results.txt", "w") as f:
        f.write("--- Verifying FIRST PLAYER ID (Legacy) ---\n")
        for tid in LEGACY_IDS:
            c.execute("SELECT count(*) FROM match WHERE tournament_id=? AND first_player_id > 0", (tid,))
            count = c.fetchone()[0]
            c.execute("SELECT count(*) FROM match WHERE tournament_id=?", (tid,))
            total = c.fetchone()[0]
            f.write(f"Event {tid}: {count}/{total} matches have First Player recorded.\n")
            
        f.write("\n--- Verifying SCENARIO (XWA) ---\n")
        for tid in XWA_IDS:
            c.execute("SELECT count(*) FROM match WHERE tournament_id=? AND scenario IS NOT NULL", (tid,))
            count = c.fetchone()[0]
            c.execute("SELECT count(*) FROM match WHERE tournament_id=?", (tid,))
            total = c.fetchone()[0]
            f.write(f"Event {tid}: {count}/{total} matches have Scenario recorded.\n")
            # Check scenario values
            c.execute("SELECT DISTINCT scenario FROM match WHERE tournament_id=?", (tid,))
            scenarios = [row[0] for row in c.fetchall() if row[0]]
            f.write(f"  Scenarios found: {scenarios}\n")

    conn.close()

if __name__ == "__main__":
    verify()
