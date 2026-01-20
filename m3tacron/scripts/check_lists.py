import sqlite3
import json

def check_lists():
    conn = sqlite3.connect("metacron.db")
    c = conn.cursor()
    
    print("--- Tournament 2546 Lists ---")
    c.execute("SELECT player_name, list_json FROM playerresult WHERE tournament_id=2546")
    rows = c.fetchall()
    
    populated = 0
    for name, l_json in rows:
        try:
            data = json.loads(l_json)
            if data and data != {}:
                populated += 1
                # print(f"  {name}: Has List")
            else:
                pass
                # print(f"  {name}: NO List")
        except:
             print(f"  {name}: Invalid JSON")
             
    print(f"Total Players: {len(rows)}")
    print(f"Players with List: {populated}")
    
    conn.close()

if __name__ == "__main__":
    check_lists()
