"""
Script to populate the database with a mix of tournaments from different providers.
Includes game format inference verification.
"""
import sys
import os
import asyncio
from sqlmodel import Session, select
from difflib import SequenceMatcher

from datetime import datetime, timedelta
from collections import Counter

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from m3tacron.backend.database import engine, create_db_and_tables
from m3tacron.backend.models import Tournament, PlayerResult, GameFormat
from m3tacron.backend.inference import infer_format_from_xws

# Import Scrapers via package exports
from m3tacron.backend.scrapers import (
    ls_scrape_history, ls_scrape_tournament,
    rb_scrape_tournament,
    lf_fetch_tournaments, lf_fetch_tournament_details, extract_xws_from_participant
)


def is_duplicate(session: Session, name: str, date: datetime, player_count: int = 0, tolerance_days: int = 3) -> bool:
    """Check if tournament with similar name, date, and player count already exists.
    
    Args:
        session: Database session
        name: Tournament name to check
        date: Tournament date
        player_count: Number of participants (if 0, skip this check)
        tolerance_days: Date range tolerance (default ±3 days)
    
    Returns:
        True if a duplicate is found
    """
    start_date = date - timedelta(days=tolerance_days)
    end_date = date + timedelta(days=tolerance_days)
    
    existing = session.exec(
        select(Tournament).where(
            Tournament.date >= start_date,
            Tournament.date <= end_date
        )
    ).all()
    
    name_lower = name.lower().strip()
    for t in existing:
        existing_name = t.name.lower().strip()
        
        # Check name similarity
        is_name_match = False
        if name_lower == existing_name:
            is_name_match = True
        else:
            similarity = SequenceMatcher(None, name_lower, existing_name).ratio()
            if similarity > 0.8:
                is_name_match = True
        
        if not is_name_match:
            continue
        
        # If player_count provided, also check if counts are similar (±20%)
        if player_count > 0 and t.player_count > 0:
            tolerance = 0.2
            min_count = int(player_count * (1 - tolerance))
            max_count = int(player_count * (1 + tolerance))
            if min_count <= t.player_count <= max_count:
                print(f"    [Duplicate] '{name}' matches '{t.name}' (players: {player_count}~{t.player_count})")
                return True
        else:
            # No player count to compare, name+date match is enough
            print(f"    [Duplicate] '{name}' matches '{t.name}' (name+date)")
            return True
    
    return False


async def process_tournament(data: dict[str, any], session: Session) -> bool:
    """
    Process a scraped tournament dictionary and save to DB.
    Returns True if saved, False if skipped/error.
    """
    t_info = data.get("tournament", {})
    if not t_info:
        return False
        
    t_name = t_info.get("name")
    t_url = t_info.get("url")
    t_date = t_info.get("date")
    t_platform = t_info.get("platform")
    players = data.get("players", [])
    player_count = len(players)
    
    # Check identifying info
    if not t_name or not t_url:
        print(f"Skipping incomplete data: {t_name}")
        return False
    
    # Check for URL duplicate first (exact match)
    existing = session.exec(select(Tournament).where(Tournament.url == t_url)).first()
    if existing:
        print(f"Skipping existing URL: {t_name}")
        return False
    
    # Check for name/date/player duplicate (fuzzy match)
    if t_date and is_duplicate(session, t_name, t_date, player_count=player_count):
        print(f"Skipping duplicate: {t_name}")
        return False

    print(f"Processing: {t_name} ({t_platform})...")
    
    # Process Players & Infer Formats (already extracted at top)
    player_formats = []
    
    player_data_list = []
    
    for p in players:
        xws = p.get("xws")
        fmt = GameFormat.OTHER.value
        if xws:
            fmt = infer_format_from_xws(xws)
            player_formats.append(fmt)
            
        points = 0
        if xws and "points" in xws:
            try:
                points = int(xws["points"])
            except:
                pass
        
        # Store data to create objects later
        player_data_list.append({
            "player_name": p.get("name", "Unknown"),
            "rank": p.get("rank", 0),
            "swiss_rank": p.get("swiss_rank"),
            "list_json": xws or {},
            "points_at_event": points
        })
        
    # Determine Tournament Majority Format
    t_format = GameFormat.OTHER.value
    if player_formats:
        counts = Counter(player_formats)
        most_common = counts.most_common(1)[0]
        # Only assign if it's a significant majority or specifically identified
        t_format = most_common[0]
        print(f"   Detected Format: {t_format} (votes: {counts})")
    
    # Use player_count from scraper if available (e.g. Longshanks Event size header)
    # Otherwise fallback to counting extracted players
    scraped_player_count = t_info.get("player_count", 0)
    actual_player_count = scraped_player_count if scraped_player_count > 0 else len(player_data_list)
    
    # Create Tournament
    db_t = Tournament(
        name=t_name,
        date=t_date if isinstance(t_date, datetime) else datetime.now(),
        platform=t_platform,
        url=t_url,
        format=t_format,
        player_count=actual_player_count
    )
    
    session.add(db_t)
    session.commit()
    session.refresh(db_t)
    
    # Save Players
    db_players = []
    for p_data in player_data_list:
        db_p = PlayerResult(
            tournament_id=db_t.id,
            **p_data
        )
        session.add(db_p)
        db_players.append(db_p)
        
    session.commit()
    print(f"   Saved {len(db_players)} players.")
    return True

