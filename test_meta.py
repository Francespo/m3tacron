
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from backend.analytics.factions import get_meta_snapshot
from backend.data_structures.data_source import DataSource

try:
    print("Testing get_meta_snapshot(DataSource.XWA)...")
    res = get_meta_snapshot(DataSource.XWA)
    print("Success!")
except Exception as e:
    print(f"Failed with error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
