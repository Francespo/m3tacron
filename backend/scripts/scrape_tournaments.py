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
    --time-range RANGE     Time range (see parse_time_range for full list):
                           Single day:  today | yesterday | YYYY-MM-DD
                           Range:       last 3 days | last week | last month |
                                        last 3 months | last 6 months | last year |
                                        all time
                           Explicit:    YYYY-MM-DD:YYYY-MM-DD | YYYY-MM-DD:today
                           Legacy:      positive integer (days back)
                           Default: yesterday.
    --max-tournaments N    Maximum tournaments to collect per scraper instance.
                           Default: no limit.
    --include-listfortress When platform is 'all', also include ListFortress.
    --dry-run              List discovered tournaments without saving to DB.
    --tournament-url URL   Scrape a specific tournament URL (repeatable). When
                           provided, the scraper bypasses listing and ignores
                           --platform/--time-range for discovery.
"""

import argparse
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

from sqlalchemy import func
from sqlmodel import Session, create_engine, select

from ..database import engine, create_db_and_tables
from ..data_structures.round_types import RoundType
from ..models import Match, PlayerStanding, Tournament, TeamStanding, TeamMatch
from ..scrapers.listfortress_scraper import ListFortressScraper
from ..scrapers.longshanks_scraper import LongshanksScraper
from ..scrapers.rollbetter_scraper import RollbetterScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Module-level lock to serialize database writes across parallel scraper
# workers.  The save_tournament_data helper assigns explicit IDs via
# MAX+1, which is not atomic across concurrent transactions.  Holding
# this lock around the commit window prevents duplicate-key violations.
_DB_WRITE_LOCK = threading.Lock()


def parse_time_range(value: str) -> tuple[date, date]:
    """Parse --time-range argument into (date_from, date_to).

    Accepts (case-insensitive):
        Single day keywords:
            - "today"          → today only
            - "yesterday"      → yesterday only

        Single ISO date:
            - "YYYY-MM-DD"     → that day only (not a range to today)

        Range keywords:
            - "last 3 days"    → last 3 days (including today)
            - "last week"      → last 7 days
            - "last month"     → last 30 days
            - "last 3 months"  → last ~90 days
            - "last 6 months"  → last ~180 days
            - "last year"      → last 365 days
            - "all time"       → 2018-09-13 to today

        Explicit ranges:
            - "YYYY-MM-DD:YYYY-MM-DD"       → exact range
            - "YYYY-MM-DD:today"            → from date to today
            - "YYYY-MM-DD:yesterday"        → from date to yesterday
            - "yesterday:today"             → yesterday through today
            - "yesterday:YYYY-MM-DD"        → yesterday to that date

        Legacy (still supported):
            - Positive integer: days back from today

    Returns:
        Tuple of (date_from, date_to).

    Raises:
        argparse.ArgumentTypeError: If the value cannot be parsed.
    """
    today = date.today()
    normalized = value.lower().strip()

    # --- Single-day keywords ---
    if normalized == "yesterday":
        d = today - timedelta(days=1)
        return d, d
    if normalized == "today":
        return today, today

    # --- Range keywords ---
    RANGE_KEYWORDS: dict[str, int] = {
        "last 3 days": 3,
        "last week": 7,
        "last month": 30,
        "last 3 months": 91,
        "last 6 months": 182,
        "last year": 365,
    }
    if normalized in RANGE_KEYWORDS:
        days = RANGE_KEYWORDS[normalized]
        return today - timedelta(days=days - 1), today

    if normalized == "all time":
        return date(2018, 9, 13), today

    # --- Legacy integer days ---
    try:
        days = int(value)
        if days <= 0:
            raise argparse.ArgumentTypeError(
                "--time-range days must be a positive integer"
            )
        return today - timedelta(days=days - 1), today
    except ValueError:
        pass

    # --- Helper to resolve a single part to a date ---
    def _resolve_part(part: str) -> date:
        part = part.strip().lower()
        if part == "today":
            return today
        if part == "yesterday":
            return today - timedelta(days=1)
        try:
            return datetime.strptime(part, "%Y-%m-%d").date()
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Invalid date part '{part}'. Expected YYYY-MM-DD, today, or yesterday."
            )

    # --- Explicit ranges with ":" ---
    if ":" in value:
        parts = value.split(":", 1)
        try:
            date_from = _resolve_part(parts[0])
            date_to = _resolve_part(parts[1])
            if date_from > date_to:
                raise argparse.ArgumentTypeError(
                    f"Start date {date_from} is after end date {date_to}."
                )
            return date_from, date_to
        except argparse.ArgumentTypeError:
            raise
        except Exception:
            raise argparse.ArgumentTypeError(
                f"Invalid date range '{value}'. Expected format: YYYY-MM-DD:YYYY-MM-DD, "
                "or mix keywords like yesterday:today."
            )

    # --- Single ISO date → that day only ---
    try:
        d = datetime.strptime(value, "%Y-%m-%d").date()
        return d, d
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid --time-range value '{value}'. "
            "Accepted: single day (today/yesterday/YYYY-MM-DD), "
            "range keyword (last 3 days/last week/last month/last 3 months/last 6 months/last year/all time), "
            "ISO date range (YYYY-MM-DD:YYYY-MM-DD or YYYY-MM-DD:today/yesterday), "
            "or positive integer (days back)."
        )


def get_existing_urls(session: Session) -> set[str]:
    """Return the set of tournament URLs already present in the database."""
    return set(session.exec(select(Tournament.url)).all())


def _delete_existing_tournament(session: Session, url: str) -> None:
    from sqlmodel import delete
    from ..models import Match, TeamMatch, PlayerStanding, TeamStanding, Tournament

    existing = session.exec(select(Tournament).where(
        Tournament.url == url)).first()
    if existing:
        logger.info(f"Deleting existing tournament data for {url}")
        session.exec(delete(TeamMatch).where(
            TeamMatch.tournament_id == existing.id))
        session.exec(delete(Match).where(Match.tournament_id == existing.id))
        session.exec(delete(PlayerStanding).where(
            PlayerStanding.tournament_id == existing.id))
        session.exec(delete(TeamStanding).where(
            TeamStanding.tournament_id == existing.id))
        session.exec(delete(Tournament).where(Tournament.id == existing.id))
        session.commit()


def save_tournament_data(
    session: Session,
    tournament: Tournament,
    players: list[PlayerStanding],
    matches: list,
) -> None:
    """Persist a tournament along with its players and matches.

    Assigns explicit next IDs (MAX+1) so saves work correctly on both fresh
    databases (with SERIAL) and pre-existing databases that have integer
    primary keys without a DEFAULT sequence.

    ``matches`` may contain either ``Match`` objects or dicts as returned by
    the scrapers' ``get_matches`` methods.
    """
    # Assign next tournament ID explicitly.
    max_t = session.exec(select(func.max(Tournament.id))).first()
    tournament.id = (max_t or 0) + 1
    session.add(tournament)
    session.flush()  # Flush so player FKs can reference tournament.id

    # --- Teams: build TeamStanding rows if team names are present in players
    team_names: set[str] = set()
    for p in players:
        tname = getattr(p, "team_name", None)
        if tname:
            team_names.add(tname.strip())
    # Also include any team names that appear in team matches
    for m in matches:
        if isinstance(m, dict) and m.get("is_team_match"):
            if m.get("p1_name_temp"):
                team_names.add(m.get("p1_name_temp").strip())
            if m.get("p2_name_temp"):
                team_names.add(m.get("p2_name_temp").strip())

    team_id_map: dict[str, int] = {}
    if team_names:
        max_tsid = session.exec(select(func.max(TeamStanding.id))).first()
        next_tsid = (max_tsid or 0) + 1
        for i, tname in enumerate(sorted(team_names)):
            ts = TeamStanding(
                id=next_tsid + i,
                tournament_id=tournament.id,
                team_name=tname,
            )
            session.add(ts)
            team_id_map[tname.lower().strip()] = ts.id
        session.flush()

    # Assign player IDs from current max + offset so they are unique.
    max_p = session.exec(select(func.max(PlayerStanding.id))).first()
    next_p_id = (max_p or 0) + 1

    player_id_map: dict[str, int] = {}
    for i, player in enumerate(players):
        player.id = next_p_id + i
        player.tournament_id = tournament.id
        # Link player to team_id if team_name available
        tname = getattr(player, "team_name", None)
        if tname:
            player.team_id = team_id_map.get(tname.lower().strip())
        session.add(player)
        if player.player_name:
            player_id_map[player.player_name.lower().strip()] = player.id

    if players:
        session.flush()  # Flush so match FKs can reference player IDs

    # Assign match IDs from current max + offset.
    # Scrapers return match dicts; convert them to Match or TeamMatch objects here.
    max_m = session.exec(select(func.max(Match.id))).first()
    next_m_id = (max_m or 0) + 1
    max_tm = session.exec(select(func.max(TeamMatch.id))).first()
    next_tm_id = (max_tm or 0) + 1

    m_counter = 0
    tm_counter = 0
    for match_raw in matches:
        if isinstance(match_raw, dict) and match_raw.get("is_team_match"):
            p1_name = (match_raw.get("p1_name_temp") or "").lower().strip()
            p2_name = (match_raw.get("p2_name_temp") or "").lower().strip()
            winner_name = (match_raw.get("winner_name_temp")
                           or "").lower().strip()
            team1_id = team_id_map.get(p1_name)
            team2_id = team_id_map.get(p2_name)
            winner_id = team_id_map.get(winner_name)
            tm = TeamMatch(
                id=next_tm_id + tm_counter,
                tournament_id=tournament.id,
                round_number=match_raw["round_number"],
                round_type=match_raw.get("round_type", RoundType.SWISS),
                team1_score=match_raw.get("player1_score", -1),
                team2_score=match_raw.get("player2_score", -1),
                is_bye=match_raw.get("is_bye", False),
                team1_id=team1_id,
                team2_id=team2_id,
                winner_id=winner_id,
            )
            session.add(tm)
            tm_counter += 1
        else:
            if isinstance(match_raw, dict):
                # Resolve player names to DB IDs directly from the scraper dict.
                p1_name = (match_raw.get("p1_name_temp") or "").lower().strip()
                p2_name = (match_raw.get("p2_name_temp") or "").lower().strip()
                winner_name = (match_raw.get("winner_name_temp")
                               or "").lower().strip()
                match = Match(
                    round_number=match_raw["round_number"],
                    round_type=match_raw.get("round_type", RoundType.SWISS),
                    scenario=match_raw.get("scenario"),
                    player1_score=match_raw.get("player1_score", -1),
                    player2_score=match_raw.get("player2_score", -1),
                    is_bye=match_raw.get("is_bye", False),
                    player1_id=player_id_map.get(p1_name),
                    player2_id=player_id_map.get(p2_name),
                    winner_id=player_id_map.get(winner_name),
                )
            else:
                match = match_raw
                # Resolve winner from the object if it has a temp name attr.
                winner_name_attr = getattr(match_raw, "winner_name_temp", None)
                if winner_name_attr:
                    match.winner_id = player_id_map.get(
                        winner_name_attr.lower().strip(), None)
            match.id = next_m_id + m_counter
            match.tournament_id = tournament.id
            session.add(match)
            m_counter += 1


def _extract_tournament_id(url: str) -> str:
    """Extract the platform-specific tournament ID from its URL."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if not path:
        return ""
    return path.split("/")[-1]


