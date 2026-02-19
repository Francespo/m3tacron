from m3tacron.backend.database import engine
from m3tacron.backend.models import Tournament
from sqlmodel import Session, select, func

def check_dates():
    with Session(engine) as session:
        max_date = session.exec(select(func.max(Tournament.date))).one()
        count = session.exec(select(func.count(Tournament.id))).one()
        print(f"Max Tournament Date: {max_date}")
        print(f"Total Tournaments: {count}")
        
        from datetime import datetime, timedelta
        now = datetime.now()
        start_90 = now - timedelta(days=90)
        recent_count = session.exec(select(func.count(Tournament.id)).where(Tournament.date >= start_90)).one()
        print(f"Tournaments since {start_90.date()}: {recent_count}")

if __name__ == "__main__":
    check_dates()
