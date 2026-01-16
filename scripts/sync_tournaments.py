#!/usr/bin/env python3
"""
M3taCron Tournament Sync Script.

Synchronizes tournament data from RollBetter, ListFortress, and Longshanks.

Usage:
    python scripts/sync_tournaments.py test     # Test with 2 tournaments per source
    python scripts/sync_tournaments.py daily    # Last 7 days (for GitHub Actions)
    python scripts/sync_tournaments.py init     # Full historical import
"""
import sys
import os
import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, select
from m3tacron.backend.database import engine, create_db_and_tables
from m3tacron.backend.models import Tournament, PlayerResult, GameFormat, MacroFormat, SubFormat
from m3tacron.backend.inference import infer_format_from_xws

from m3tacron.backend.scrapers.rollbetter import (
    fetch_tournament as rb_fetch_tournament,
    fetch_players as rb_fetch_players,
    extract_xws_from_player as rb_extract_xws,
)
from m3tacron.backend.scrapers.listfortress import (
    fetch_tournaments as lf_fetch_tournaments,
    fetch_tournament_details as lf_fetch_details,
    extract_xws_from_participant as lf_extract_xws,
)
from m3tacron.backend.scrapers.longshanks import (
    scrape_tournament as ls_scrape_tournament,
    scrape_longshanks_history as ls_scrape_history,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Known RollBetter tournament IDs to check (can be expanded)
# In practice, RB doesn't have a public search API, so we maintain a list
ROLLBETTER_IDS = [2550, 2551, 2554, 2555, 2556, 2557, 2600, 2650, 2700]


def is_duplicate(session: Session, name: str, date: datetime, player_count: int = 0, tolerance_days: int = 3) -> bool:
    """Check if tournament with similar name, date, and player count already exists."""
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
                logger.debug(f"Duplicate: '{name}' ~ '{t.name}' (players: {player_count}~{t.player_count})")
                return True
        else:
            logger.debug(f"Duplicate: '{name}' ~ '{t.name}' (name+date)")
            return True
    
    return False


async def sync_rollbetter(session: Session, since_date: datetime | None, limit: int = 0) -> int:
    """Sync tournaments from RollBetter API."""
    logger.info("=== RollBetter ===")
    count = 0
    
    ids_to_check = ROLLBETTER_IDS # Check all candidates until limit reached
    
    for t_id in ids_to_check:
        try:
            t_data = await rb_fetch_tournament(t_id)
            if not t_data:
                continue
            
            # Parse date
            t_date = datetime.now()
            if t_data.get("startDate"):
                try:
                    t_date = datetime.fromisoformat(t_data["startDate"][:10])
                except ValueError:
                    pass
            
            # Filter by date if specified
            if since_date and t_date < since_date:
                continue
            
            t_name = t_data.get("title") or t_data.get("name", f"RB-{t_id}")
            
            # Fetch players for count and XWS
            players = await rb_fetch_players(t_id)
            if len(players) < 4:
                logger.debug(f"Skipping small event: {t_name} ({len(players)} players)")
                continue
            
            if is_duplicate(session, t_name, t_date, player_count=len(players)):
                logger.info(f"[SKIP] Duplicate: {t_name}")
                continue
            
            # Process players
            player_results = []
            for i, p in enumerate(players):
                xws = rb_extract_xws(p)
                player_results.append({
                    "name": p.get("name") or p.get("displayName") or f"Player {i+1}",
                    "rank": p.get("rank") or (i + 1),
                    "xws": xws
                })
            
            # Create tournament
            t = Tournament(
                name=t_name,
                date=t_date,
                platform="RollBetter",
                format=GameFormat.OTHER.value,
                player_count=len(players),
                url=f"https://rollbetter.gg/tournaments/{t_id}"
            )
            session.add(t)
            session.commit()
            session.refresh(t)
            
            # Add player results
            for pr_data in player_results:
                pr = PlayerResult(
                    tournament_id=t.id,
                    player_name=pr_data["name"],
                    rank=pr_data["rank"],
                    list_json=pr_data["xws"] or {}
                )
                session.add(pr)
            session.commit()
            
            logger.info(f"[OK] {t_name} ({len(players)} players)")
            count += 1
            
            if limit > 0 and count >= limit:
                break
                
        except Exception as e:
            logger.warning(f"Error RB-{t_id}: {e}")
    
    return count


async def sync_listfortress(session: Session, since_date: datetime | None, limit: int = 0, max_fetch: int = 100) -> int:
    """Sync tournaments from ListFortress API."""
    logger.info("=== ListFortress ===")
    count = 0
    
    try:
        # Fetch tournaments (fetch enough to find non-duplicates)
        fetch_limit = (limit * 10) if limit > 0 else max_fetch
        # Ensure minimum fetch size
        if fetch_limit < 20: fetch_limit = 20
        
        tournaments = await lf_fetch_tournaments(limit=fetch_limit)
        logger.info(f"Fetched {len(tournaments)} tournaments from ListFortress")
        
        for t_summary in tournaments:
            if limit > 0 and count >= limit:
                break
            
            t_id = t_summary.get("id")
            t_name = t_summary.get("name", f"LF-{t_id}")
            t_date_str = t_summary.get("date", "1900-01-01")
            
            try:
                t_date = datetime.fromisoformat(t_date_str)
            except ValueError:
                t_date = datetime.now()
            
            # Filter by date if specified
            if since_date and t_date < since_date:
                continue
            
            # Fetch details for participants
            try:
                details = await lf_fetch_details(t_id)
            except Exception:
                continue
            
            if not details:
                continue
            
            participants = details.get("participants", [])
            if len(participants) < 4:
                continue
            
            if is_duplicate(session, t_name, t_date, player_count=len(participants)):
                logger.info(f"[SKIP] Duplicate: {t_name}")
                continue
            
            # Create tournament
            t = Tournament(
                name=t_name,
                date=t_date,
                platform="ListFortress",
                format=GameFormat.OTHER.value,
                player_count=len(participants),
                url=f"https://listfortress.com/tournaments/{t_id}"
            )
            session.add(t)
            session.commit()
            session.refresh(t)
            
            # Add player results
            for p in participants:
                xws = lf_extract_xws(p)
                pr = PlayerResult(
                    tournament_id=t.id,
                    player_name=p.get("name") or "Unknown",
                    rank=p.get("rank", 0),
                    swiss_rank=p.get("swiss_rank"),
                    list_json=xws or {}
                )
                session.add(pr)
            session.commit()
            
            logger.info(f"[OK] {t_name} ({len(participants)} players)")
            count += 1
            
    except Exception as e:
        logger.error(f"ListFortress error: {e}")
    
    return count


async def sync_longshanks(session: Session, since_date: datetime | None, limit: int = 0, max_pages: int = 1) -> int:
    """Sync tournaments from Longshanks (requires Playwright)."""
    logger.info("=== Longshanks ===")
    count = 0
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed, skipping Longshanks")
        return 0
    
    subdomains = ["xwing", "xwing-legacy"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            for subdomain in subdomains:
                if limit > 0 and count >= limit:
                    break
                
                logger.info(f"Scraping {subdomain} (max_pages={max_pages})...")
                
                try:
                    events = await ls_scrape_history(subdomain, max_pages=max_pages)
                    logger.info(f"Found {len(events)} events from {subdomain}")
                except Exception as e:
                    logger.warning(f"History scrape failed: {e}")
                    continue
                
                for event in events:
                    if limit > 0 and count >= limit:
                        break
                    
                    eid = event["id"]
                    t_name = event["name"]
                    t_date = event["date"]
                    player_count = event.get("player_count", 0)
                    
                    # Filter by date if specified
                    if since_date and t_date < since_date:
                        continue
                    
                    if player_count > 0 and is_duplicate(session, t_name, t_date, player_count=player_count):
                        logger.info(f"[SKIP] Duplicate: {t_name}")
                        continue
                    
                    try:
                        result = await ls_scrape_tournament(eid, subdomain, browser=browser)
                        if not result:
                            continue
                        
                        players = result.get("players", [])
                        if len(players) < 4:
                            continue
                        
                        # Double-check duplicate with actual player count
                        if is_duplicate(session, t_name, t_date, player_count=len(players)):
                            logger.info(f"[SKIP] Duplicate: {t_name}")
                            continue
                        
                        # Determine format
                        fmt_display = "2.5 Standard" if subdomain == "xwing" else "2.0 Legacy"
                        
                        t = Tournament(
                            name=t_name,
                            date=t_date,
                            platform="Longshanks",
                            format=fmt_display,
                            player_count=len(players),
                            url=event.get("url", f"https://{subdomain}.longshanks.org/event/{eid}/")
                        )
                        session.add(t)
                        session.commit()
                        session.refresh(t)
                        
                        for pl in players:
                            pr = PlayerResult(
                                tournament_id=t.id,
                                player_name=pl.get("name") or "Unknown",
                                rank=pl.get("rank", 0),
                                list_json={}
                            )
                            session.add(pr)
                        session.commit()
                        
                        logger.info(f"[OK] {t_name} ({len(players)} players)")
                        count += 1
                        
                    except Exception as e:
                        logger.warning(f"Error LS-{eid}: {e}")
                        
        finally:
            await browser.close()
    
    return count


async def run_sync(mode: str, days: int | None, limit: int):
    """Run the sync process.
    
    Args:
        mode: 'test', 'daily', or 'init'
        days: Number of days to look back, or None for all history
        limit: Max tournaments per source (0 = no limit)
    """
    logger.info("=" * 50)
    logger.info(f"M3taCron Tournament Sync - Mode: {mode.upper()}")
    logger.info("=" * 50)
    
    create_db_and_tables()
    
    # Determine date filter
    if days is None:
        since_date = None
        logger.info("Importing ALL historical tournaments (no date filter)")
    else:
        since_date = datetime.now() - timedelta(days=days)
        logger.info(f"Importing tournaments since: {since_date.date()}")
    
    if limit > 0:
        logger.info(f"Limit: {limit} per source")
    
    total = 0
    
    # Determine fetch parameters based on mode
    if mode == "init":
        lf_max_fetch = 1000  # Get as many as possible from ListFortress
        ls_max_pages = 10    # Scrape more Longshanks history pages
    else:
        lf_max_fetch = 100
        ls_max_pages = 1
    
    with Session(engine) as session:
        # Priority order: RollBetter → ListFortress → Longshanks
        total += await sync_rollbetter(session, since_date, limit)
        total += await sync_listfortress(session, since_date, limit, max_fetch=lf_max_fetch)
        total += await sync_longshanks(session, since_date, limit, max_pages=ls_max_pages)
    
    logger.info("=" * 50)
    logger.info(f"Sync complete! Total imported: {total}")
    logger.info("=" * 50)
    
    return total


def main():
    parser = argparse.ArgumentParser(
        description="M3taCron Tournament Sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/sync_tournaments.py test          # Quick test (2 per source)
  python scripts/sync_tournaments.py daily         # Last 7 days
  python scripts/sync_tournaments.py daily --days 14  # Last 14 days
  python scripts/sync_tournaments.py init          # ALL historical data
  python scripts/sync_tournaments.py init --days 90  # Last 90 days only
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Test mode
    test_parser = subparsers.add_parser("test", help="Test with few tournaments")
    test_parser.add_argument("--limit", type=int, default=2, help="Tournaments per source (default: 2)")
    test_parser.add_argument("--days", type=int, default=30, help="Days to look back (default: 30)")
    
    # Daily mode (for cron/GitHub Actions)
    daily_parser = subparsers.add_parser("daily", help="Daily incremental sync")
    daily_parser.add_argument("--days", type=int, default=3, help="Days to look back (default: 3)")
    
    # Init mode (full historical import)
    init_parser = subparsers.add_parser("init", help="Initial full historical import")
    init_parser.add_argument("--days", type=int, default=None, help="Days to look back (default: ALL history)")
    
    args = parser.parse_args()
    
    # Determine settings based on mode
    if args.command == "test":
        days = args.days
        limit = args.limit
    elif args.command == "daily":
        days = args.days
        limit = 0  # No limit for daily
    else:  # init
        days = args.days  # None = all history
        limit = 0  # No limit for init
    
    asyncio.run(run_sync(args.command, days, limit))


if __name__ == "__main__":
    main()
