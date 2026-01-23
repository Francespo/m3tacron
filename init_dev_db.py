from sqlmodel import Session, select, create_engine
from m3tacron.backend.models import Tournament, PlayerResult, Match, Format, Platform, RoundType, Scenario, Location
from m3tacron.backend.database import create_db_and_tables, engine
from datetime import date
import os

# Delete existing dev.db if it exists to ensure clean schema
if os.path.exists("dev.db"):
    os.remove("dev.db")

# Force engine to dev.db for this script independently of database.py
# (We will update database.py separately, but this ensures script works standalone)
DEV_DB_URL = "sqlite:///dev_v2.db"
engine = create_engine(DEV_DB_URL)

def create_dev_tables():
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

def seed_dummy_data():
    create_dev_tables()
    
    with Session(engine) as session:
        # Tournament 1: Local Event
        t1 = Tournament(
            name="Metropolis Local Open",
            date=date.today(),
            location=Location(city="Metropolis", country="USA"),
            player_count=4,
            url="http://example.com/t1",
            platform=Platform.LONGSHANKS,
            format=Format.XWA
        )
        session.add(t1)
        session.commit()
        session.refresh(t1)

        # Players T1
        p1 = PlayerResult(tournament_id=t1.id, player_name="Luke Skywalker", rank=1, swiss_wins=3, list_json={"faction": "rebelalliance"})
        p2 = PlayerResult(tournament_id=t1.id, player_name="Darth Vader", rank=2, swiss_wins=2, list_json={"faction": "galacticempire"})
        p3 = PlayerResult(tournament_id=t1.id, player_name="Boba Fett", rank=3, swiss_wins=1, list_json={"faction": "scumandvillainy"})
        p4 = PlayerResult(tournament_id=t1.id, player_name="Grievous", rank=4, swiss_wins=0, list_json={"faction": "separatistalliance"})
        
        session.add_all([p1, p2, p3, p4])
        session.commit()
        session.refresh(p1); session.refresh(p2); session.refresh(p3); session.refresh(p4)

        # Matches T1
        m1 = Match(
            tournament_id=t1.id, round_number=1, round_type=RoundType.SWISS, scenario=Scenario.ASSAULT_AT_THE_SATELLITE_ARRAY,
            player1_id=p1.id, player2_id=p2.id, player1_score=20, player2_score=15, winner_id=p1.id, first_player_id=p1.id
        )
        m2 = Match(
            tournament_id=t1.id, round_number=1, round_type=RoundType.SWISS, scenario=Scenario.CHANCE_ENGAGEMENT,
            player1_id=p3.id, player2_id=p4.id, player1_score=18, player2_score=5, winner_id=p3.id, first_player_id=p4.id
        )
        session.add_all([m1, m2])
        session.commit()

        # Tournament 2: World Championship
        t2 = Tournament(
            name="Galactic Championship",
            date=date.today(),
            location=Location(city="Coruscant", country="Galactic Core"),
            player_count=8,
            url="http://example.com/t2",
            platform=Platform.LONGSHANKS, # Using generic unknown type if Gemini not in Enum, checking Enum... Assuming REAL_LIFE or other valid
            format=Format.XWA
        )
        # Fix platform if Gemini not exists
        t2.platform = Platform.LONGSHANKS
        
        session.add(t2)
        session.commit()
        print("Seeded 2 tournaments into dev.db")

if __name__ == "__main__":
    seed_dummy_data()
