"""
Migration: add faction column to pilot_ship_mapping.

The ships-page faction toggle needs to attribute a ship's lists to the
faction the ship actually played as. The `list.faction` column is the
faction of the whole squad, which is wrong for cross-faction lists
(e.g. "battle of" squads mixing Republic + Rebel + Empire ships): an
ARC-170 in a mixed squad would be mis-attributed to the list's faction
(or "unknown" when the list has no faction at all).

Each pilot in the xwing-data manifest has a canonical `faction`, so we
denormalize it onto pilot_ship_mapping(pilot_xws, source, ship_xws) as
`faction`. Idempotent: adds the column if missing, then backfills any
NULLs from the in-repo pilot manifest.

Usage:
    python -m backend.scripts.migrate_pilot_ship_mapping_faction
"""

import logging
import sys

from sqlalchemy import text
from sqlmodel import Session

from ..database import engine
from ..data_structures.data_source import DataSource
from ..utils.xwing_data.pilots import load_all_pilots

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def migrate() -> None:
    with Session(engine) as session:
        # 1. Add the column if it doesn't exist.
        has_col = session.execute(text("""
            SELECT EXISTS(SELECT 1 FROM information_schema.columns
                          WHERE table_name='pilot_ship_mapping' AND column_name='faction')
        """)).scalar()
        if not has_col:
            session.execute(text("ALTER TABLE pilot_ship_mapping ADD COLUMN faction TEXT"))
            session.commit()
            log.info("   Added column pilot_ship_mapping.faction")
        else:
            log.info("   Column pilot_ship_mapping.faction already exists")

        # 2. Backfill NULL factions from the in-repo pilot manifest.
        total = session.execute(text("SELECT COUNT(*) FROM pilot_ship_mapping WHERE faction IS NULL")).scalar() or 0
        if total == 0:
            log.info("   No NULL factions to backfill")
            session.close()
            return

        pilots = load_all_pilots(DataSource.XWA) | load_all_pilots(DataSource.LEGACY)
        rows = session.execute(text(
            "SELECT pilot_xws, source FROM pilot_ship_mapping WHERE faction IS NULL"
        )).fetchall()

        updated = 0
        for pilot_xws, source in rows:
            pilot = pilots.get(pilot_xws)
            if not pilot or not pilot.get("faction"):
                continue
            session.execute(text(
                "UPDATE pilot_ship_mapping SET faction = :faction "
                "WHERE pilot_xws = :pilot_xws AND source = :source"
            ), {"faction": pilot["faction"], "pilot_xws": pilot_xws, "source": source})
            updated += 1

        session.commit()
        log.info(f"   Backfilled {updated}/{total} NULL factions")

        remaining = session.execute(text("SELECT COUNT(*) FROM pilot_ship_mapping WHERE faction IS NULL")).scalar()
        log.info(f"   Remaining NULL factions: {remaining}")
        log.info("Migration complete!")


if __name__ == "__main__":
    migrate()
