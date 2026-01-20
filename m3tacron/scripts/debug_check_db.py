import sqlite3
import os

DB_PATH = "longshanks_dev.db"

if not os.path.exists(DB_PATH):
    print("DB missing")
else:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM match")
    print(f"Total Matches in DB: {c.fetchone()[0]}")
    
    c.execute("PRAGMA table_info(match)")
    cols = [r[1] for r in c.fetchall()]
    print(f"Match Columns: {cols}")
    
    conn.close()
