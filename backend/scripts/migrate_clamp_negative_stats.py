"""
Migration: Clamp negative stats to 0.

Older `PlayerStanding` rows in the database may still have `swiss_wins`,
`swiss_losses`, and `swiss_rank` set to -1 (the legacy default for
"unknown" / "not applicable"). COALESCE(ps.X, 0) only converts NULL to 0,
not negative values, so aggregation queries that sum across rows were
producing negative game/win counts.

This script:
  1. Updates `playerstanding` rows where these fields are < 0 to 0.
  2. Reports the number of rows updated per column.
  3. Is idempotent — safe to re-run. If all values are already >= 0, the
     UPDATE statements affect 0 rows.

The same fix is applied to `teamstanding` (which had the same legacy
defaults). `match.player1_score` / `match.player2_score` /
`teammatch.team1_score` / `teammatch.team2_score` are intentionally
left alone — they are sentinel values that mean "not yet scored" and
are handled at the API/formatter layer.

Usage:
    python -m backend.scripts.migrate_clamp_negative_stats
"""

import logging
import sys

from sqlalchemy import text
from sqlmodel import Session

from ..database import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# (table, column) pairs to clamp. The list mirrors the model defaults
# that used to be -1 and have since been changed to 0 in
# backend/models.py.
TARGETS: list[tuple[str, str]] = [
    ("playerstanding", "swiss_wins"),
    ("playerstanding", "swiss_losses"),
    ("playerstanding", "swiss_rank"),
    ("teamstanding", "swiss_wins"),
    ("teamstanding", "swiss_losses"),
    ("teamstanding", "swiss_rank"),
]


def migrate() -> None:
    with Session(engine) as session:
        total_updated = 0
        for table, column in TARGETS:
            # Idempotent: matches nothing when all values are already >= 0.
            result = session.execute(
                text(
                    f"UPDATE {table} SET {column} = 0 "
                    f"WHERE {column} < 0"
                )
            )
            # SQLAlchemy 2.0 exposes rowcount on the underlying CursorResult.
            # `getattr` keeps both static and dynamic (e.g. async) Result
            # implementations happy.
            count = getattr(result, "rowcount", 0) or 0
            total_updated += count
            log.info(f"   {table}.{column}: {count} row(s) updated")
            # Commit per column so partial progress is durable on long runs.
            session.commit()

        log.info(f"Migration complete. Total rows updated: {total_updated}")


if __name__ == "__main__":
    migrate()
