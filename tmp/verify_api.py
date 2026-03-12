import sys
from fastapi.testclient import TestClient
import json

# Add parent directory to path to import backend
sys.path.append(".")

try:
    from backend.main import app
    client = TestClient(app)
except Exception as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

def test_endpoint(path, name):
    print(f"\n--- Testing {name} ({path}) ---")
    try:
        response = client.get(path)
        if response.status_code != 200:
            print(f"FAILED: Status {response.status_code}")
            return False
        
        data = response.json()
        print(f"SUCCESS: Status 200")
        
        # Check for XWS identifiers in common places
        if "items" in data:
            for item in data["items"][:1]:
                check_xws(item)
        elif isinstance(data, list):
            for item in data[:1]:
                check_xws(item)
        else:
            check_xws(data)
            
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def check_xws(obj):
    if not isinstance(obj, dict): return
    
    keys = ["faction_xws", "ship_xws", "xws"]
    found = [k for k in keys if k in obj]
    if found:
        print(f"Found identifiers: { {k: obj[k] for k in found} }")
    
    # Recursive check for nested lists/pilots
    if "pilots" in obj and isinstance(obj["pilots"], list):
        for p in obj["pilots"][:1]:
            check_xws(p)
    if "upgrades" in obj and isinstance(obj["upgrades"], list):
        for u in obj["upgrades"][:1]:
            check_xws(u)
    if "info" in obj:
        check_xws(obj["info"])

endpoints = [
    ("/api/meta-snapshot", "Meta Snapshot"),
    ("/api/lists", "Lists"),
    ("/api/squadrons", "Squadrons"),
    ("/api/ships", "Ships"),
    ("/api/cards", "Cards"),
    ("/api/tournaments", "Tournaments"),
]

# Run tests
all_pass = True
for path, name in endpoints:
    if not test_endpoint(path, name):
        all_pass = False

# Test Detail endpoints if we can find IDs
print("\n--- Testing Detail Endpoints ---")
try:
    # Try to find a pilot xws from card list
    cards_res = client.get("/api/cards")
    if cards_res.status_code == 200:
        pilots = cards_res.json().get("items", [])
        if pilots:
            pxws = pilots[0].get("xws")
            test_endpoint(f"/api/pilot/{pxws}", f"Pilot Detail: {pxws}")
            
    # Try to find a ship xws from ships list
    ships_res = client.get("/api/ships")
    if ships_res.status_code == 200:
        ships = ships_res.json().get("items", [])
        if ships:
            sxws = ships[0].get("xws")
            test_endpoint(f"/api/ship/{sxws}", f"Ship Detail: {sxws}")
            
except Exception as e:
    print(f"Detail test error: {e}")

if all_pass:
    print("\nOVERALL STATUS: PASS")
else:
    print("\nOVERALL STATUS: FAIL")
    sys.exit(1)
