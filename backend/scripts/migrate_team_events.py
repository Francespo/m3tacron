"""
Migration: model team events properly.

Adds:
  - tournament.is_team_event boolean
  - playerstanding.is_team_member boolean
  - team_member table (teamstanding_id, playerstanding_id, list_id, list_json)

Then repairs the historical data:
  1. Marks team events (from real teamstanding/teammatch presence).
  2. Re-rosters corrupt team events: for each Longshanks team tournament whose
     playerstanding rows are team-placeholders (player_name == team name), the
     individual member rows are re-scraped from the live ranking tab (the DB
     never stored them) and inserted as PlayerStanding rows with is_team_member
     + team_name, TeamStanding identity rows are (re)built, and team_member
     edges are inserted.
  3. Re-links per-player match rows (player1_id/player2_id/winner_id) against
     the now-populated member rows by name.
  4. Deletes the legacy team-placeholder playerstanding rows.

Usage: docker exec <backend> python -m backend.scripts.migrate_team_events
"""
import logging
import sys

from sqlalchemy import text
from sqlmodel import Session

from ..database import engine
from ..scrapers.longshanks_scraper import LongshanksScraper
from ..models import PlayerStanding, TeamStanding

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def _ensure_schema(session: Session) -> None:
    """Add columns + team_member table if missing (idempotent)."""
    log.info("Ensuring schema (is_team_event / is_team_member / team_member)...")
    session.execute(text("""
        ALTER TABLE tournament ADD COLUMN IF NOT EXISTS is_team_event boolean NOT NULL DEFAULT false
    """))
    session.execute(text("""
        ALTER TABLE playerstanding ADD COLUMN IF NOT EXISTS is_team_member boolean NOT NULL DEFAULT false
    """))
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS team_member (
            id SERIAL PRIMARY KEY,
            teamstanding_id integer NOT NULL REFERENCES teamstanding(id) ON DELETE CASCADE,
            playerstanding_id integer NOT NULL REFERENCES playerstanding(id) ON DELETE CASCADE,
            list_id integer REFERENCES list(id),
            list_json jsonb,
            CONSTRAINT uq_team_member_team_player UNIQUE (teamstanding_id, playerstanding_id)
        )
    """))
    session.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_team_member_player ON team_member(playerstanding_id)
    """))
    session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_team_member_teamstanding ON team_member(teamstanding_id)
    """))
    session.commit()


def _backfill_is_team_event(session: Session) -> int:
    """Mark tournaments that have teamstanding/teammatch rows as team events."""
    log.info("Backfilling tournament.is_team_event...")
    res = session.execute(text("""
        UPDATE tournament t SET is_team_event = true
        WHERE EXISTS (
            SELECT 1 FROM teamstanding ts WHERE ts.tournament_id = t.id
        ) OR EXISTS (
            SELECT 1 FROM teammatch tm WHERE tm.tournament_id = t.id
        )
    """))
    session.commit()
    n = res.rowcount or 0
    log.info(f"Marked {n} tournaments as team events.")
    return n


def _team_events(session: Session) -> list[tuple[int, str, str]]:
    """Return (tournament_id, url, source) for all team events."""
    rows = session.execute(text("""
        SELECT t.id, t.url, t.source FROM tournament t WHERE t.is_team_event = true ORDER BY t.id
    """)).fetchall()
    return [(r[0], r[1], r[2]) for r in rows]


def _is_longshanks(url: str) -> bool:
    return "longshanks.org" in url


def _clean_team_named_members(session: Session, tid: int) -> int:
    """Remove is_team_member rows whose player_name equals a team name in the
    same tournament (stale output from earlier buggy scraper versions)."""
    bad_rows = session.execute(text("""
        SELECT ps.id FROM playerstanding ps
        WHERE ps.tournament_id = :tid AND ps.is_team_member = true
          AND EXISTS (SELECT 1 FROM teamstanding ts
                      WHERE ts.tournament_id = ps.tournament_id
                        AND lower(ts.team_name) = lower(ps.player_name))
    """), {"tid": tid}).fetchall()
    if not bad_rows:
        return 0
    bad_ids = [r[0] for r in bad_rows]
    session.execute(text(
        "DELETE FROM team_member WHERE playerstanding_id = ANY(:ids)"
    ), {"ids": bad_ids})
    session.execute(text(
        "DELETE FROM playerstanding WHERE id = ANY(:ids)"
    ), {"ids": bad_ids})
    session.commit()
    log.info(f"[{tid}] Removed {len(bad_ids)} stale team-named member rows.")
    return len(bad_ids)


def _re_roster_event(session: Session, tid: int, url: str) -> dict:
    """Re-scrape a Longshanks team event's individual ranking tab and insert
    member PlayerStanding rows + team_member edges. Returns stats."""
    import re as _re
    from ..utils.list_keys import get_list_key
    from ..scripts.scrape_tournaments import _persist_list_rows

    m = _re.search(r"/event/(\d+)/", url)
    if not m:
        return {"error": f"cannot parse event id from {url}"}
    event_id = m.group(1)

    subdomain = "xwing-legacy" if "xwing-legacy" in url else "xwing"
    scraper = LongshanksScraper(subdomain=subdomain)
    members = scraper.get_participants(event_id)
    if not members:
        return {"error": "no members scraped"}

    # Guard: only re-roster events the scraper ACTUALLY detects as team
    # events (has a team tab). Some tournaments have teamstanding/teammatch
    # rows in the DB but render as SOLO events on the platform (leagues, etc.)
    # — re-rostering those would create fake team-named members. For them we
    # clear is_team_event and leave the (already correct) individual data.
    if not scraper.is_team_event:
        # Clean any stale team-named member rows first.
        _clean_team_named_members(session, tid)
        session.execute(text(
            "UPDATE tournament SET is_team_event = false WHERE id = :tid"
        ), {"tid": tid})
        session.commit()
        return {"skipped": "not a real team event on the platform; is_team_event cleared"}

    # Build team name -> teamstanding id (identity rows exist from old scrape)
    team_rows = session.execute(text(
        "SELECT id, team_name FROM teamstanding WHERE tournament_id = :tid"
    ), {"tid": tid}).fetchall()
    team_id_by_name = {r[1].lower().strip(): r[0] for r in team_rows}

    # Populate the `list` table for the members' lists and link list_id.
    list_jsons = [p.list_json for p in members if p.list_json]
    lj_sig_to_lid = _persist_list_rows(session, list_jsons)
    for member in members:
        lj = member.list_json
        if lj and isinstance(lj, dict) and lj.get("faction"):
            sig = get_list_key(lj)
            lid = lj_sig_to_lid.get(sig)
            if lid is not None:
                member.list_id = lid

    inserted = 0
    edge_rows = 0
    # Explicit IDs: max playerstanding id + offset
    max_p = session.execute(text("SELECT COALESCE(MAX(id),0) FROM playerstanding")).scalar() or 0
    next_pid = max_p + 1
    # Avoid re-inserting members that already exist for this tournament
    existing_members = set(session.execute(text(
        "SELECT lower(player_name) FROM playerstanding WHERE tournament_id = :tid AND is_team_member = true"
    ), {"tid": tid}).fetchall())
    existing_members = {r[0] for r in existing_members}

    # Self-heal: remove any WRONG team-named member rows (is_team_member rows
    # whose name == a team name — produced by earlier buggy scraper versions)
    # so they don't linger as fake members.
    _clean_team_named_members(session, tid)

    for i, member in enumerate(members):
        mkey = member.player_name.lower().strip()
        if mkey in existing_members:
            continue
        member.id = next_pid + i
        member.tournament_id = tid
        tname = getattr(member, "team_name", None)
        member.is_team_member = True
        tsid = team_id_by_name.get((tname or "").lower().strip()) if tname else None
        if tsid:
            member.team_id = tsid
        session.add(member)
        inserted += 1
    # Flush ALL member rows BEFORE inserting team_member edges so the
    # playerstanding_id FK exists (raw SQL insert runs outside the ORM flush).
    session.flush()
    for member in members:
        mkey = member.player_name.lower().strip()
        if mkey in existing_members:
            continue
        tname = getattr(member, "team_name", None)
        tsid = team_id_by_name.get((tname or "").lower().strip()) if tname else None
        if tsid and member.id is not None:
            session.execute(text(
                "INSERT INTO team_member (teamstanding_id, playerstanding_id, list_id, list_json) "
                "VALUES (:tsid, :pid, :lid, CAST(:lj AS jsonb)) "
                "ON CONFLICT (teamstanding_id, playerstanding_id) DO NOTHING"
            ), {"tsid": tsid, "pid": member.id, "lid": member.list_id,
                "lj": __import__("json").dumps(member.list_json) if member.list_json else "{}"})
            edge_rows += 1
    session.commit()

    # Link the legacy team-named playerstanding rows (team records) to their
    # teamstanding identity and mark them as NOT members.
    linked_team_rows = session.execute(text("""
        UPDATE playerstanding ps
        SET team_id = ts.id, is_team_member = false
        FROM teamstanding ts
        WHERE ps.tournament_id = :tid
          AND ts.tournament_id = :tid
          AND lower(ps.player_name) = lower(ts.team_name)
          AND ps.is_team_member = false
    """), {"tid": tid})
    session.commit()

    return {"members": inserted, "edges": edge_rows, "linked_team_rows": linked_team_rows.rowcount or 0}


def _re_link_matches(session: Session, tid: int) -> int:
    """Link per-player matches in a team event to the member rows.

    The `match` table stores only FKs, not player names, so legacy dangling
    rows cannot be re-linked from the DB alone. The reliable repair is a full
    re-scrape of the event with the fixed scraper (--tournament-url), which
    now resolves per-player game names to member PlayerStanding ids. For the
    migration we simply log; the subsequent overwrite re-scrape handles it.
    """
    log.info(f"Tournament {tid}: match re-link is handled by re-scrape "
             f"(--tournament-url) with the team-aware scraper.")
    return 0


def migrate(only_event_id: int | None = None, skip_reroaster: bool = False) -> None:
    with Session(engine) as session:
        _ensure_schema(session)
        _backfill_is_team_event(session)

        events = _team_events(session)
        if only_event_id is not None:
            events = [e for e in events if e[0] == only_event_id]
        log.info(f"Processing {len(events)} team events.")

        for tid, url, source in events:
            if not _is_longshanks(url):
                log.info(f"[{tid}] Skipping non-Longshanks team event ({source}).")
                continue
            if skip_reroaster:
                # Schema/backfill only — do not touch data.
                continue
            log.info(f"[{tid}] Re-rostering {url} ...")
            stats = _re_roster_event(session, tid, url)
            if stats.get("error"):
                log.warning(f"[{tid}] Re-roster failed: {stats['error']}")
                continue
            if "skipped" in stats:
                log.info(f"[{tid}] {stats['skipped']}")
                continue
            log.info(f"[{tid}] Re-roster: {stats}")
            _re_link_matches(session, tid)
            # Team-named playerstanding rows are kept as team records
            # (is_team_member=false) — the re-roster links them to teamstanding.
            session.execute(text("UPDATE tournament SET is_team_event = true WHERE id = :tid"), {"tid": tid})
            session.commit()

    # Final safety net: no is_team_member row may ever share its name with a
    # team in the same tournament (stale buggy output). Whatever the scraper's
    # team-event detection did, clean these up across the whole DB.
    if not skip_reroaster:
        log.info("Final cleanup: removing any team-named member rows...")
        with Session(engine) as clean_session:
            bad = clean_session.execute(text("""
                SELECT ps.id FROM playerstanding ps
                WHERE ps.is_team_member = true
                  AND EXISTS (SELECT 1 FROM teamstanding ts
                              WHERE ts.tournament_id = ps.tournament_id
                                AND lower(ts.team_name) = lower(ps.player_name))
            """)).fetchall()
            if bad:
                bad_ids = [r[0] for r in bad]
                clean_session.execute(text(
                    "DELETE FROM team_member WHERE playerstanding_id = ANY(:ids)"
                ), {"ids": bad_ids})
                clean_session.execute(text(
                    "DELETE FROM playerstanding WHERE id = ANY(:ids)"
                ), {"ids": bad_ids})
                clean_session.commit()
                log.info(f"Final cleanup removed {len(bad_ids)} team-named member rows.")
            else:
                log.info("Final cleanup: none found.")

    log.info("Migration complete!")


if __name__ == "__main__":
    only = None
    skip = False
    args = sys.argv[1:]
    if "--event" in args:
        i = args.index("--event")
        only = int(args[i + 1])
    if "--skip-reroaster" in args:
        skip = True
    migrate(only_event_id=only, skip_reroaster=skip)
