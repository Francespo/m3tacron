import sys
import os

# Add root to path
sys.path.insert(0, os.getcwd())

try:
    print("Importing backend.utils.xwing_data.ships...")
    import m3tacron.backend.utils.xwing_data.ships as ships
    print("Success: ships")
except Exception as e:
    print(f"Failed to import ships: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing backend.utils.xwing_data.upgrades...")
    import m3tacron.backend.utils.xwing_data.upgrades as upgrades
    print("Success: upgrades")
except Exception as e:
    print(f"Failed to import upgrades: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing backend.utils.xwing_data.__init__...")
    import m3tacron.backend.utils.xwing_data as xwing_data
    print("Success: xwing_data init")
except Exception as e:
    print(f"Failed to import xwing_data init: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing backend.utils...")
    import m3tacron.backend.utils as utils
    print("Success: backend.utils")
except Exception as e:
    print(f"Failed to import backend.utils: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing list_browser page module...")
    import m3tacron.pages.list_browser
    print("Success: list_browser")
except Exception as e:
    print(f"Failed to run list_browser: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing squadrons_browser page module...")
    import m3tacron.pages.squadrons_browser
    print("Success: squadrons_browser")
except Exception as e:
    print(f"Failed to run squadrons_browser: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing tournament_detail page module...")
    import m3tacron.pages.tournament_detail
    print("Success: tournament_detail")
except Exception as e:
    print(f"Failed to run tournament_detail: {e}")
    import traceback
    traceback.print_exc()
