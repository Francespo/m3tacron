"""Test and import from Longshanks."""
import asyncio
import sys
sys.path.insert(0, '.')

from datetime import datetime
from sqlmodel import Session, select
from m3tacron.backend.database import engine, create_db_and_tables
from m3tacron.backend.models import Tournament, PlayerResult
from m3tacron.backend.scrapers.longshanks import scrape_tournament


async def test_and_import_longshanks():
    print("=" * 60)
    print("Testing Longshanks Scraper")
    print("=" * 60)
    
    # Test with known X-Wing tournament from DOM analysis
    event_id = 30874  # Xhammer X-Wing X-mas Tournament 2025
    
    print(f"\n1. Scraping event {event_id}...")
    result = await scrape_tournament(event_id)
    
    if not result:
        print("   ✗ Failed to scrape tournament")
        return
    
    tournament = result.get("tournament", {})
    players = result.get("players", [])
    
    print(f"   ✓ Tournament: {tournament.get('name')}")
    print(f"   ✓ Players found: {len(players)}")
    
    if players:
        print("\n   Top players:")
        for p in players[:5]:
            faction = p.get('faction', 'Unknown')
            print(f"   - #{p['rank']} {p['name']} ({faction})")
    
    # Import to database
    if len(players) >= 4:
        print("\n2. Importing to database...")
        create_db_and_tables()
        
        with Session(engine) as session:
            # Check if exists
            existing = session.exec(
                select(Tournament).where(Tournament.url.contains(str(event_id)))
            ).first()
            
            if existing:
                print(f"   → Already exists: {existing.name}")
            else:
                # Create tournament
                t = Tournament(
                    name=tournament.get("name", f"Event {event_id}"),
                    date=tournament.get("date", datetime.now()),
                    platform="Longshanks",
                    format="Standard",
                    url=tournament.get("url", f"https://longshanks.org/event/{event_id}/"),
                )
                session.add(t)
                session.commit()
                session.refresh(t)
                print(f"   ✓ Created: {t.name}")
                
                # Import players
                for p in players:
                    pr = PlayerResult(
                        tournament_id=t.id,
                        player_name=p.get("name", "Unknown"),
                        rank=p.get("rank", 999),
                        list_json={"faction": p.get("faction")} if p.get("faction") else {},
                        points_at_event=200,
                    )
                    session.add(pr)
                
                session.commit()
                print(f"   ✓ Imported {len(players)} players")
    
    print("\n" + "=" * 60)
    print("Longshanks test complete!")


if __name__ == "__main__":
    asyncio.run(test_and_import_longshanks())
