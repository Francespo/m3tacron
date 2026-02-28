from fastapi.testclient import TestClient
from backend.main import app
import json

client = TestClient(app)

print("Fetching /api/meta-snapshot...")
response = client.get("/api/meta-snapshot")

if response.status_code == 200:
    data = response.json()
    print("SUCCESS: 200 OK")
    print("-" * 40)
    print(f"Date Range: {data.get('date_range')}")
    print(f"Total Tournaments: {data.get('total_tournaments')}")
    print(f"Total Players: {data.get('total_players')}")
    if data.get('factions'):
        print(f"Top Faction: {data['factions'][0]['name']} (WR: {data['factions'][0]['win_rate']}%, Pop: {data['factions'][0]['popularity']})")
    
    # Save full JSON to check
    with open("test_response.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Full JSON saved to test_response.json")
else:
    print(f"FAILED: {response.status_code}")
    print(response.text)
