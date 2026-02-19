from backend.utils.xwing_data.pilots import load_all_pilots, get_pilot_info
from backend.utils.xwing_data.upgrades import get_upgrade_info

print("--- Pilot Data Debug ---")
pilot = get_pilot_info("ketsuonyo")
if pilot:
    print(f"Name: {pilot.get('name')}")
    print(f"Loadout: {pilot.get('loadout')}")
    print(f"Image: {pilot.get('image')}")
else:
    print("Pilot not found")

print("\n--- Upgrade Data Debug ---")
# Check a common upgrade
upg = get_upgrade_info("fearless")
if upg:
    print(f"Name: {upg.get('name')}")
    print(f"Image: {upg.get('image')}")
else:
    print("Upgrade not found")
