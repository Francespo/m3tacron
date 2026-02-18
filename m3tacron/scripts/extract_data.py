"""
Data Extraction Script.

Given tournament URLs, runs the appropriate scraper for each and
persists results (Tournament, PlayerResult, Match) to a SQLite database.

Usage:
    python -m m3tacron.scripts.extract_data \
        --db scraped_data.db \
        "https://xwing.longshanks.org/event/31565/"

    python -m m3tacron.scripts.extract_data \
        --file urls.txt --db scraped_data.db --format xwa
"""
import argparse
import logging
import sys
from sqlmodel import Session, create_engine, SQLModel, select, delete

from m3tacron.backend.models import Tournament, PlayerResult, Match
from m3tacron.backend.data_structures.formats import Format
from m3tacron.backend.data_structures.round_types import RoundType
from m3tacron.backend.data_structures.scenarios import Scenario
from m3tacron.backend.scrapers.longshanks_scraper import LongshanksScraper
from m3tacron.backend.scrapers.rollbetter_scraper import RollbetterScraper
from m3tacron.backend.scrapers.listfortress_scraper import ListFortressScraper
from m3tacron.backend.domain.deduplication import DedupService
from m3tacron.backend.data_structures.platforms import Platform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("extract_data")


def _get_scraper(url: str):
    """Determine the correct scraper from a tournament URL.

    Returns:
        (scraper_instance, tournament_id) or (None, None) if unknown.
    """
    if "rollbetter.gg" in url:
        tid = url.rstrip("/").split("/")[-1]
        return RollbetterScraper(), tid

    if "longshanks.org" in url:
        subdomain = "xwing"
        if "xwing-legacy" in url:
            subdomain = "xwing-legacy"
        tid = url.rstrip("/").split("/")[-1]
        return LongshanksScraper(subdomain=subdomain), tid

    if "listfortress.com" in url:
        tid = url.rstrip("/").split("/")[-1]
        return ListFortressScraper(), tid

    return None, None


def _calculate_and_update_stats(session, tournament):
    """Recalculate player tie breakers based on match data.

    Legacy (2.0) -> MOV based on Score Differential (Score - OppScore).
    Standard (2.5) -> MP based on Score Sum (Score).
    """
    try:
        matches = session.exec(
            select(Match).where(Match.tournament_id == tournament.id)
        ).all()
        players = session.exec(
            select(PlayerResult).where(PlayerResult.tournament_id == tournament.id)
        ).all()

        player_map = {p.id: p for p in players}
        tb_stats = {p.id: 0 for p in players}

        # Determine calculation method
        legacy_formats = [Format.LEGACY_X2PO, Format.LEGACY_XLC, Format.FFG]
        fmt_val = tournament.format
        if hasattr(fmt_val, "value"):
            fmt_val = fmt_val.value
        is_legacy = fmt_val in [f.value for f in legacy_formats]

        for m in matches:
            if not m.player1_id or not m.player2_id:
                continue
            s1 = max(0, m.player1_score)
            s2 = max(0, m.player2_score)

            if is_legacy:
                diff = s1 - s2
                if m.player1_id in tb_stats:
                    tb_stats[m.player1_id] += diff
                if m.player2_id in tb_stats:
                    tb_stats[m.player2_id] -= diff
            else:
                if m.player1_id in tb_stats:
                    tb_stats[m.player1_id] += s1
                if m.player2_id in tb_stats:
                    tb_stats[m.player2_id] += s2

        # Update DB
        win_pts = 3
        draw_pts = 1
        count = 0

        for pid, val in tb_stats.items():
            if pid in player_map:
                p = player_map[pid]
                p.swiss_tie_breaker_points = val
                if not is_legacy:
                    current_ep = p.swiss_event_points if p.swiss_event_points is not None else 0
                    calc_ep = (p.swiss_wins * win_pts) + (p.swiss_draws * draw_pts)
                    if current_ep == 0 or current_ep is None:
                        p.swiss_event_points = calc_ep
                session.add(p)
                count += 1

        session.commit()
        mode = "Legacy/Diff" if is_legacy else "Standard/Sum"
        logger.info(f"Stats recalculated for {count} players (Mode: {mode}).")

    except Exception as e:
        logger.error(f"Stats Calculation Error: {e}")


