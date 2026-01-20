import sqlite3
import os

DB_PATH = "dev.db"

def verify():
    if not os.path.exists(DB_PATH):
        print("dev.db missing!")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check for unlinked matches
    c.execute("SELECT count(*) FROM match WHERE player1_id = 0")
    p1_unlinked = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM match WHERE player2_id = 0 AND is_bye = 0")
    p2_unlinked = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM match")
    total = c.fetchone()[0]
    
    print(f"Total Matches: {total}")
    print(f"Unlinked P1: {p1_unlinked}")
    print(f"Unlinked P2: {p2_unlinked}")
    
    if p1_unlinked == 0 and p2_unlinked == 0:
        print("SUCCESS: All non-bye matches have linked players.")
    else:
        print("FAILURE: Some matches have unlinked players.")
        print("\n--- Unlinked P1 (Sample) ---")
        c.execute("SELECT DISTINCT tournament_id, round_number, p1_name_temp FROM match WHERE player1_id=0 LIMIT 10")
        for row in c.fetchall():
            print(f"Event {row[0]} R{row[1]}: '{row[2]}'")
            
        print("\n--- Unlinked P2 (Sample) ---")
        c.execute("SELECT DISTINCT tournament_id, round_number, p2_name_temp FROM match WHERE player2_id=0 AND is_bye=0 LIMIT 10")
        for row in c.fetchall():
            print(f"Event {row[0]} R{row[1]}: '{row[2]}'")
            
        print("\n--- Available Players (Sample from Event 30230) ---")
        c.execute("SELECT player_name FROM playerresult WHERE tournament_id=30230 LIMIT 10")
        for row in c.fetchall():
            print(f"'{row[0]}'")
        
    conn.close()

if __name__ == "__main__":
    verify()
