"""
Tournament data collection script for M3taCron.

Collects completed X-Wing tournaments from configured platforms within a
given time range, deduplicates against the database, and persists new data.

Usage:
    python -m backend.scripts.scrape_tournaments [options]

Options:
    --platform PLATFORM    Platform(s) to scrape: all, longshanks, rollbetter,
                           listfortress. When 'all', listfortress is excluded
                           by default to avoid duplicates.
    --time-range RANGE     Time range as integer days (e.g. 7), keyword
                           (yesterday, today, week, month), or ISO date
                           (YYYY-MM-DD) as start date. Default: 1 (yesterday).
    --max-tournaments N    Maximum tournaments to collect per scraper instance.
                           Default: no limit.
    --include-listfortress When platform is 'all', also include ListFortress.
    --dry-run              List discovered tournaments without saving to DB.
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from ..database import engine, create_db_and_tables
from ..models import Match, PlayerResult, Tournament
from ..scrapers.listfortress_scraper import ListFortressScraper
from ..scrapers.longshanks_scraper import LongshanksScraper
from ..scrapers.rollbetter_scraper import RollbetterScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_time_range(value: str) -> tuple[date, date]:
    """Parse --time-range argument into (date_from, date_to).

    Accepts:
        - Positive integer string: days back from today, e.g. "7" -> last 7 days.
        - "yesterday": yesterday only.
        - "today": today only.
        - "week": last 7 days.
        - "month": last 30 days.
        - "YYYY-MM-DD": from that date to today (inclusive).

    Returns:
        Tuple of (date_from, date_to).

    Raises:
        argparse.ArgumentTypeError: If the value cannot be parsed.
    """
    today = date.today()
    normalized = value.lower().strip()

    if normalized == "yesterday":
        d = today - timedelta(days=1)
        return d, d
    if normalized == "today":
        return today, today
    if normalized == "week":
        return today - timedelta(days=7), today
    if normalized == "month":
        return today - timedelta(days=30), today

    try:
        days = int(value)
        if days <= 0:
            raise argparse.ArgumentTypeError(
                "--time-range days must be a positive integer"
            )
        return today - timedelta(days=days), today
    except ValueError:
        pass

    try:
        return datetime.strptime(value, "%Y-%m-%d").date(), today
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid --time-range value '{value}'. "
            "Accepted: positive integer (days), "
            "keyword (yesterday/today/week/month), "
            "or ISO date (YYYY-MM-DD)."
        )


def get_existing_urls(session: Session) -> set[str]:
    """Return the set of tournament URLs already present in the database."""
    return set(session.exec(select(Tournament.url)).all())


def save_tournament_data(
    session: Session,
    tournament: Tournament,
    players: list[PlayerResult],
    matches: list[Match],
) -> None:
    """Persist a tournament along with its players and matches.

    Clears explicitly set IDs so the database assigns auto-incremented values,
    then links players and matches to the newly inserted tournament.
    """
    # Let the DB assign the primary key to avoid cross-platform ID collisions.
    tournament.id = None
    session.add(tournament)
    session.flush()  # Populate tournament.id

    # Map player name -> DB id for match resolution after insert.
    player_id_map: dict[str, int] = {}
    for player in players:
        player.id = None
        player.tournament_id = tournament.id
        session.add(player)
        session.flush()
        if player.id is not None:
            player_id_map[player.player_name.lower().strip()] = player.id

    for match in matches:
        match.id = None
        match.tournament_id = tournament.id
        # Resolve temporary name references to real DB player IDs.
        if match.p1_name_temp:
            match.player1_id = player_id_map.get(match.p1_name_temp.lower().strip())
        if match.p2_name_temp:
            match.player2_id = player_id_map.get(match.p2_name_temp.lower().strip())
        session.add(match)


def _extract_tournament_id(url: str) -> str:
    """Extract the platform-specific tournament ID from its URL."""
    return url.rstrip("/").split("/")[-1]


def scrape_platform(
    scraper,
    scraper_name: str,
    date_from: date,
    date_to: date,
    max_tournaments: int | None,
    existing_urls: set[str],
) -> tuple[int, int]:
    """Discover and persist tournaments for a single scraper instance.

    Args:
        scraper: An instance of a BaseScraper subclass.
        scraper_name: Human-readable name for log messages.
        date_from: Start of the date range (inclusive).
        date_to: End of the date range (inclusive).
        max_tournaments: Cap on tournaments to process. None = no limit.
        existing_urls: URLs already in the database (mutated on success).

    Returns:
        Tuple of (saved_count, skipped_count).
    """
    logger.info(f"[{scraper_name}] Listing tournaments from {date_from} to {date_to}...")
    try:
        candidates = scraper.list_tournaments(date_from, date_to)
    except Exception as exc:
        logger.error(f"[{scraper_name}] Failed to list tournaments: {exc}")
        return 0, 0

    logger.info(f"[{scraper_name}] Found {len(candidates)} candidate(s).")

    if max_tournaments is not None:
        candidates = candidates[:max_tournaments]

    saved = 0
    skipped = 0

    for item in candidates:
        url: str = item.get("url", "")
        name: str = item.get("name", "Unknown")

        if url in existing_urls:
            logger.debug(f"[{scraper_name}] Already in DB, skipping: {name} ({url})")
            skipped += 1
            continue

        tournament_id = _extract_tournament_id(url)
        logger.info(f"[{scraper_name}] Scraping: {name} (id={tournament_id})")

        try:
            tournament, players, matches = scraper.run_full_scrape(tournament_id)
            # Ensure the URL is always stored; scrapers may not set it consistently.
            tournament.url = url

            with Session(engine) as session:
                save_tournament_data(session, tournament, players, matches)
                session.commit()

            existing_urls.add(url)
            saved += 1
            logger.info(
                f"[{scraper_name}] Saved '{tournament.name}' "
                f"({len(players)} player(s), {len(matches)} match(es))."
            )
        except Exception as exc:
            logger.error(
                f"[{scraper_name}] Failed to scrape '{name}' ({url}): {exc}"
            )

    return saved, skipped


def build_scrapers(
    platform: str, include_listfortress: bool
) -> list[tuple[str, object]]:
    """Build the list of (name, scraper) pairs to run.

    Longshanks is split into two instances (2.5 and Legacy 2.0 subdomains).
    RollBetter is split into AMG (game 5) and XWA (game 17) game systems.
    ListFortress is opt-in when platform is 'all'.
    """
    scrapers: list[tuple[str, object]] = []

    if platform in ("all", "longshanks"):
        scrapers.append(("longshanks_25", LongshanksScraper(subdomain="xwing")))
        scrapers.append(("longshanks_legacy", LongshanksScraper(subdomain="xwing-legacy")))

    if platform in ("all", "rollbetter"):
        scrapers.append(("rollbetter_amg", RollbetterScraper(game_id=5)))
        scrapers.append(("rollbetter_xwa", RollbetterScraper(game_id=17)))

    if platform == "listfortress" or (platform == "all" and include_listfortress):
        scrapers.append(("listfortress", ListFortressScraper()))

    return scrapers


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect completed X-Wing tournament data from online platforms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--platform",
        default="all",
        choices=["all", "longshanks", "rollbetter", "listfortress"],
        help=(
            "Platform to scrape. 'all' scrapes Longshanks and RollBetter. "
            "Default: all."
        ),
    )
    parser.add_argument(
        "--time-range",
        default="1",
        dest="time_range",
        metavar="RANGE",
        help=(
            "Time range: positive integer (days back from today), keyword "
            "(yesterday/today/week/month), or ISO date YYYY-MM-DD (start date). "
            "Default: 1 (yesterday)."
        ),
    )
    parser.add_argument(
        "--max-tournaments",
        type=int,
        default=None,
        dest="max_tournaments",
        metavar="N",
        help="Maximum tournaments to collect per scraper instance. Default: no limit.",
    )
    parser.add_argument(
        "--include-listfortress",
        action="store_true",
        dest="include_listfortress",
        help="When platform is 'all', also scrape ListFortress (excluded by default).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="List discovered tournaments without writing to the database.",
    )
    args = parser.parse_args()

    try:
        date_from, date_to = parse_time_range(args.time_range)
    except argparse.ArgumentTypeError as exc:
        logger.error(str(exc))
        return 1

    logger.info(
        f"Date range: {date_from} -> {date_to} | "
        f"Platform: {args.platform} | "
        f"Max per scraper: {args.max_tournaments or 'unlimited'} | "
        f"Dry run: {args.dry_run}"
    )

    if not args.dry_run:
        create_db_and_tables()

    scrapers = build_scrapers(args.platform, args.include_listfortress)
    if not scrapers:
        logger.error("No scrapers configured for the given --platform value.")
        return 1

    if args.dry_run:
        for name, scraper in scrapers:
            try:
                candidates = scraper.list_tournaments(date_from, date_to)
                logger.info(
                    f"[{name}] DRY RUN: {len(candidates)} tournament(s) discovered."
                )
                for item in candidates:
                    logger.info(
                        f"  - {item.get('name', 'Unknown')} ({item.get('url', '')})"
                    )
            except Exception as exc:
                logger.error(f"[{name}] DRY RUN listing failed: {exc}")
        return 0

    with Session(engine) as session:
        existing_urls = get_existing_urls(session)
    logger.info(f"Database contains {len(existing_urls)} existing tournament URL(s).")

    total_saved = 0
    total_skipped = 0

    for name, scraper in scrapers:
        saved, skipped = scrape_platform(
            scraper, name, date_from, date_to, args.max_tournaments, existing_urls
        )
        total_saved += saved
        total_skipped += skipped

    logger.info(
        f"Finished. Saved: {total_saved} new tournament(s), "
        f"skipped: {total_skipped} duplicate(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
