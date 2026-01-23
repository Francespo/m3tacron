
import os
from sqlmodel import create_engine, Session, select, func
from m3tacron.backend.models import Tournament, PlayerResult, Match
import json

dbs = {
    "RollBetter V1": "rb_v1.db",
    "RollBetter V2": "rb_v2.db",
    "Longshanks V1": "ls_v1.db",
    "Longshanks V2": "ls_v2.db"
}


def analyze_db(name, path, f):
    f.write(f"\n=== {name} ({path}) ===\n")
    if not os.path.exists(path):
        f.write("Database file not found.\n")
        return

    try:
        engine = create_engine(f"sqlite:///{path}")
        with Session(engine) as session:
            tournaments = session.exec(select(Tournament)).all()
            f.write(f"Tournaments Found: {len(tournaments)}\n")
            
            for t in tournaments:
                player_count = session.exec(select(func.count(PlayerResult.id)).where(PlayerResult.tournament_id == t.id)).one()
                match_count = session.exec(select(func.count(Match.id)).where(Match.tournament_id == t.id)).one()
                
                players = session.exec(select(PlayerResult).where(PlayerResult.tournament_id == t.id)).all()
                # Legacy check removed

                
                # Fix list count logic properly
                lists_count = 0
                for p in players:
                    if p.list_json and isinstance(p.list_json, dict) and len(p.list_json) > 0:
                        lists_count += 1

                f.write(f"  ID {t.id}: {t.name}\n")
                f.write(f"    Location: {t.location} \n")
                f.write(f"    Players: {player_count} (With Lists: {lists_count})\n")
                f.write(f"    Matches: {match_count}\n")
                
    except Exception as e:
        f.write(f"Error reading {name}: {e}\n")

if __name__ == "__main__":
    with open("results_summary.txt", "w", encoding="utf-8") as f:
        for name, path in dbs.items():
            analyze_db(name, path, f)

