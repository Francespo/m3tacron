import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Backend is running"}

def test_meta_snapshot():
    response = client.get("/api/meta-snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "factions" in data
    assert "ships" in data
    assert "lists" in data
    assert "pilots" in data
    assert "upgrades" in data
    assert "total_tournaments" in data
    # Ensure lists structure is somewhat valid
    if len(data["lists"]) > 0:
        lst = data["lists"][0]
        assert "signature" in lst
        assert "faction" in lst
        assert "win_rate" in lst

def test_tournaments():
    response = client.get("/api/tournaments?size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data

    if len(data["items"]) > 0:
        t = data["items"][0]
        assert "name" in t
        assert "date" in t
        assert "format_label" in t

def test_tournaments_with_search():
    response = client.get("/api/tournaments?search=Test")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data

def test_lists():
    response = client.get("/api/lists?size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    
    if len(data["items"]) > 0:
        l = data["items"][0]
        assert "faction" in l
        assert "win_rate" in l

def test_pilots():
    response = client.get("/api/cards/pilots?size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

    if len(data["items"]) > 0:
        p = data["items"][0]
        assert "name" in p
        assert "popularity" in p

def test_upgrades():
    response = client.get("/api/cards/upgrades?size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

    if len(data["items"]) > 0:
        u = data["items"][0]
        assert "name" in u
        assert "type" in u

def test_ships():
    response = client.get("/api/ships?size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

    if len(data["items"]) > 0:
        s = data["items"][0]
        assert "ship_name" in s
        assert "faction_xws" in s
