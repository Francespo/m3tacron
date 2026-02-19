import sqlite3
import json
from datetime import datetime, timedelta

db_path = "metacron_new.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"Connected to {db_path}")

# 1. Check Tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cursor.fetchall()]
print(f"Tables: {tables}")

if "tournament" not in tables:
    print("ERROR: table 'tournament' missing!")
    exit(1)

print("\n--- SCHEMA INFO ---")
cursor.execute("PRAGMA table_info(tournament);")
print("Tournament Columns:", [r[1] for r in cursor.fetchall()])
cursor.execute("PRAGMA table_info(playerresult);")
print("PlayerResult Columns:", [r[1] for r in cursor.fetchall()])
print("-------------------\n")

# 2. Seed Data
print("Cleaning old data...")
cursor.execute("DELETE FROM playerresult;")
cursor.execute("DELETE FROM tournament;")
conn.commit()

print("Seeding data...")
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
location_json = json.dumps({"city": "Space", "country": "Orbit", "continent": "Galaxy"})

# Tournament
try:
    cursor.execute("""
        INSERT INTO tournament (name, date, format, url, location, player_count, team_count, platform)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("XWA Galactic Raw", yesterday, "xwa", "http://raw.sql", location_json, 10, 0, "RealLife"))
    
    t_id = cursor.lastrowid
    print(f"Inserted Tournament ID: {t_id}")

    # PlayerResult (JSON dumping)
    list_json = json.dumps({
        "faction": "rebelalliance", 
        "pilots": [{"name": "wedgeantilles", "ship": "xwing"}]
    })
    
    cursor.execute("""
        INSERT INTO playerresult (
            tournament_id, player_name, swiss_rank, list_json, 
            swiss_wins, swiss_losses, swiss_draws, swiss_tie_breaker_points
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (t_id, "Raw SQL Pilot", 1, list_json, 5, 0, 0, 0))
    print("Inserted PlayerResult")

    conn.commit()
    print("Commit successful.")

except Exception as e:
    print(f"Error inserting: {e}")
    conn.rollback()

conn.close()
