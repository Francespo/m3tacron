import sys
import os

# Ensure we can import m3tacron
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlmodel import Session, select, func
from m3tacron.database import engine
from m3tacron.backend.models import Tournament

def check_formats():
    print(f"Connecting to DB with engine: {engine.url}")
    try:
        with Session(engine) as session:
            # Get count of tournaments by format
            statement = select(Tournament.format, func.count(Tournament.id)).group_by(Tournament.format)
            results = session.exec(statement).all()
            
            print("\nTournament Formats in DB:")
            if not results:
                print("No tournaments found.")
            for fmt, count in results:
                # fmt is the value in the column
                print(f"Format: '{fmt}' (Type: {type(fmt)}) - Count: {count}")
                
    except Exception as e:
        print(f"Error accessing DB: {e}")

if __name__ == "__main__":
    check_formats()
