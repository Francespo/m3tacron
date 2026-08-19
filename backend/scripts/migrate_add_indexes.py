"""
Migration: Add performance indexes on the analytics hot path.

The heavy aggregation queries in backend/analytics/* JOIN
`playerstanding ps` to `tournament t` and `list l`, filtering on
`t.date`, `t.source`, `t.format`, `ps.faction_xws_normalized`, and
`l.faction_xws_normalized`. With 96K+ standing rows these filters ran
as seq scans / hash joins on every cache miss.

This script creates the supporting indexes. Every statement is
`CREATE INDEX IF NOT EXISTS`, so the script is idempotent — safe to
re-run at any time, including after a partial failure.

Usage:
    python -m backend.scripts.migrate_add_indexes
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


# (index_name, table, column) — mirrors the `index=True` flags added to
# backend/models.py plus the denormalized faction columns used in WHERE.
INDEXES: list[tuple[str, str, str]] = [
    ("ix_playerstanding_tournament_id", "playerstanding", "tournament_id"),
    ("ix_tournament_date", "tournament", "date"),
    ("ix_tournament_source", "tournament", "source"),
    ("ix_tournament_format", "tournament", "format"),
    ("ix_playerstanding_faction_xws_normalized", "playerstanding", "faction_xws_normalized"),
    ("ix_list_faction_xws_normalized", "list", "faction_xws_normalized"),
]


def migrate() -> None:
    with Session(engine) as session:
        for index_name, table, column in INDEXES:
            # Idempotent: no-op when the index already exists.
            session.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS {index_name} "
                    f"ON {table} ({column})"
                )
            )
            # Commit per index so partial progress is durable on long runs.
            session.commit()
            log.info(f"   {index_name} ON {table}({column}) ✓")

        log.info("Migration complete. All indexes are in place.")


if __name__ == "__main__":
    migrate()
