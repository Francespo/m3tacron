"""
Consolidated Import Script for M3taCron.

Imports data from:
1. RollBetter (JSON API)
2. ListFortress (JSON API)  
3. Longshanks (Playwright Scraper)

Includes duplicate detection and date filtering.
"""
import asyncio
import sys
import os
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, '.')

from sqlmodel import Session, select
from m3tacron.backend.database import engine, create_db_and_tables
from m3tacron.backend.models import Tournament, PlayerResult, MacroFormat, SubFormat

from m3tacron.backend.scrapers.rollbetter import (
    fetch_tournament as fetch_rb_tournament,
    fetch_players as fetch_rb_players,
    extract_xws_from_player as extract_rb_xws
)
from m3tacron.backend.scrapers.listfortress import (
    fetch_tournaments as fetch_lf_tournaments,
    fetch_tournament_details as fetch_lf_details,
    extract_xws_from_participant as extract_lf_xws
)
from m3tacron.backend.scrapers.longshanks import (
    scrape_tournament as scrape_ls_tournament,
    scrape_longshanks_history
)

from m3tacron.backend.format_detector import (
    detect_format_from_tournament_lists,
    detect_format_from_listfortress,
    get_format_display,
)

# Hardcoded fallbacks if search fails or for specific tests
RB_IDS = [2550, 2551, 2554, 2555, 2556, 2557, 2510, 2530, 2502, 2600, 2650]
LF_LIMIT = 8

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
    from difflib import SequenceMatcher
    
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


async def import_rollbetter(session: Session, since_date: datetime, limit: int = 0):
    """Import RollBetter tournaments."""
    print("\n--- Importing RollBetter ---")
    count = 0
    
    # In a real scenario we would search RB api by date, here we iterate known IDs
    for t_id in RB_IDS:
        if limit > 0 and count >= limit:
            break
        print(f"Fetching RB {t_id}...")
        try:
            t_data = await fetch_rb_tournament(t_id)
            if not t_data:
                continue
            
            t_date = datetime.now()
            if t_data.get("startDate"):
                try:
                    t_date = datetime.fromisoformat(t_data["startDate"][:10])
                except:
                    pass
            
            if t_date < since_date:
                print(f"  [Skip] Too old: {t_date.date()}")
                continue
                
            t_name = t_data.get("title") or t_data.get("name", "Unknown")
            
            # Fetch players FIRST to get count for duplicate detection
            players = await fetch_rb_players(t_id)
            if len(players) < 4:
                print(f"  [Skip] Small event: {len(players)}")
                continue
            
            if is_duplicate(session, t_name, t_date, player_count=len(players)):
                print(f"  [Skip] Duplicate: {t_name}")
                continue

            # Format detection
            rb_format_raw = t_data.get("format", "Unknown")
            xws_lists = [extract_rb_xws(p) for p in players if extract_rb_xws(p)]
            
            macro = MacroFormat.OTHER.value
            sub = SubFormat.UNKNOWN.value
            
            if "Legacy 2.0" in rb_format_raw or "2.0" in rb_format_raw:
                macro = MacroFormat.V2_0.value
                m, s = detect_format_from_tournament_lists(xws_lists)
                sub = s if s != SubFormat.UNKNOWN.value else SubFormat.X2PO.value
            elif "Standard" in rb_format_raw or "Extended" in rb_format_raw:
                macro = MacroFormat.V2_5.value
                m, s = detect_format_from_tournament_lists(xws_lists)
                sub = s if s != SubFormat.UNKNOWN.value else SubFormat.AMG.value
                
            display_format = get_format_display(macro, sub)
            
            t = Tournament(
                name=t_name,
                date=t_date,
                platform="RollBetter",
                format=display_format,
                macro_format=macro,
                sub_format=sub,
                url=f"https://rollbetter.gg/tournaments/{t_id}"
            )
            session.add(t)
            session.commit()
            session.refresh(t)
            
            for i, p in enumerate(players):
                p_name = p.get("name") or p.get("displayName") or f"Player {i+1}"
                xws = extract_rb_xws(p)
                
                pr = PlayerResult(
                    tournament_id=t.id,
                    player_name=p_name,
                    rank=p.get("rank") or (i+1),
                    list_json=xws or {},
                    points_at_event=0
                )
                session.add(pr)
            
            session.commit()
            print(f"  [OK] Imported RB: {t_name}")
            count += 1

        except Exception as e:
            print(f"  [X] Error RB {t_id}: {e}")
            
    print(f"Imported {count} RollBetter tournaments.")