def _scrape_by_url(
    url: str,
    existing_urls: set[str],
    saved_items: list | None = None,
    overwrite: bool = False,
) -> tuple[bool, str | None]:
    """Scrape a single tournament URL and persist it.

    Returns:
        Tuple of (saved, error_message). If saved is True, error_message is None.
    """
    if url in existing_urls:
        if not overwrite:
            # Check if this IS NOT rollbetter/longshanks, and we have a rollbetter/longshanks version already?
            # Actually, the 'existing_urls' check only handles the EXACT same URL.
            # We need the dedup check here to catch rollbetter tournaments being re-scraped from listfortress.
            logger.debug(f"Already in DB (URL match), skipping: {url}")
            return False, None
        else:
            logger.info(f"Overwriting existing tournament: {url}")
    
    # If it's listfortress, we check if it already exists from a better source
    if "listfortress.com" in url and not overwrite:
        # We don't have the tournament object yet, so we have to scrape it first or do a light check.
        # But we can use _extract_tournament_id and do a quick check? 
        # Actually, let's wait until we have the data object.
        pass

    tournament_id = _extract_tournament_id(url)
    if not tournament_id:
        return False, f"Could not parse tournament ID from URL: {url}"

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()

    try:
        if "rollbetter.gg" in host:
            candidates = [
                ("rollbetter_amg", RollbetterScraper(game_id=5)),
                ("rollbetter_xwa", RollbetterScraper(game_id=17)),
                ("rollbetter_legacy", RollbetterScraper(game_id=4)),
                ("rollbetter_legacy", RollbetterScraper(game_id=4)),
            ]
            last_exc: Exception | None = None
            for name, scraper in candidates:
                try:
                    tournament, players, matches = scraper.run_full_scrape(
                        tournament_id)
                    scraper_name = name
                    break
                except Exception as exc:
                    logger.warning(
                        f"[{name}] Failed to scrape {url} (id={tournament_id}): {exc}"
                    )
                    last_exc = exc
            else:
                raise last_exc or ValueError("No Rollbetter scraper succeeded")
        elif "xwing-legacy.longshanks.org" in host:
            scraper = LongshanksScraper(subdomain="xwing-legacy")
            scraper_name = "longshanks_legacy"
            tournament, players, matches = scraper.run_full_scrape(
                tournament_id)
        elif "xwing.longshanks.org" in host:
            scraper = LongshanksScraper(subdomain="xwing")
            scraper_name = "longshanks_25"
            tournament, players, matches = scraper.run_full_scrape(
                tournament_id)
        elif "listfortress.com" in host:
            scraper = ListFortressScraper()
            scraper_name = "listfortress"
            tournament, players, matches = scraper.run_full_scrape(
                tournament_id)
        else:
            return False, f"Unsupported tournament URL host: {url}"
    except Exception as exc:
        return False, f"Scrape failed for {url} (id={tournament_id}): {exc}"

    tournament.url = url
    raw_matches = list(matches)

    if len(players) == 0:
        logger.info(f"[{scraper_name}] '{tournament.name}' has 0 players. Skipping.")
        return False, None

    with Session(engine, expire_on_commit=False) as session:
        # Check source priority: listfortress can't overwrite/duplicate RB/Longshanks
        # We always check for duplicates for listfortress unless forced otherwise.
        from .dedup_utils import check_for_duplicates
        dup = check_for_duplicates(session, tournament, players, overwrite=overwrite)
        if dup:
            # If the duplicate is NOT from listfortress, we NEVER allow overwrite by listfortress
            if scraper_name == "listfortress" and dup.source != Source.LISTFORTRESS:
                logger.info(
                    f"[{scraper_name}] Protected tournament found: '{dup.name}' ({dup.source}). "
                    f"Cannot overwrite with ListFortress data. Skipping."
                )
                return False, f"Duplicate of protected source {dup.source} ({dup.url})"

            if scraper_name == "listfortress":
                logger.info(
                    f"[{scraper_name}] Dedup detected '{tournament.name}' is a duplicate of '{dup.name}' ({dup.url}). Skipping.")
                return False, f"Duplicate of {dup.url}"

        if overwrite:
            _delete_existing_tournament(session, url)
        save_tournament_data(session, tournament, players, matches)
        t_name = tournament.name
        n_players = len(players)
        n_matches = len(raw_matches)
        session.commit()

    existing_urls.add(url)
    if saved_items is not None:
        saved_items.append((tournament, players, raw_matches))

    logger.info(
        f"[{scraper_name}] Saved '{t_name}' "
        f"({n_players} player(s), {n_matches} match(es))."
    )
    return True, None


