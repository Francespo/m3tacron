from sqlmodel import Session, select
from database import engine
from models import PlayerResult, Tournament
from api.lists import get_lists

def test_lists():
    res = get_lists(page=0, size=1, data_source="xwa", factions=None, formats=None, points_min=0, points_max=200, min_games=0, loadout_min=0, loadout_max=50, sort_metric="Games", sort_direction="desc")
    if res.items:
        for p in res.items[0].pilots:
            print(p.name, p.ship_icon, p.ship_name)

if __name__ == "__main__":
    test_lists()
