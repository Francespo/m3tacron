"""
Debug DB connection and tables.
"""
import os
import os
import sys
# Add project root (where rxconfig.py lives)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sqlite3
from sqlalchemy import create_engine, inspect

# Check CWD
print(f"CWD: {os.getcwd()}")

# Check file existence
db_file = "longshanks_dev.db"
if os.path.exists(db_file):
    print(f"File {db_file} exists. Size: {os.path.getsize(db_file)} bytes")
else:
    print(f"File {db_file} NOT found.")

# Raw SQLite check
try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Raw Tables: {tables}")
    conn.close()
except Exception as e:
    print(f"Raw SQLite error: {e}")

# SQLAlchemy Check
try:
    from m3tacron.backend.database import engine
    print(f"SQLAlchemy URL: {engine.url}")
    inspector = inspect(engine)
    sa_tables = inspector.get_table_names()
    print(f"SQLAlchemy Tables: {sa_tables}")
except Exception as e:
    print(f"SQLAlchemy error: {e}")
