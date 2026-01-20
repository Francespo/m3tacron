import sqlite3
import os

DB_PATH = "metacron.db"

def clean():
    if not os.path.exists(DB_PATH):
        print("No DB found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("Cleaning database...")
    tables = ["match", "playerresult", "tournament"]
    for t in tables:
        try:
            c.execute(f"DELETE FROM {t}")
            print(f"Deleted from {t}")
        except Exception as e:
            print(f"Error cleaning {t}: {e}")
            
    conn.commit()
    conn.close()
    print("Database cleaned.")

if __name__ == "__main__":
    clean()
