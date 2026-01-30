
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime

# Configuration
DB_OLD = "verify_old.db"
DB_NEW = "verify_new.db"

SCRAPERS_DIR = "m3tacron/backend/scrapers"
LONGSHANKS_PY = os.path.join(os.getcwd(), SCRAPERS_DIR, "longshanks.py")
ROLLBETTER_PY = os.path.join(os.getcwd(), SCRAPERS_DIR, "rollbetter.py")

LONGSHANKS_OLD = os.path.join(os.getcwd(), SCRAPERS_DIR, "longshanks_old.py")
LONGSHANKS_NEW_BAK = os.path.join(os.getcwd(), SCRAPERS_DIR, "longshanks_new.py.bak")

ROLLBETTER_OLD = os.path.join(os.getcwd(), SCRAPERS_DIR, "rollbetter_old.py")
ROLLBETTER_NEW_BAK = os.path.join(os.getcwd(), SCRAPERS_DIR, "rollbetter_new.py.bak")

# Events to Test
URLS = [
    "https://xwing.longshanks.org/event/29346/",
    "https://rollbetter.gg/tournaments/2557",
    "https://xwing-legacy.longshanks.org/event/28919/"
]

def backup_current_scrapers():
    print(">>> Backing up CURRENT (New) scrapers...")
    if os.path.exists(LONGSHANKS_PY):
        shutil.copy(LONGSHANKS_PY, LONGSHANKS_NEW_BAK)
    if os.path.exists(ROLLBETTER_PY):
        shutil.copy(ROLLBETTER_PY, ROLLBETTER_NEW_BAK)

def restore_scrapers():
    print(">>> Restoring CURRENT (New) scrapers...")
    if os.path.exists(LONGSHANKS_NEW_BAK):
        shutil.copy(LONGSHANKS_NEW_BAK, LONGSHANKS_PY)
    if os.path.exists(ROLLBETTER_NEW_BAK):
        shutil.copy(ROLLBETTER_NEW_BAK, ROLLBETTER_PY)

def install_old_scrapers():
    print(">>> Installing OLD scrapers...")
    if os.path.exists(LONGSHANKS_OLD):
        shutil.copy(LONGSHANKS_OLD, LONGSHANKS_PY)
    if os.path.exists(ROLLBETTER_OLD):
        shutil.copy(ROLLBETTER_OLD, ROLLBETTER_PY)

def run_scrape(db_name):
    print(f"\n>>> Running Scrape for {db_name}...")
    
    runner_code = f"""
import os
import sys
import json
from datetime import datetime
sys.path.append(os.getcwd())

os.environ['DB_PATH'] = '{db_name}'

from m3tacron.backend.scrapers.longshanks import LongshanksScraper
from m3tacron.backend.scrapers.rollbetter import RollbetterScraper
from sqlmodel import create_engine, SQLModel, Session
from m3tacron.backend.models import Tournament, PlayerResult, Match

# Init DB
sqlite_url = f"sqlite:///{{os.environ['DB_PATH']}}"
engine = create_engine(sqlite_url)
SQLModel.metadata.create_all(engine)

def save_data(session, t, players, matches):
    if not t.name: t.name = "Unknown Event"
    if not t.date: t.date = datetime.now().date()
    session.merge(t)
    session.commit()
    t_id = t.id 
    
    for p in players:
        p.tournament_id = t_id
        session.merge(p)
    session.commit()
        
    for m_data in matches:
        if isinstance(m_data, dict):
            m = Match(
                tournament_id=t_id,
                round_number=m_data.get("round_number", 1),
                round_type=m_data.get("round_type", "Swiss"),
                player1_score=m_data.get("player1_score", 0),
                player2_score=m_data.get("player2_score", 0),
                p1_name_temp=m_data.get("p1_name_temp"),
                p2_name_temp=m_data.get("p2_name_temp"),
                winner_name_temp=m_data.get("winner_name_temp"),
                is_bye=m_data.get("is_bye", False),
                scenario=m_data.get("scenario")
            )
            session.add(m)
        else:
            m_data.tournament_id = t_id
            session.add(m_data)
    session.commit()

urls = {URLS}
with Session(engine) as session:
    ls = LongshanksScraper()
    rb = RollbetterScraper()
    for url in urls:
        print(f"--- Processing {{url}} ---")
        try:
            s = ls if "longshanks" in url else rb
            tid = url.split("/")[-1] if "rollbetter" in url else url.split("event/")[1].split("/")[0]
            t = s.get_tournament_data(tid)
            p = s.get_participants(tid)
            m = s.get_matches(tid)
            save_data(session, t, p, m)
            print(f"Success: {{len(p)}} players, {{len(m)}} matches.")
        except Exception as e:
            print(f"FAILED: {{e}}")
"""
    with open("temp_runner.py", "w") as f:
        f.write(runner_code)
    subprocess.run([sys.executable, "temp_runner.py"], check=False)

def compare_dbs():
    print("\n>>> COMPARING DATABASES <<<")
    
    def get_counts(db):
        if not os.path.exists(db): return 0,0,0
        con = sqlite3.connect(db)
        try:
            t = con.execute("SELECT count(*) FROM tournament").fetchone()[0]
            p = con.execute("SELECT count(*) FROM playerresult").fetchone()[0]
            m = con.execute("SELECT count(*) FROM match").fetchone()[0]
            return t, p, m
        except: return 0,0,0
        finally: con.close()

    t_old, p_old, m_old = get_counts(DB_OLD)
    t_new, p_new, m_new = get_counts(DB_NEW)
    
    print(f"METRIC      | OLD DB | NEW DB")
    print("-" * 30)
    print(f"Tournaments | {t_old:<6} | {t_new}")
    print(f"Players     | {p_old:<6} | {p_new}")
    print(f"Matches     | {m_old:<6} | {m_new}")
    print("-" * 30)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", choices=["old", "new", "compare", "full"], required=True)
    args = parser.parse_args()

    if args.step in ["old", "full"]:
        if os.path.exists(DB_OLD): os.remove(DB_OLD)
        backup_current_scrapers()
        install_old_scrapers()
        run_scrape(DB_OLD)
        
    if args.step in ["new", "full"]:
        if os.path.exists(DB_NEW): os.remove(DB_NEW)
        restore_scrapers()
        run_scrape(DB_NEW)
        
    if args.step in ["compare", "full"]:
        restore_scrapers() 
        compare_dbs()

if __name__ == "__main__":
    main()