def scrape_platform(
    scraper,
    scraper_name: str,
    date_from: date,
    date_to: date,
    max_tournaments: int | None,
    existing_urls: set[str],
    saved_items: list | None = None,
    overwrite: bool = False,
) -> tuple[int, int]:
    """Discover and persist tournaments for a single scraper instance.

    Args:
        scraper: An instance of a BaseScraper subclass.
        scraper_name: Human-readable name for log messages.
        date_from: Start of the date range (inclusive).
        date_to: End of the date range (inclusive).
        max_tournaments: Cap on tournaments to process. None = no limit.
        existing_urls: URLs already in the database (mutated on success).
        saved_items: Optional list to append raw (tournament, players, matches)
            tuples to for each successfully saved tournament (e.g. for SQLite
            artifact output).

    Returns:
        Tuple of (saved_count, skipped_count).
    """
    logger.info(
        f"[{scraper_name}] Listing tournaments from {date_from} to {date_to}...")
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
            if not overwrite:
                logger.debug(
                    f"[{scraper_name}] Already in DB, skipping: {name} ({url})")
                skipped += 1
                continue
            else:
                logger.info(
                    f"[{scraper_name}] Overwriting existing tournament: {name} ({url})")

        tournament_id = _extract_tournament_id(url)
        logger.info(f"[{scraper_name}] Scraping: {name} (id={tournament_id})")

        try:
            tournament, players, matches = scraper.run_full_scrape(
                tournament_id)
            # Ensure the URL is always stored; scrapers may not set it consistently.
            tournament.url = url

            # Keep a copy of the raw matches (dicts) before save_tournament_data
            # converts them to Match objects, so they can be reused for SQLite output.
            raw_matches = list(matches)

            # expire_on_commit=False keeps object attribute values in memory after
            # commit so they remain accessible once the session closes (detaches
            # objects).  Without this, SQLAlchemy expires all attributes on commit
            # and any access after the 'with' block raises DetachedInstanceError.
            #
            # The DB write is serialised across parallel scraper workers via
            # _DB_WRITE_LOCK because save_tournament_data assigns explicit
            # IDs (MAX+1) which is not atomic across concurrent transactions.
            with _DB_WRITE_LOCK:
                with Session(engine, expire_on_commit=False) as session:
                    from .dedup_utils import check_for_duplicates
                    # ListFortress cannot overwrite or duplicate higher priority sources
                    dup = check_for_duplicates(
                        session, tournament, players, overwrite=overwrite)
                    if dup:
                        if scraper_name == "listfortress" and dup.source != Source.LISTFORTRESS:
                            logger.info(
                                f"[{scraper_name}] Protected tournament found: '{dup.name}' ({dup.source}). "
                                f"Cannot overwrite with ListFortress data. Skipping."
                            )
                            skipped += 1
                            continue

                        if scraper_name == "listfortress":
                            logger.info(
                                f"[{scraper_name}] Dedup detected '{tournament.name}' is a duplicate of '{dup.name}' ({dup.url}). Skipping.")
                            skipped += 1
                            continue

                    if overwrite:
                        _delete_existing_tournament(session, url)
                    save_tournament_data(session, tournament, players, matches)
                    # Capture values for logging while the session is still open.
                    t_name = tournament.name
                    n_players = len(players)
                    n_matches = len(raw_matches)
                    session.commit()

                existing_urls.add(url)
                saved += 1
                if saved_items is not None:
                    saved_items.append((tournament, players, raw_matches))
            logger.info(
                f"[{scraper_name}] Saved '{t_name}' "
                f"({n_players} player(s), {n_matches} match(es))."
            )
        except Exception as exc:
            logger.error(
                f"[{scraper_name}] Failed to scrape '{name}' ({url}): {exc}",
                exc_info=True,
            )

    return saved, skipped


