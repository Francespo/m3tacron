
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_factions_endpoint():
    print("Testing /factions endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/factions")
        if response.status_code != 200:
            print(f"FAILED: /factions returned {response.status_code}")
            return False
        
        data = response.json()
        
        # Check meta fields
        meta = data.get("meta", {})
        print(f"Meta: {json.dumps(meta, indent=2)}")
        
        required_meta = ["total_players", "total_unique_lists", "total_games"]
        for field in required_meta:
            if field not in meta:
                print(f"FAILED: Missing meta field '{field}'")
                return False
        
        # Check factions data
        factions = data.get("factions", [])
        if not factions:
            print("FAILED: No factions data returned")
            return False
            
        for f in factions:
            print(f"Faction: {f.get('faction')}")
            # win_rate should be a float/number now, not string "NA" (at least in backend)
            wr = f.get("win_rate")
            print(f"  Win Rate: {wr} (type: {type(wr)})")
            
            # Check for new stats
            players = f.get("players")
            unique_lists = f.get("unique_lists")
            print(f"  Players: {players}, Unique Lists: {unique_lists}")
            
            if players is None or unique_lists is None:
                print(f"FAILED: Missing players or unique_lists in faction {f.get('faction')}")
                return False
                
        print("SUCCESS: /factions endpoint verified")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_squadrons_endpoint():
    print("\nTesting /squadrons endpoint...")
    try:
        # Just check one page
        response = requests.get(f"{BASE_URL}/squadrons?limit=5")
        if response.status_code != 200:
            print(f"FAILED: /squadrons returned {response.status_code}")
            return False
            
        data = response.json()
        lists = data.get("lists", [])
        if not lists:
            print("WARNING: No lists found, but endpoint returned 200")
            return True
            
        for l in lists:
            wr = l.get("win_rate")
            print(f"List: {l.get('signature')[:20]}... Win Rate: {wr} (type: {type(wr)})")
            
        print("SUCCESS: /squadrons endpoint verified")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    b_ok = test_factions_endpoint()
    s_ok = test_squadrons_endpoint()
    
    if b_ok and s_ok:
        print("\nALL VERIFICATIONS PASSED")
        sys.exit(0)
    else:
        print("\nVERIFICATION FAILED")
        sys.exit(1)
