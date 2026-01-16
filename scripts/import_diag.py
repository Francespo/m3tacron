import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print(f"Python executable: {sys.executable}")
print(f"Path[0]: {sys.path[0]}")

try:
    import m3tacron.backend.scrapers.rollbetter
    print("DIRECT module import: OK")
except Exception as e:
    print(f"DIRECT module import FAIL: {str(e)[:200]}")
    # import traceback
    # traceback.print_exc()

print("-" * 20)

try:
    from m3tacron.backend.scrapers import rollbetter
    print("PACKAGE module import: OK")
except Exception as e:
    print(f"PACKAGE module import FAIL: {str(e)[:200]}")

print("-" * 20)

try:
    from m3tacron.backend.scrapers import rb_scrape_tournament
    print("EXPORT import: OK")
except Exception as e:
    print(f"EXPORT import FAIL: {str(e)[:200]}")