def _write_sqlite(sqlite_path: str, saved_items: list) -> None:
    """Write saved tournaments to a local SQLite file as artifact.

    Creates fresh model instances with clean IDs independent of the main DB.

    Args:
        sqlite_path: Filesystem path for the SQLite database file.
        saved_items: List of (tournament, players, raw_matches) tuples collected
            during the main scrape run.
    """
    from sqlmodel import SQLModel as _SQLModel

    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    _SQLModel.metadata.create_all(sqlite_engine)

    with Session(sqlite_engine, expire_on_commit=False) as session:
        for tournament, players, raw_matches in saved_items:
            # Build fresh Tournament instance — do NOT reuse the ORM object that
            # was attached to the main-DB session to avoid identity-map conflicts.
            t_copy = Tournament(
                name=tournament.name,
                date=tournament.date,
                location=tournament.location,
                player_count=tournament.player_count,
                team_count=tournament.team_count,
                url=tournament.url,
                source=tournament.source,
                format=tournament.format,
            )
            p_copies = [
                PlayerStanding(
                    player_name=p.player_name,
                    team_id=getattr(p, "team_id", None),
                    swiss_rank=p.swiss_rank,
                    swiss_wins=p.swiss_wins,
                    swiss_losses=p.swiss_losses,
                    swiss_draws=p.swiss_draws,
                    swiss_event_points=p.swiss_event_points,
                    # swiss_tie_breaker_points has type `int` but default `None` in
                    # the model, creating a NOT NULL / None mismatch.  Use 0 as a
                    # safe sentinel rather than silently passing None.
                    swiss_tie_breaker_points=(
                        0 if p.swiss_tie_breaker_points is None
                        else p.swiss_tie_breaker_points
                    ),
                    cut_rank=p.cut_rank,
                    cut_wins=p.cut_wins,
                    cut_losses=p.cut_losses,
                    cut_draws=p.cut_draws,
                    cut_event_points=p.cut_event_points,
                    cut_tie_breaker_points=p.cut_tie_breaker_points,
                    list_json=p.list_json or {},
                )
                for p in players
            ]
            save_tournament_data(session, t_copy, p_copies, raw_matches)
        session.commit()

    logger.info(
        f"SQLite artifact written: {sqlite_path} "
        f"({len(saved_items)} tournament(s))"
    )