def _resolve_player_id(name: str, player_map: dict[str, int]) -> int | None:
    """Resolve player ID from name using exact, case-insensitive, or substring matching."""
    if not name:
        return None
    
    # Robust normalization: collapse all whitespace (NBSP, double space, etc) to single space
    clean = " ".join(name.split())
    
    # 1. Exact match
    if clean in player_map:
        return player_map[clean]
        
    # 2. Case-insensitive match
    clean_lower = clean.lower()
    if clean_lower in player_map:
        return player_map[clean_lower]
        
    # 3. Substring match (Ranking name contains Match name)
    candidates = []
    for key, pid in player_map.items():
        if key.lower().startswith(clean_lower):
             candidates.append(pid)
             
    if len(candidates) == 1:
        return candidates[0]
        
    return None

def run_url(url: str, engine, format_filter: str | None = None) -> bool:
    """Scrape a single tournament URL and persist to DB.

    Args:
        url: Tournament URL.
        engine: SQLAlchemy engine.
        format_filter: Optional format string. If set, skip tournaments
                       whose inferred format doesn't match.

    Returns:
        True if a NEW tournament was successfully added to the database.
        False if it was a duplicate, already existed, or encountered an error.
    """
    logger.info(f"--- Processing: {url} ---")

    scraper, tid = _get_scraper(url)
    if not scraper:
        logger.error(f"Unknown URL type: {url}")
        return False

    SQLModel.metadata.create_all(engine)

    import traceback
    try:
        with Session(engine) as session:
            # 1. Get participants (triggers format inference via XWS)
            players = scraper.get_participants(tid)
            logger.info(f"Scraped {len(players)} players.")

            # 1a. Infer format from XWS (Critical: User Requirement)
            from m3tacron.backend.data_structures.formats import infer_format_from_xws, Format
            inferred_format = None
            
            # Check first 20 players for valid lists
            for pl in players[:20]:
                if pl.list_json:
                    # Depending on scraper, list_json might be the XWS dict or wrapped
                    # BaseScraper/ListFortressScraper usually puts XWS dict in list_json
                    inferred = infer_format_from_xws(pl.list_json)
                    if inferred != Format.OTHER:
                        inferred_format = inferred
                        logger.info(
                            f"XWS-inferred format {inferred.value} "
                            f"from player {pl.player_name}"
                        )
                        break
            
            if not inferred_format:
                logger.warning("Could not infer format from XWS. Defaulting to OTHER.")
                inferred_format = Format.OTHER

            # 2. Get tournament metadata
            t_data = scraper.get_tournament_data(tid, inferred_format=inferred_format)
            logger.info(
                f"Tournament: {t_data.name} | {t_data.date} | "
                f"Format: {t_data.format}"
            )

            # Fine-grained format filter (Stage 2)
            if format_filter:
                inferred = t_data.format
                inferred_val = inferred.value if hasattr(inferred, "value") else inferred
                if inferred_val != format_filter:
                    logger.info(
                        f"SKIPPED: format mismatch "
                        f"(want={format_filter}, got={inferred_val})"
                    )
                    return False

            # 3. Persist tournament
            
            # 3a. ID Collision Check
            existing_t = session.get(Tournament, t_data.id)
            if existing_t and existing_t.platform != t_data.platform:
               logger.error(
                   f"ID Collision detected! ID {t_data.id} exists for {existing_t.platform} "
                   f"but trying to save for {t_data.platform}. Skipping."
               )
               return False

            added_new = True
            if existing_t:
                added_new = False
                logger.info(f"Tournament {t_data.id} already exists in database. Updating.")

            # 3b. Deduplication Check
            dedup_service = DedupService()
            # Fetch candidates within +/- 2 days window
            # We can't use date math in SQLModel easily with sqlite sometimes, fetching wider range or all
            # Optimization: Fetch only id, name, date, platform for efficiency if DB matches
            # For now, fetching all is fine for scale < 10k
            candidates = session.exec(select(Tournament)).all()
            
            # Need candidate players for deep check? 
            # This is expensive (n+1). For this implementation, pass None for candidate_players_map 
            # and rely on Name/Date matching unless we want to do a heavy load.
            # Plan: Only load players for high-name-match candidates if needed?
            # Or just rely on dedup_service to be fast with partial data.
            
            duplicate = dedup_service.find_duplicate(t_data, candidates)
            if duplicate:
                logger.warning(
                    f"[DEDUP] Tournament '{t_data.name}' ({t_data.platform}) "
                    f"appears to be a duplicate of '{duplicate.name}' ({duplicate.platform}). "
                    f"Proceeding with save, but flagging."
                )
                # Logic to Link/Merge could go here in future.
                added_new = False

            session.merge(t_data)
            session.commit()
            t_data = session.get(Tournament, t_data.id)

            # 4. Persist players
            player_map = {}
            for p in players:
                p.tournament_id = t_data.id
                existing = session.exec(
                    select(PlayerResult).where(
                        PlayerResult.tournament_id == t_data.id,
                        PlayerResult.player_name == p.player_name
                    )
                ).first()

                if existing:
                    # Update existing record
                    for field in [
                        "team_name", "swiss_rank", "swiss_event_points",
                        "swiss_tie_breaker_points", "swiss_wins",
                        "swiss_losses", "swiss_draws", "cut_rank",
                        "cut_wins", "cut_losses", "cut_draws",
                        "cut_event_points", "cut_tie_breaker_points",
                        "list_json",
                    ]:
                        setattr(existing, field, getattr(p, field))
                    session.add(existing)
                    session.commit()
                    session.refresh(existing)
                    p_bound = existing
                else:
                    session.add(p)
                    session.commit()
                    session.refresh(p)
                    p_bound = p

                # Normalize name for map
                if p.player_name:
                    clean_name = " ".join(p.player_name.split())
                    player_map[clean_name] = p_bound.id
                    player_map[clean_name.lower()] = p_bound.id

            logger.info(f"Mapped {len(player_map) // 2} players.")

            # 5. Persist matches (clear old ones first to avoid dupes)
            session.exec(
                delete(Match).where(Match.tournament_id == t_data.id)
            )
            session.commit()

            matches = scraper.get_matches(tid)
            logger.info(f"Scraped {len(matches)} matches.")

            saved_matches = 0
            for m_data in matches:
                p1_name = m_data.get("p1_name_temp") or m_data.get("player1_name")
                p2_name = m_data.get("p2_name_temp") or m_data.get("player2_name")

                # Resolve player IDs
                p1_id = _resolve_player_id(p1_name, player_map)
                p2_id = _resolve_player_id(p2_name, player_map)

                if not p1_id:
                    continue

                # Enum serialization
                r_type = m_data["round_type"]
                if hasattr(r_type, "value"):
                    r_type = r_type.value
                scen = m_data["scenario"]
                if hasattr(scen, "value"):
                    scen = scen.value

                m = Match(
                    tournament_id=t_data.id,
                    round_number=m_data["round_number"],
                    round_type=r_type,
                    scenario=scen,
                    player1_id=p1_id,
                    player2_id=p2_id,
                    player1_score=m_data["player1_score"],
                    player2_score=m_data["player2_score"],
                    is_bye=m_data["is_bye"],
                    p1_name_temp=p1_name,
                    p2_name_temp=p2_name,
                )

                # Winner assignment
                winner_name = m_data.get("winner_name_temp")
                if winner_name:
                    w_clean = winner_name.strip().lower()
                    p1_check = p1_name.strip().lower() if p1_name else ""
                    p2_check = p2_name.strip().lower() if p2_name else ""
                    if w_clean == p1_check:
                        m.winner_id = p1_id
                    elif w_clean == p2_check:
                        m.winner_id = p2_id

                # Fallback: score-based winner
                if not m.winner_id and m.player1_score != m.player2_score:
                    if m.player1_score > m.player2_score:
                        m.winner_id = p1_id
                    else:
                        m.winner_id = p2_id

                session.add(m)
                saved_matches += 1

            session.commit()
            logger.info(f"Saved {saved_matches} matches to DB.")

            # 6. Recalculate stats for Rollbetter
            if "rollbetter" in scraper.__class__.__name__.lower():
                logger.info("Recalculating tie breakers from match data...")
                _calculate_and_update_stats(session, t_data)
            
            return added_new

    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Extract tournament data from URLs and persist to DB."
    )
    parser.add_argument(
        "urls", nargs="*",
        help="Tournament URLs to scrape."
    )
    parser.add_argument(
        "--file", default=None,
        help="Path to file with one URL per line."
    )
    parser.add_argument(
        "--db", default="scraped_data.db",
        help="SQLite database path. Default: scraped_data.db"
    )
    parser.add_argument(
        "--format", default=None,
        choices=[f.value for f in Format],
        help="Optional fine-grained format filter. "
             "Tournaments whose inferred format doesn't match will be skipped."
    )

    args = parser.parse_args()

    # Collect URLs
    urls = list(args.urls)
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        urls.append(line)
        except FileNotFoundError:
            logger.error(f"File not found: {args.file}")
            sys.exit(1)

    if not urls:
        logger.error("No URLs provided. Use positional args or --file.")
        sys.exit(1)

    engine = create_engine(f"sqlite:///{args.db}")
    logger.info(f"Database: {args.db} | URLs: {len(urls)} | Format filter: {args.format}")

    for url in urls:
        run_url(url, engine, format_filter=args.format)

    logger.info("Done.")


if __name__ == "__main__":
    main()
