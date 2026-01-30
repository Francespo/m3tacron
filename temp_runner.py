
import os
import sys
import json
from datetime import datetime
sys.path.append(os.getcwd())

os.environ['DB_PATH'] = 'verify_new.db'

from m3tacron.backend.scrapers.longshanks import LongshanksScraper
from m3tacron.backend.scrapers.rollbetter import RollbetterScraper
from sqlmodel import create_engine, SQLModel, Session
from m3tacron.backend.models import Tournament, PlayerResult, Match

# Init DB
sqlite_url = f"sqlite:///{os.environ['DB_PATH']}"
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

urls = ['https://xwing.longshanks.org/event/29346/', 'https://rollbetter.gg/tournaments/2557', 'https://xwing-legacy.longshanks.org/event/28919/']
with Session(engine) as session:
    ls = LongshanksScraper()
    rb = RollbetterScraper()
    for url in urls:
        print(f"--- Processing {url} ---")
        try:
            s = ls if "longshanks" in url else rb
            tid = url.split("/")[-1] if "rollbetter" in url else url.split("event/")[1].split("/")[0]
            t = s.get_tournament_data(tid)
            p = s.get_participants(tid)
            m = s.get_matches(tid)
            save_data(session, t, p, m)
            print(f"Success: {len(p)} players, {len(m)} matches.")
        except Exception as e:
            print(f"FAILED: {e}")