def build_scrapers(
    platform: str, include_listfortress: bool
) -> list[tuple[str, object]]:
    """Build the list of (name, scraper) pairs to run.

    Longshanks is split into two instances (2.5 and Legacy 2.0 subdomains).
    RollBetter is split into AMG (game 5), XWA (game 17), and Legacy 2.0
    (game 4) game systems.
    RollBetter is split into AMG (game 5), XWA (game 17), and Legacy 2.0
    (game 4) game systems.

    Platform options:
        - 'longshanks+rollbetter': Longshanks and RollBetter only (default).
        - 'longshanks': Longshanks only.
        - 'rollbetter': RollBetter only.
        - 'listfortress': ListFortress only.
        - 'all': All three platforms (Longshanks + RollBetter + ListFortress).
    """
    scrapers: list[tuple[str, object]] = []

    if platform in ("all", "longshanks+rollbetter", "longshanks"):
        scrapers.append(
            ("longshanks_25", LongshanksScraper(subdomain="xwing")))
        scrapers.append(
            ("longshanks_legacy", LongshanksScraper(subdomain="xwing-legacy")))

    if platform in ("all", "longshanks+rollbetter", "rollbetter"):
        scrapers.append(("rollbetter_amg", RollbetterScraper(game_id=5)))
        scrapers.append(("rollbetter_xwa", RollbetterScraper(game_id=17)))
        scrapers.append(("rollbetter_legacy", RollbetterScraper(game_id=4)))
        scrapers.append(("rollbetter_legacy", RollbetterScraper(game_id=4)))

    if platform in ("listfortress", "all") or (
        platform == "longshanks+rollbetter" and include_listfortress
    ):
        scrapers.append(("listfortress", ListFortressScraper()))

    return scrapers


