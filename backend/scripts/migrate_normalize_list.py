"""
Migration: Normalize list storage.
Creates list table, populates from playerstanding, adds list_id FK.

Usage: docker exec <container> python -m backend.scripts.migrate_normalize_list
"""

import json
import logging
import sys

from sqlalchemy import text
from sqlmodel import Session

from ..database import engine
from ..utils.list_keys import get_list_key, get_ship_list

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def normalize_faction(f: str | None) -> str:
    return (f or "").lower().replace(" ", "").replace("-", "")


def migrate():
    with Session(engine) as session:
        # Step 1: Create list table
        log.info("1. Creating list table...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS list (
                id SERIAL PRIMARY KEY,
                canonical_signature TEXT UNIQUE NOT NULL,
                faction TEXT NOT NULL,
                faction_xws_normalized TEXT NOT NULL,
                name TEXT,
                points INTEGER,
                pilot_count INTEGER,
                ship_list TEXT NOT NULL,
                list_json JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        session.commit()

        # Step 2: Add list_id to playerstanding
        log.info("2. Adding list_id column...")
        has_col = session.execute(text("""
            SELECT EXISTS(SELECT 1 FROM information_schema.columns
                          WHERE table_name='playerstanding' AND column_name='list_id')
        """)).scalar()
        if not has_col:
            session.execute(text("ALTER TABLE playerstanding ADD COLUMN list_id INTEGER REFERENCES list(id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_ps_list_id ON playerstanding(list_id)"))
            session.commit()
        log.info("   Done.")

        # Step 3: Scan playerstanding, deduplicate by canonical signature
        log.info("3. Scanning for unique lists...")
        total = session.execute(text("SELECT COUNT(*) FROM playerstanding")).scalar() or 0
        seen: dict[str, dict] = {}
        BATCH = 5000

        for offset in range(0, total, BATCH):
            rows = session.execute(text(
                "SELECT list_json FROM playerstanding "
                "WHERE list_json IS NOT NULL AND list_json::text != '{}' "
                "ORDER BY id LIMIT :lim OFFSET :off"
            ), {"lim": BATCH, "off": offset}).fetchall()
            if not rows:
                break
            for (lj,) in rows:
                if not lj or not isinstance(lj, dict):
                    continue
                sig = get_list_key(lj)
                if sig and sig not in seen:
                    seen[sig] = lj
            log.info(f"   {min(offset+BATCH, total)}/{total} scanned, {len(seen)} unique")

        log.info(f"   Found {len(seen)} unique lists.")

        # Step 4: Insert one by one (reliable, ~30s for 60K)
        log.info("4. Inserting into list table...")
        inserted = 0
        for sig, lj in seen.items():
            faction = lj.get("faction") or "unknown"
            try:
                session.execute(text("""
                    INSERT INTO list (canonical_signature, faction, faction_xws_normalized,
                                     name, points, pilot_count, ship_list, list_json)
                    VALUES (:sig, :fac, :fn, :name, :pts, :pc, :sl, CAST(:lj AS jsonb))
                    ON CONFLICT (canonical_signature) DO NOTHING
                """), {
                    "sig": sig, "fac": faction, "fn": normalize_faction(faction),
                    "name": lj.get("name", ""), "pts": lj.get("points"),
                    "pc": len(lj.get("pilots", [])), "sl": get_ship_list(lj),
                    "lj": json.dumps(lj),
                })
                inserted += 1
            except Exception as e:
                log.error(f"   INSERT failed: {e}")
                session.rollback()
                continue

            if inserted % 5000 == 0:
                session.commit()
                log.info(f"   {inserted}/{len(seen)} inserted")

        session.commit()
        count = session.execute(text("SELECT COUNT(*) FROM list")).scalar()
        log.info(f"   list table: {count} rows")

        # Step 5: Populate list_id via Python loop
        log.info("5. Populating list_id...")
        sig_to_id = {
            row[1]: row[0]
            for row in session.execute(text("SELECT id, canonical_signature FROM list")).fetchall()
        }
        log.info(f"   Loaded {len(sig_to_id)} mappings")

        updated = 0
        for offset in range(0, total, BATCH):
            rows = session.execute(text(
                "SELECT id, list_json FROM playerstanding "
                "WHERE list_id IS NULL AND list_json IS NOT NULL "
                "ORDER BY id LIMIT :lim OFFSET :off"
            ), {"lim": BATCH, "off": offset}).fetchall()
            if not rows:
                break
            for ps_id, lj in rows:
                if not lj or not isinstance(lj, dict):
                    continue
                sig = get_list_key(lj)
                lid = sig_to_id.get(sig)
                if lid:
                    session.execute(text(
                        "UPDATE playerstanding SET list_id = :lid WHERE id = :pid"
                    ), {"lid": lid, "pid": ps_id})
                    updated += 1
            session.commit()
            log.info(f"   {updated} matched so far")

        # Step 6: Verify
        log.info("6. Verification...")
        list_count = session.execute(text("SELECT COUNT(*) FROM list")).scalar()
        ps_with = session.execute(text("SELECT COUNT(*) FROM playerstanding WHERE list_id IS NOT NULL")).scalar()
        ps_null = session.execute(text("SELECT COUNT(*) FROM playerstanding WHERE list_id IS NULL")).scalar()
        log.info(f"   list table: {list_count} rows")
        log.info(f"   playerstanding with list_id: {ps_with}")
        log.info(f"   playerstanding without list_id: {ps_null}")

        session.execute(text("""
            INSERT INTO scrape_meta (key, value) VALUES ('data_version', 'norm_v1')
            ON CONFLICT (key) DO UPDATE SET value = 'norm_v1'
        """))
        session.commit()
        log.info("Migration complete!")


if __name__ == "__main__":
    migrate()
