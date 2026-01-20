import sqlite3
import os

def check_db(name):
    print(f"--- Checking {name} ---")
    if not os.path.exists(name):
        print("File does not exist.")
        return
        
    try:
        conn = sqlite3.connect(name)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        print(f"Tables: {tables}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

check_db("metacron.db")
check_db("longshanks_dev.db")
check_db("dev.db")
