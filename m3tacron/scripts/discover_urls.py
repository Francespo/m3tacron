"""
URL Discovery Script.

Given a format, date range, and platform, discovers tournament URLs
from platform listing pages.

Usage:
    python -m m3tacron.scripts.discover_urls \
        --platform longshanks --format xwa \
        --from 2025-01-01 --to 2025-12-31 \
        --max-pages 2 --output urls.txt
"""
import argparse
import logging
import sys
from datetime import date

from m3tacron.backend.data_structures.formats import Format
from m3tacron.backend.scrapers.longshanks import LongshanksScraper
from m3tacron.backend.scrapers.rollbetter import RollbetterScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discover_urls")

# --- Format-to-platform mapping ---

# Longshanks: format -> subdomain
FORMAT_TO_LONGSHANKS_SUBDOMAIN: dict[str, str] = {
    "amg": "xwing",
    "xwa": "xwing",
    "legacy_x2po": "xwing-legacy",
    "legacy_xlc": "xwing-legacy",
    "ffg": "xwing-legacy",
}

# Rollbetter: format -> game_id
FORMAT_TO_ROLLBETTER_GAME_ID: dict[str, int] = {
    "amg": 5,
    "xwa": 17,
    "legacy_x2po": 4,
    "legacy_xlc": 4,
    "ffg": 4,
}

VALID_FORMATS = list(Format.__members__.keys()) + ["all"]
VALID_PLATFORMS = ["longshanks", "rollbetter", "all"]


def _build_scrapers(platform: str, fmt: str) -> list:
    """Build scraper instances based on platform and format selection.

    Returns:
        List of (scraper, label) tuples.
    """
    scrapers = []

    # Determine which format keys to use
    if fmt == "all":
        # Deduplicate game_ids/subdomains to avoid scraping same page twice
        format_keys = list(FORMAT_TO_LONGSHANKS_SUBDOMAIN.keys())
    else:
        format_keys = [fmt]

    if platform in ("longshanks", "all"):
        # Deduplicate subdomains
        seen_subdomains = set()
        for fk in format_keys:
            subdomain = FORMAT_TO_LONGSHANKS_SUBDOMAIN.get(fk)
            if subdomain and subdomain not in seen_subdomains:
                seen_subdomains.add(subdomain)
                scrapers.append((
                    LongshanksScraper(subdomain=subdomain),
                    f"longshanks/{subdomain}"
                ))

    if platform in ("rollbetter", "all"):
        # Deduplicate game_ids
        seen_game_ids = set()
        for fk in format_keys:
            game_id = FORMAT_TO_ROLLBETTER_GAME_ID.get(fk)
            if game_id and game_id not in seen_game_ids:
                seen_game_ids.add(game_id)
                scrapers.append((
                    RollbetterScraper(game_id=game_id),
                    f"rollbetter/game_{game_id}"
                ))

    return scrapers


def main():
    parser = argparse.ArgumentParser(
        description="Discover tournament URLs from platform listing pages."
    )
    parser.add_argument(
        "--platform", required=True, choices=VALID_PLATFORMS,
        help="Platform to scrape: longshanks, rollbetter, or all."
    )
    parser.add_argument(
        "--format", required=True,
        choices=[f.value for f in Format] + ["all"],
        help="Game format filter (coarse: maps to game ID/subdomain)."
    )
    parser.add_argument(
        "--from", dest="date_from", required=True,
        help="Start date (YYYY-MM-DD, inclusive)."
    )
    parser.add_argument(
        "--to", dest="date_to", required=True,
        help="End date (YYYY-MM-DD, inclusive)."
    )
    parser.add_argument(
        "--max-pages", type=int, default=None,
        help="Max listing pages to scrape per platform. Default: no limit."
    )
    parser.add_argument(
        "--output", default=None,
        help="Output file path. Default: stdout."
    )

    args = parser.parse_args()

    # Parse dates
    try:
        d_from = date.fromisoformat(args.date_from)
        d_to = date.fromisoformat(args.date_to)
    except ValueError as e:
        logger.error(f"Invalid date format: {e}. Use YYYY-MM-DD.")
        sys.exit(1)

    if d_from > d_to:
        logger.error("--from date must be before --to date.")
        sys.exit(1)

    scrapers = _build_scrapers(args.platform, args.format)
    if not scrapers:
        logger.error("No valid scrapers for the given platform/format combination.")
        sys.exit(1)

    # Scrape each platform and collect URLs
    all_urls = []
    for scraper, label in scrapers:
        logger.info(f"Scraping {label}...")
        try:
            tournaments = scraper.list_tournaments(
                date_from=d_from,
                date_to=d_to,
                max_pages=args.max_pages
            )
            for t in tournaments:
                all_urls.append(t["url"])
                logger.info(f"  {t['date']} | {t['name']} | {t['player_count']}p | {t['url']}")
        except Exception as e:
            logger.error(f"Error scraping {label}: {e}")

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for url in all_urls:
                f.write(url + "\n")
        logger.info(f"Wrote {len(all_urls)} URLs to {args.output}")
    else:
        for url in all_urls:
            print(url)

    logger.info(f"Total: {len(all_urls)} tournament URLs discovered.")


if __name__ == "__main__":
    main()