async def import_listfortress(session: Session, since_date: datetime, limit: int = 0):
    """Import ListFortress tournaments."""
    # Use effective limit
    effective_limit = limit if limit > 0 else LF_LIMIT
    
    print(f"\n--- Importing ListFortress (limit={effective_limit}) ---")
    tournaments = await fetch_lf_tournaments(limit=effective_limit * 2) # Fetch more to filter by date
    
    count = 0
    for t_summary in tournaments:
        if limit > 0 and count >= limit:
            break
            
        t_id = t_summary.get("id")
        t_name = t_summary.get("name")
        t_date_str = t_summary.get("date", "1900-01-01")
        lf_format = str(t_summary.get("format_id", "0"))
        
        try:
            t_date = datetime.fromisoformat(t_date_str)
        except:
            t_date = datetime.now()
            
        if t_date < since_date:
            continue
        
        # Fetch details FIRST to get participant count for duplicate detection
        try:
            details = await fetch_lf_details(t_id)
        except Exception:
            continue
            
        if not details: continue
            
        participants = details.get("participants", [])
        if len(participants) < 4: continue
        
        # Check duplicates with player count (important for LF which may duplicate RB/LS)
        if is_duplicate(session, t_name, t_date, player_count=len(participants)):
            print(f"  [Skip] Duplicate: {t_name}")
            continue
        
        xws_lists = [extract_lf_xws(p) for p in participants if extract_lf_xws(p)]
        macro, sub = detect_format_from_listfortress(lf_format, t_name, t_date_str, xws_lists)
        display_format = get_format_display(macro, sub)
        
        t = Tournament(
            name=t_name,
            date=t_date,
            platform="ListFortress",
            format=display_format,
            macro_format=macro,
            sub_format=sub,
            url=f"https://listfortress.com/tournaments/{t_id}"
        )
        session.add(t)
        session.commit()
        session.refresh(t)
        
        for p in participants:
            pr = PlayerResult(
                tournament_id=t.id,
                player_name=p.get("name") or "Unknown",
                rank=p.get("rank", 0),
                swiss_rank=p.get("swiss_rank"),
                list_json=extract_lf_xws(p) or {},
                points_at_event=p.get("score", 0)
            )
            session.add(pr)
            
        session.commit()
        print(f"  [OK] Imported LF: {t_name}")
        count += 1
        
    print(f"Imported {count} ListFortress tournaments.")



