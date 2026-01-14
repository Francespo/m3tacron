"""Test and import from ListFortress API."""
import asyncio
import sys
sys.path.insert(0, '.')

from datetime import datetime
from sqlmodel import Session, select
from m3tacron.backend.database import engine, create_db_and_tables
from m3tacron.backend.models import Tournament, PlayerResult
from m3tacron.backend.scrapers.listfortress import (
    fetch_tournaments,
    fetch_tournament_details,
    extract_xws_from_participant,
)


async def test_listfortress():
    print("=" * 60)
    print("Testing ListFortress API")
    print("=" * 60)
    
    # Test 1: Fetch recent tournaments
    print("\n1. Fetching recent tournaments...")
    try:
        tournaments = await fetch_tournaments(limit=20)
        print(f"   ✓ Found {len(tournaments)} tournaments")
        
        for t in tournaments[:5]:
            print(f"   - {t.get('name', 'Unknown')} ({t.get('date', 'N/A')})")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Test 2: Fetch tournament with participants
    print("\n2. Fetching tournament with participants...")
    test_id = tournaments[0].get("id")
    details = await fetch_tournament_details(test_id)
    if details:
        participants = details.get("participants", [])
        print(f"   ✓ Tournament: {details.get('name')} - {len(participants)} participants")
        with_xws = sum(1 for p in participants if p.get("list_json"))
        print(f"   ✓ With XWS data: {with_xws}/{len(participants)}")
    
    print("\n" + "=" * 60)
    print("ListFortress API test complete!")


async def import_listfortress_tournaments():
    """Import tournaments from ListFortress that have 8+ participants."""
    print("\n" + "=" * 60)
    print("Importing ListFortress Tournaments")
    print("=" * 60)
    
    create_db_and_tables()
    
    # Fetch all available tournaments
    tournaments = await fetch_tournaments(limit=100)
    print(f"Checking {len(tournaments)} tournaments for data...")
    
    imported = 0
    with Session(engine) as session:
        for t_data in tournaments:
            if imported >= 3:  # Limit to 3 new imports
                break
                
            t_id = t_data.get("id")
            t_name = t_data.get("name", f"Tournament {t_id}")
            
            # Skip if already exists
            existing = session.exec(
                select(Tournament).where(Tournament.url.contains(str(t_id)))
            ).first()
            if existing:
                continue
            
            # Fetch details  
            details = await fetch_tournament_details(t_id)
            if not details:
                continue
            
            participants = details.get("participants", [])
            if len(participants) < 8:  # Need at least 8 players
                continue
            
            # Parse date
            date_str = t_data.get("date", "")
            try:
                date = datetime.fromisoformat(date_str) if date_str else datetime.now()
            except:
                date = datetime.now()
            
            # Create tournament
            tournament = Tournament(
                name=t_name,
                date=date,
                platform="ListFortress",
                format=t_data.get("format", "Standard"),
                url=f"https://listfortress.com/tournaments/{t_id}",
            )
            session.add(tournament)
            session.commit()
            session.refresh(tournament)
            print(f"   ✓ {tournament.name} ({len(participants)} players)")
            
            # Import participants
            for p in participants:
                xws = extract_xws_from_participant(p)
                player = PlayerResult(
                    tournament_id=tournament.id,
                    player_name=p.get("player_name") or p.get("name") or "Unknown",
                    rank=p.get("swiss_rank") or p.get("rank") or 999,
                    list_json=xws if xws else {},
                    points_at_event=200,
                )
                session.add(player)
            
            session.commit()
            imported += 1
    
    print(f"\nImported {imported} tournaments from ListFortress")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_listfortress())
    asyncio.run(import_listfortress_tournaments())