def _split_scrapers(
    scrapers: list[tuple[str, object]],
) -> tuple[list[tuple[str, object]], list[tuple[str, object]]]:
    """Split scrapers into independent and dependent groups.

    Independent scrapers (Longshanks, Rollbetter) can run in parallel
    because they pull from different data sources with no URL overlap.

    Dependent scrapers (ListFortress) must run *after* all independent
    scrapers finish, so they can deduplicate against the full set of
    already-saved tournament URLs.

    Returns:
        Tuple of (independent_scrapers, dependent_scrapers).
    """
    independent: list[tuple[str, object]] = []
    dependent: list[tuple[str, object]] = []

    for name, scraper in scrapers:
        if "listfortress" in name:
            dependent.append((name, scraper))
        else:
            independent.append((name, scraper))

    return independent, dependent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect completed X-Wing tournament data from online platforms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--platform",
        default="longshanks+rollbetter",
        choices=["longshanks+rollbetter", "longshanks",
                 "rollbetter", "listfortress", "all"],
        help=(
            "Platform(s) to scrape. "
            "'longshanks+rollbetter' scrapes Longshanks and RollBetter (default). "
            "'all' scrapes all three platforms including ListFortress. "
            "Default: longshanks+rollbetter."
        ),
    )
    parser.add_argument(
        "--time-range",
        default="1",
        dest="time_range",
        metavar="RANGE",
        help=(
            "Time range. Single day: today, yesterday, YYYY-MM-DD. "
            "Range keyword: last 3 days, last week, last month, "
            "last 3 months, last 6 months, last year, all time. "
            "Explicit range: YYYY-MM-DD:YYYY-MM-DD or YYYY-MM-DD:today/yesterday. "
            "Legacy: positive integer (days back). Default: 1 (yesterday)."
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
        help="When platform is 'longshanks+rollbetter', also scrape ListFortress.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="List discovered tournaments without writing to the database.",
    )
    parser.add_argument(
        "--tournament-url",
        action="append",
        dest="tournament_urls",
        metavar="URL",
        help=(
            "Scrape a specific tournament URL (repeatable). "
            "When provided, discovery uses these URLs instead of listings."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        dest="overwrite",
        help="Overwrite existing tournaments if they are already in the database.",
    )
    parser.add_argument(
        "--sqlite-output",
        default=None,
        dest="sqlite_output",
        metavar="PATH",
        help=(
            "Path for a local SQLite file to write scraped tournaments to "
            "(in addition to the main database). Useful for workflow artifacts."
        ),
    )
    args = parser.parse_args()

    if args.tournament_urls:
        date_from = date_to = None
    else:
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
        + (f" | SQLite output: {args.sqlite_output}" if args.sqlite_output else "")
        + (
            f" | Tournament URLs: {len(args.tournament_urls)}"
            if args.tournament_urls
            else ""
        )
    )

    tournament_urls = [u.strip()
                       for u in (args.tournament_urls or []) if u.strip()]

    if not args.dry_run:
        create_db_and_tables()

    if tournament_urls:
        if args.dry_run:
            logger.info("DRY RUN: tournament URLs provided:")
            for url in tournament_urls:
                logger.info(f"  - {url}")
            return 0
        scrapers = []
    else:
        scrapers = build_scrapers(args.platform, args.include_listfortress)
        if not scrapers:
            logger.error(
                "No scrapers configured for the given --platform value.")
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
    logger.info(
        f"Database contains {len(existing_urls)} existing tournament URL(s).")

    total_saved = 0
    total_skipped = 0
    total_failed = 0
    all_saved_items: list = []

    if tournament_urls:
        for url in tournament_urls:
            clean_url = url.strip()
            if not clean_url:
                continue
            saved, error = _scrape_by_url(
                clean_url, existing_urls, all_saved_items, overwrite=args.overwrite
            )
            if saved:
                total_saved += 1
            elif error:
                total_failed += 1
                logger.error(error)
            else:
                total_skipped += 1
    else:
        independent, dependent = _split_scrapers(scrapers)

        # Stage 1: Run independent scrapers in parallel.
        # Longshanks and Rollbetter pull from completely different domains,
        # so there is no URL collision risk across parallel workers.
        if independent:
            logger.info(
                f"Running {len(independent)} independent scraper(s) in parallel: "
                f"{', '.join(n for n, _ in independent)}"
            )
            with ThreadPoolExecutor(max_workers=len(independent)) as executor:
                future_to_name: dict = {}
                for name, scraper in independent:
                    future = executor.submit(
                        scrape_platform,
                        scraper,
                        name,
                        date_from,
                        date_to,
                        args.max_tournaments,
                        existing_urls,
                        all_saved_items,
                        args.overwrite,
                    )
                    future_to_name[future] = name

                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        saved, skipped = future.result()
                        total_saved += saved
                        total_skipped += skipped
                        logger.info(
                            f"[{name}] Parallel worker finished: "
                            f"{saved} saved, {skipped} skipped."
                        )
                    except Exception as exc:
                        logger.error(
                            f"[{name}] Parallel worker failed: {exc}",
                            exc_info=True,
                        )

        # Stage 2: Run dependent scrapers (ListFortress) sequentially after
        # all independent scrapers have completed, so it can deduplicate
        # against the full set of already-saved tournament URLs.
        if dependent:
            logger.info(
                f"Running {len(dependent)} dependent scraper(s) sequentially: "
                f"{', '.join(n for n, _ in dependent)}"
            )
            for name, scraper in dependent:
                saved, skipped = scrape_platform(
                    scraper,
                    name,
                    date_from,
                    date_to,
                    args.max_tournaments,
                    existing_urls,
                    all_saved_items,
                    args.overwrite,
                )
                total_saved += saved
                total_skipped += skipped
        independent, dependent = _split_scrapers(scrapers)

        # Stage 1: Run independent scrapers in parallel.
        # Longshanks and Rollbetter pull from completely different domains,
        # so there is no URL collision risk across parallel workers.
        if independent:
            logger.info(
                f"Running {len(independent)} independent scraper(s) in parallel: "
                f"{', '.join(n for n, _ in independent)}"
            )
            with ThreadPoolExecutor(max_workers=len(independent)) as executor:
                future_to_name: dict = {}
                for name, scraper in independent:
                    future = executor.submit(
                        scrape_platform,
                        scraper,
                        name,
                        date_from,
                        date_to,
                        args.max_tournaments,
                        existing_urls,
                        all_saved_items,
                        args.overwrite,
                    )
                    future_to_name[future] = name

                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        saved, skipped = future.result()
                        total_saved += saved
                        total_skipped += skipped
                        logger.info(
                            f"[{name}] Parallel worker finished: "
                            f"{saved} saved, {skipped} skipped."
                        )
                    except Exception as exc:
                        logger.error(
                            f"[{name}] Parallel worker failed: {exc}",
                            exc_info=True,
                        )

        # Stage 2: Run dependent scrapers (ListFortress) sequentially after
        # all independent scrapers have completed, so it can deduplicate
        # against the full set of already-saved tournament URLs.
        if dependent:
            logger.info(
                f"Running {len(dependent)} dependent scraper(s) sequentially: "
                f"{', '.join(n for n, _ in dependent)}"
            )
            for name, scraper in dependent:
                saved, skipped = scrape_platform(
                    scraper,
                    name,
                    date_from,
                    date_to,
                    args.max_tournaments,
                    existing_urls,
                    all_saved_items,
                    args.overwrite,
                )
                total_saved += saved
                total_skipped += skipped

    logger.info(
        f"Finished. Saved: {total_saved} new tournament(s), "
        f"skipped: {total_skipped} duplicate(s), "
        f"failed: {total_failed}.")

    if args.sqlite_output and all_saved_items:
        try:
            _write_sqlite(args.sqlite_output, all_saved_items)
        except Exception as exc:
            logger.error(f"Failed to write SQLite artifact: {exc}")
    elif args.sqlite_output and not all_saved_items:
        logger.info("No new tournaments saved; skipping SQLite artifact.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
