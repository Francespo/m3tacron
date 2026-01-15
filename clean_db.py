from sqlmodel import Session, select
from m3tacron.backend.database import engine
from m3tacron.backend.models import Tournament

def clean():
    bad_keywords = ['40k', 'shatterpoint', 'legion', 'armada', 'marvel']
    with Session(engine) as session:
        tournaments = session.exec(select(Tournament)).all()
        count = 0
        for t in tournaments:
            name = t.name.lower()
            if any(k in name for k in bad_keywords):
                print(f"Deleting: {t.name}")
                session.delete(t)
                count += 1
        session.commit()
        print(f"Removed {count} invalid tournaments.")

if __name__ == "__main__":
    clean()
