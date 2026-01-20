import sqlite3

DB_PATH = "rollbetter_dev.db"

def run():
    print(f"Connecting to raw sqlite: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n--- Raw 'platform' values from Tournament ---")
    try:
        cursor.execute("SELECT DISTINCT platform FROM tournament")
        rows = cursor.fetchall()
        for r in rows:
            print(f"Raw Value: '{r[0]}'")
    except Exception as e:
        print(e)
        
    print("\n--- Raw 'scenario' values from Match ---")
    try:
        cursor.execute("SELECT DISTINCT scenario FROM match WHERE scenario IS NOT NULL")
        rows = cursor.fetchall()
        for r in rows:
            print(f"Raw Value: '{r[0]}'")
    except Exception as e:
        print(e)

    conn.close()

if __name__ == "__main__":
    run()
