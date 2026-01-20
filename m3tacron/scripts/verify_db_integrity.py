import sqlite3
import os

DB_PATH = "longshanks_dev.db"

def verify():
    if not os.path.exists(DB_PATH):
        print("dev.db missing!")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check for unlinked matches (P1)
    c.execute("SELECT count(*) FROM match WHERE player1_id = 0")
    p1_unlinked = c.fetchone()[0]
    
    # Check for unlinked matches (P2) - Excluding Byes
    c.execute("SELECT count(*) FROM match WHERE player2_id = 0 AND is_bye = 0")
    p2_unlinked = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM match")
    total = c.fetchone()[0]
    
    print(f"Total Matches: {total}")
    print(f"Unlinked P1: {p1_unlinked}")
    print(f"Unlinked P2: {p2_unlinked}")
    
    # Check Events count
    c.execute("SELECT count(*) FROM tournament")
    events = c.fetchone()[0]
    print(f"Events: {events}")
    
    if p1_unlinked == 0 and p2_unlinked == 0:
        print("SUCCESS: All matches linked.")
    else:
        print("WARNING: Some matches unlinked.")
        # Print breakdown by event
        c.execute("""
            SELECT t.name, count(*) 
            FROM match m JOIN tournament t ON m.tournament_id = t.id 
            WHERE m.player1_id = 0 
            GROUP BY t.name
        """)
        rows = c.fetchall()
        if rows:
            print("Unlinked P1 by Event:")
            for r in rows:
                print(f"  {r[0]}: {r[1]}")
                
    conn.close()

if __name__ == "__main__":
    verify()