async def import_longshanks(session: Session, since_date: datetime, limit: int = 0):
    """Import Longshanks tournaments using history page scraping."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return

    print("\n--- Importing Longshanks ---")
    
    # Target specific subdomains as requested
    urls = [
        "https://xwing.longshanks.org/events/history/",
        "https://xwing-legacy.longshanks.org/events/history/"
    ]
    
    print("Scraping Longshanks history pages...")
    found_tournaments = await scrape_longshanks_history(urls)
    print(f"Found {len(found_tournaments)} potential tournaments.")
    
    count = 0
    
    # Use one browser instance for all details
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            for t_info in found_tournaments:
                if limit > 0 and count >= limit:
                    break
                
                eid = t_info["id"]
                t_name = t_info["name"]
                t_date = t_info["date"]
                
                # Date filter
                if t_date < since_date:
                    continue
                
                # Get player count from scrape info (if available) for early duplicate check
                player_count = t_info.get("player_count", 0)
                if player_count > 0 and is_duplicate(session, t_name, t_date, player_count=player_count):
                    print(f"  [Skip] Duplicate: {t_name}")
                    continue
                
                # Create Tournament with trusted metadata
                fmt = t_info.get("format", "Standard")
                if fmt == "Legacy":
                    macro = MacroFormat.V2_0.value
                    sub = SubFormat.X2PO.value
                    display = "2.0 Legacy"
                else:
                    macro = MacroFormat.V2_5.value
                    sub = SubFormat.AMG.value
                    display = "2.5 Standard"
                    
                print(f"  Processing {t_name} ({t_date.date()})...")
                
                try:
                    # Scrape details for players - REUSING BROWSER
                    result = await scrape_ls_tournament(eid, browser=browser)
                    
                    # If detail scrape fails, we skip (need players)
                    if not result:
                        print(f"    [X] Failed to get details for {eid}")
                        continue
                        
                    players = result.get("players", [])
                    
                    if len(players) < 4:
                        print(f"    [Skip] Small event: {len(players)})")
                        continue

                    t = Tournament(
                        name=t_name,
                        date=t_date,
                         platform="Longshanks",
                        format=display,
                        macro_format=macro,
                        sub_format=sub,
                        url=t_info.get("url")
                    )
                    session.add(t)
                    session.commit()
                    session.refresh(t)
                    
                    for p in players:
                        # Basic mock XWS for now as LS doesn't expose full XWS easily without JSON export
                        mock_xws = {}
                        if p.get("faction"):
                            mock_xws["faction"] = p.get("faction")
                        
                        pr = PlayerResult(
                            tournament_id=t.id,
                            player_name=p.get("name") or "Unknown",
                            rank=p.get("rank"),
                            list_json=mock_xws,
                            points_at_event=0
                        )
                        session.add(pr)
                        
                    session.commit()
                    print(f"    [OK] Imported LS: {t.name} - {len(players)} players")
                    count += 1
                    
                except Exception as e:
                    print(f"Failed to import LS {eid}: {e}")
        finally:
            await browser.close()
            
    print(f"Imported {count} Longshanks tournaments.")


def parse_args():
    parser = argparse.ArgumentParser(description="M3taCron Data Import")
    parser.add_argument("--days", type=int, default=30, help="Import tournaments from last N days (default: 30)")
    parser.add_argument("--clean", action="store_true", help="Clear database before importing")
    parser.add_argument("--all", action="store_true", help="Ignore date limit (import everything found)")
    parser.add_argument("--limit", type=int, default=0, help="Max number of tournaments to import per source (0 = no limit)")
    return parser.parse_args()


async def main():
    args = parse_args()
    
    # Calculate cutoff date
    if args.all:
        cutoff_date = datetime(2000, 1, 1)
        limit_txt = "ALL TIME"
    else:
        cutoff_date = datetime.now() - timedelta(days=args.days)
        limit_txt = f"Last {args.days} days ({cutoff_date.date()})"
    
    print("=" * 60)
    print(f"M3taCron - Data Import")
    print(f"Range: {limit_txt}")
    if args.limit > 0:
        print(f"Limit: {args.limit} tournaments per source")
    print("=" * 60)
    
    if args.clean:
        print("Cleaning database...")
        db_file = "metacron.db"
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except PermissionError:
                print("Warning: Could not delete database (locked). Using existing DB.")
            
    create_db_and_tables()
    
    with Session(engine) as session:
        await import_rollbetter(session, cutoff_date, limit=args.limit)
        await import_longshanks(session, cutoff_date, limit=args.limit)
        await import_listfortress(session, cutoff_date, limit=args.limit)
    
    print("\n" + "=" * 60)
    print("Import complete!")


if __name__ == "__main__":
    asyncio.run(main())
