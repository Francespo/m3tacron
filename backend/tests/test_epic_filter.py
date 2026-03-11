import pytest
from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_epic_filter_pilots():
    # 1. Default (epic should be excluded if include_epic=false)
    response = client.get("/api/cards/pilots?include_epic=false&size=100")
    assert response.status_code == 200
    data = response.json()
    items = data.get("items", [])
    
    epic_xws = {'raiderclasscorvette', 'cr90corelliancorvette', 'gozanticlasscruiser', 
                'gr75mediumtransport', 'cthc620cclasscorvette', 'croccruiser', 'tridentclassassaultship'}
    
    for item in items:
        assert item['xws'] not in epic_xws, f"Epic pilot {item['xws']} found when filtered out"

def test_epic_filter_upgrades():
    response = client.get("/api/cards/upgrades?include_epic=false&size=100")
    assert response.status_code == 200
    data = response.json()
    items = data.get("items", [])
    
    epic_types = {'huge ship turret', 'command', 'hardpoint', 'team', 'cargo'}
    
    for item in items:
        assert item['type'].lower() not in epic_types, f"Epic upgrade type {item['type']} found when filtered out"

def test_epic_filter_ships():
    response = client.get("/api/ships?include_epic=false&size=100")
    assert response.status_code == 200
    data = response.json()
    items = data.get("items", [])
    
    epic_ships = {'raider-class corvette', 'cr90 corellian corvette', 'gozanticlass cruiser', 
                  'gr-75 medium transport', 'cthc-620c-class corvette', 'c-roc cruiser', 'trident-class assault ship'}
    
    for item in items:
        assert item['ship_name'].lower() not in epic_ships, f"Epic ship {item['ship_name']} found when filtered out"

def test_meta_snapshot_epic():
    response = client.get("/api/meta-snapshot?include_epic=false")
    assert response.status_code == 200
    data = response.json()
    
    # Check pilots in meta sample
    # Check pilots in meta sample
    epic_xws = {'raiderclasscorvette', 'cr90corelliancorvette', 'gozanticlasscruiser', 
                'gr75mediumtransport', 'cthc620cclasscorvette', 'croccruiser', 'tridentclassassaultship'}
    for p in data.get("pilots", []):
        assert p['xws'] not in epic_xws, f"Epic pilot {p['xws']} found in meta snapshot"
        
    # Check upgrades in meta sample
    epic_types = {'huge ship turret', 'command', 'hardpoint', 'team', 'cargo'}
    for u in data.get("upgrades", []):
        assert u['type'].lower() not in epic_types, f"Epic upgrade type {u['type']} found in meta snapshot"
