import sqlite3

def check_db():
    conn = sqlite3.connect("metacron.db")
    c = conn.cursor()
    
    print("--- Tournament 2545 (Achtung X-Wing) ---")
    c.execute("SELECT count(*) FROM match WHERE tournament_id=2545")
    print(f"Match Count: {c.fetchone()[0]}")
    
    c.execute("SELECT id, player1_id, player2_id, is_bye FROM match WHERE tournament_id=2545")
    rows = c.fetchall()
    for r in rows:
        print(f"Match {r[0]}: P1={r[1]}, P2={r[2]}, Bye={r[3]}")
        if r[1] == 0:
             print("  [ALERT] Player 1 ID is 0 (Unknown)")
        if r[2] == 0 and not r[3]:
             print("  [ALERT] Player 2 ID is 0 (Unknown)")

    print("\n--- GLOBAL STATS ---")
    c.execute("SELECT count(*) FROM tournament")
    print(f"Tournaments: {c.fetchone()[0]}")
    
    c.execute("SELECT count(*) FROM match")
    total_matches = c.fetchone()[0]
    print(f"Total Matches: {total_matches}")
    
    print("\n--- Tournament 2546 ---")
    c.execute("SELECT id, player1_id, player2_id, is_bye FROM match WHERE tournament_id=2546")
    rows = c.fetchall()
    for r in rows:
        print(f"Match {r[0]}: P1={r[1]}, P2={r[2]}")
        if r[1] == 0: print("  [ALERT] P1 Unknown")
        if r[2] == 0 and not r[3]: print("  [ALERT] P2 Unknown")
            
    conn.close()

if __name__ == "__main__":
    check_db()
