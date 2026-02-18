"""
Orchestration Script for Tournament Scraping.

Combines discovery and extraction into a single workflow.
Usage:
    python -m m3tacron.scripts.scrape_tournaments \
        --platform all --time-range yesterday
"""
import argparse
import logging
import sys
from datetime import date, timedelta
from sqlmodel import create_engine

# Reuse existing logic
from m3tacron.scripts.discover_urls import _build_scrapers
from m3tacron.scripts.extract_data import run_url
from m3tacron.backend.data_structures.formats import Format

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scrape_tournaments")

VALID_PLATFORMS = ["longshanks", "rollbetter", "listfortress", "all"]
TIME_RANGES = ["yesterday", "today", "last_week"]

def _parse_date_robust(d_str: str) -> date:
    """Parse date robustly handling YYYY-MM-DD and single digit M/D."""
    try:
        return date.fromisoformat(d_str)
    except ValueError:
        pass
    
    # Fallback for non-padded 2025-8-1
    try:
        parts = d_str.split("-")
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, TypeError):
        pass
    raise ValueError(f"Invalid date format: {d_str}")


def parse_time_range(range_str: str) -> tuple[date, date]:
    """Convert named range or date string to (start_date, end_date) tuple.
    
    Supports:
    - Presets: "yesterday", "today", "last_week"
    - Single Date: "YYYY-MM-DD"
    - Date Range: "YYYY-MM-DD,YYYY-MM-DD" (start,end)
    """
    today = date.today()
    
    if range_str == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
        
    if range_str == "today":
        return today, today
        
    if range_str == "last_week":
        # last 7 days inclusive
        start = today - timedelta(days=7)
        return start, today
        
    # Try parsing as specific date(s)
    try:
        if "," in range_str:
            start_str, end_str = range_str.split(",", 1)
            start = _parse_date_robust(start_str.strip())
            end = _parse_date_robust(end_str.strip())
            return start, end
        else:
            single_date = _parse_date_robust(range_str.strip())
            return single_date, single_date
    except ValueError:
        pass
        
    raise ValueError(f"Unknown time range format: {range_str}. Use YYYY-MM-DD, range, or preset.")

def main():
    parser = argparse.ArgumentParser(description="Scrape tournaments based on platform and time range.")
    parser.add_argument(
        "--platform", default="all", choices=VALID_PLATFORMS,
        help="Platform to scrape."
    )
    parser.add_argument(
        "--time-range", default="yesterday",
        help="Time range: preset (yesterday, today, last_week) or YYYY-MM-DD or start,end."
    )
    parser.add_argument(
        "--db", default="scraped_data.db",
        help="Database connection string or path (sqlite default)."
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max number of NEW (non-duplicate) tournaments to scrape."
    )
    
    args = parser.parse_args()
    
    # 1. Setup Dates
    try:
        d_from, d_to = parse_time_range(args.time_range)
        logger.info(f"Time Range: {args.time_range} -> {d_from} to {d_to}")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
        
    # 2. Setup Scrapers
    # Default format to 'all' for broad coverage
    scrapers = _build_scrapers(args.platform, "all")
    if not scrapers and args.platform == "listfortress":
         # manual add for LF since discover_urls might not fully support it 
         # (discover_urls logic excludes ListFortress in _build_scrapers explicitly? 
         # Checked file: discover_urls.py uses FORMAT_TO_LONGSHANKS / ROLLBETTER. 
         # It DOES NOT seem to have ListFortress logic in _build_scrapers.
         # So we need to handle ListFortress manually here.)
         from m3tacron.backend.scrapers.listfortress_scraper import ListFortressScraper
         scrapers.append((ListFortressScraper(), "listfortress"))

    if not scrapers:
         # Double check if "all" missed ListFortress
         if args.platform == "all":
             from m3tacron.backend.scrapers.listfortress_scraper import ListFortressScraper
             scrapers.append((ListFortressScraper(), "listfortress"))
         
    if not scrapers:
        logger.error("No scrapers found.")
        sys.exit(1)
        
    # 3. Discover URLs
    found_tournaments = []
    
    for scraper, label in scrapers:
        logger.info(f"Discovering on {label}...")
        try:
            # Note: ListFortressScraper.list_tournaments might need checking if it follows same signature
            # Checked file: listfortress_scraper.py has list_tournaments(date_from, date_to, max_pages)
            # So signature matches BaseScraper.
            
            results = scraper.list_tournaments(
                date_from=d_from,
                date_to=d_to
            )
            for t in results:
                logger.info(f"Found: {t['name']} ({t['date']}) - {t['url']}")
                found_tournaments.append(t)
                
        except Exception as e:
            logger.error(f"Error discovering on {label}: {e}")
            
    logger.info(f"Total tournaments found: {len(found_tournaments)}")
    
    if not found_tournaments:
        logger.info("No tournaments to scrape. Exiting.")
        return

    # 4. Extract Data
    db_path = args.db
    if "sqlite" not in db_path and "postgres" not in db_path:
        db_path = f"sqlite:///{args.db}"
        
    engine = create_engine(db_path)
    
    added_count = 0
    for t in found_tournaments:
        if args.limit and added_count >= args.limit:
            logger.info(f"Reached limit of {args.limit} new tournaments. Stopping.")
            break
            
        is_new = run_url(t["url"], engine)
        if is_new:
            added_count += 1
            logger.info(f"Added new tournament. Total added: {added_count}")
        else:
            logger.info(f"Skipped duplicate or existing tournament: {t['url']}")

if __name__ == "__main__":
    main()