async def main():
    print("Initializing Database...")
    create_db_and_tables()
    
    imported_count = 0
    
    with Session(engine) as session:
        # 1. Rollbetter (Specific Verification ID) - PRIORITY SOURCE
        print("\n--- Scraping Rollbetter ---")
        rb_ids = [2474] 
        for rid in rb_ids:
            try:
                # Assuming browser scraping for full XWS
                print(f"Scraping Rollbetter #{rid}...")
                data = await rb_scrape_tournament(rid)
                if data:
                    if await process_tournament(data, session):
                        imported_count += 1
            except Exception as e:
                print(f"Error Rollbetter {rid}: {e}")

        # 2. ListFortress - PRIORITY SOURCE (imported before Longshanks)
        print("\n--- Fetching ListFortress ---")
        try:
            lf_tourneys = await lf_fetch_tournaments(limit=5)
            for t in lf_tourneys:
                tid = t["id"]
                try:
                    print(f"Fetching LF #{tid}...")
                    details = await lf_fetch_tournament_details(tid)
                    if not details:
                        continue
                        
                    # Convert LF format to our structure
                    pf_players = []
                    for p in details.get("participants", []):
                        xws = extract_xws_from_participant(p)
                        pf_players.append({
                            "name": p.get("name"),
                            "rank": p.get("rank"),
                            "swiss_rank": p.get("swiss_rank"),
                            "xws": xws
                        })
                        
                    # Standardize Date
                    d_str = t.get("date")
                    try:
                        t_date = datetime.fromisoformat(d_str) if d_str else datetime.now() 
                    except:
                        t_date = datetime.now()

                    data = {
                        "tournament": {
                            "name": t.get("name"),
                            "date": t_date,
                            "platform": "ListFortress",
                            "url": f"https://listfortress.com/tournaments/{tid}"
                        },
                        "players": pf_players
                    }
                    
                    if await process_tournament(data, session):
                        imported_count += 1
                        
                except Exception as e:
                    print(f"Error LF {tid}: {e}")
        except Exception as e:
            print(f"Error fetching LF list: {e}")

        # 3. Longshanks (History) - Last priority, may have duplicates in LF/RB
        print("\n--- Scraping Longshanks ---")
        # 2.5 Standard
        try:
            ls_events = await ls_scrape_history("xwing", max_pages=1)
            # Take top 5
            for event in ls_events[:5]:
                eid = event["id"]
                try:
                    data = await ls_scrape_tournament(eid, "xwing")
                    if data:
                        if await process_tournament(data, session):
                            imported_count += 1
                except Exception as e:
                    print(f"Error LS {eid}: {e}")
        except Exception as e:
            print(f"Error LS History: {e}")

        # 2.0 Legacy
        try:
            ls_events_legacy = await ls_scrape_history("xwing-legacy", max_pages=1)
            # Take top 5
            for event in ls_events_legacy[:5]:
                eid = event["id"]
                try:
                    data = await ls_scrape_tournament(eid, "xwing-legacy")
                    if data:
                        if await process_tournament(data, session):
                            imported_count += 1
                except Exception as e:
                    print(f"Error LS Legacy {eid}: {e}")
        except Exception as e:
            print(f"Error LS Legacy History: {e}")


    print(f"\nCompleted! Total tournaments imported: {imported_count}")

if __name__ == "__main__":
    asyncio.run(main())
