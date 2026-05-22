"""
Standalone deduplication script for M3taCron.

Runs cross-platform duplicate detection on specified tournament IDs or ID ranges,
and optionally prunes lower-priority duplicates.

Priority order (highest to lowest):
    1. longshanks_25 / longshanks_legacy
    2. rollbetter_amg / rollbetter_xwa
    3. listfortress

Usage:
    # Report duplicates only
    python -m backend.scripts.run_deduplication --ids 23 24 25

    # With ranges
    python -m backend.scripts.run_deduplication --ids 23:48 12 90:100

    # Prune lower-priority duplicates (destructive!)
    python -m backend.scripts.run_deduplication --ids 23:48 --prune
"""

import argparse
import logging
import sys

from sqlmodel import Session, select

from ..database import engine
from ..models import Tournament, PlayerStanding, Match, TeamMatch, TeamStanding
from .dedup_utils import check_for_duplicates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Priority: lower number = higher priority
PRIORITY_ORDER: dict[str, int] = {
    "longshanks_25": 0,
    "longshanks_legacy": 0,
    "rollbetter_amg": 1,
    "rollbetter_xwa": 1,
    "listfortress": 2,
}


def _resolve_source(url: str) -> str:
    """Map a tournament URL to its source key for priority comparison."""
    url_lower = url.lower()
    if "xwing.longshanks.org" in url_lower:
        return "longshanks_25"
    if "xwing-legacy.longshanks.org" in url_lower:
        return "longshanks_legacy"
    if "rollbetter.gg" in url_lower:
        return "rollbetter_amg"
    if "listfortress.com" in url_lower:
        return "listfortress"
    return "unknown"


def _resolve_ids(raw_ids: list[str]) -> list[int]:
    """Parse a list that may contain ranges like '23:48' into flat ints."""
    result: list[int] = []
    for item in raw_ids:
        if ":" in item:
            parts = item.split(":", 1)
            try:
                start, end = int(parts[0]), int(parts[1])
                result.extend(range(start, end + 1))
            except ValueError:
                logger.warning(f"Skipping invalid range: {item}")
        else:
            try:
                result.append(int(item))
            except ValueError:
                logger.warning(f"Skipping invalid id: {item}")
    return sorted(set(result))


def _delete_tournament(session: Session, t: Tournament) -> None:
    """Delete a tournament and all its associated data."""
    logger.info(f"Deleting lower-priority duplicate: {t.name} ({t.url})")
    session.exec(select(TeamMatch).where(TeamMatch.tournament_id == t.id)).delete()
    session.exec(select(Match).where(Match.tournament_id == t.id)).delete()
    session.exec(select(PlayerStanding).where(PlayerStanding.tournament_id == t.id)).delete()
    session.exec(select(TeamStanding).where(TeamStanding.tournament_id == t.id)).delete()
    session.exec(select(Tournament).where(Tournament.id == t.id)).delete()
    session.commit()


def deduplicate_ids(ids: list[int], prune: bool = False) -> None:
    """Check each tournament id against the database for duplicates.

    When prune=True, the lower-priority duplicate is deleted.
    """
    with Session(engine) as session:
        for t_id in ids:
            t = session.exec(select(Tournament).where(Tournament.id == t_id)).first()
            if not t:
                logger.warning(f"Tournament {t_id} not found. Skipping.")
                continue

            players = list(
                session.exec(
                    select(PlayerStanding).where(PlayerStanding.tournament_id == t_id)
                ).all()
            )
            dup = check_for_duplicates(session, t, players)
            if not dup or dup.id == t.id:
                continue

            t_source = _resolve_source(t.url)
            dup_source = _resolve_source(dup.url)
            t_priority = PRIORITY_ORDER.get(t_source, 99)
            dup_priority = PRIORITY_ORDER.get(dup_source, 99)

            logger.info(
                f"Duplicate: [{t_source}] {t.name} (id={t.id}, prio={t_priority}) "
                f"== [{dup_source}] {dup.name} (id={dup.id}, prio={dup_priority})"
            )

            if prune:
                if t_priority < dup_priority:
                    _delete_tournament(session, dup)
                elif dup_priority < t_priority:
                    _delete_tournament(session, t)
                else:
                    logger.info(
                        f"Equal priority ({t_source}), keeping both. "
                        "Manual review recommended."
                    )
            else:
                if t_priority > dup_priority:
                    logger.info(
                        f"  -> {t.name} (id={t.id}) is lower priority; "
                        f"prefer {dup.name} (id={dup.id})"
                    )
                elif dup_priority > t_priority:
                    logger.info(
                        f"  -> {dup.name} (id={dup.id}) is lower priority; "
                        f"prefer {t.name} (id={t.id})"
                    )
                else:
                    logger.info("  -> Equal priority, manual review recommended.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect cross-platform duplicate tournaments.",
    )
    parser.add_argument(
        "--ids",
        type=str,
        nargs="+",
        required=True,
        help="Tournament IDs or ranges (e.g. 23:48 12 90:100).",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete lower-priority duplicates (destructive).",
    )
    args = parser.parse_args()

    resolved = _resolve_ids(args.ids)
    if not resolved:
        logger.error("No valid tournament IDs provided.")
        return 1

    logger.info(
        "Checking %d tournament(s) for duplicates. Prune=%s",
        len(resolved),
        args.prune,
    )
    deduplicate_ids(resolved, prune=args.prune)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
