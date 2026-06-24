"""
Populate the `pilot_ship_mapping` lookup table.

For each known DataSource (XWA, Legacy), iterate every pilot returned by
`load_all_pilots(source)` and INSERT (pilot_xws, source, ship_xws) into
`pilot_ship_mapping`. Conflicts (same pilot_xws+source) are ignored so the
script is safe to re-run.

Run with:
    python -m backend.scripts.populate_pilot_ship_mapping
"""
from __future__ import annotations

import logging
from sqlalchemy import text

from ..database import engine
from ..data_structures.data_source import DataSource
from ..utils.xwing_data.pilots import load_all_pilots

logger = logging.getLogger(__name__)


def _source_value(source: DataSource) -> str:
    """Return the lowercased string value used as the source column key."""
    # DataSource is a StrEnum; str(source) gives the value (e.g. 'xwa', 'legacy').
    return str(source).lower()


def populate() -> None:
    """Fill pilot_ship_mapping from the in-repo pilot data."""
    sources = [DataSource.XWA, DataSource.LEGACY]
    total_inserted = 0

    with engine.begin() as conn:
        for source in sources:
            pilots = load_all_pilots(source)
            source_key = _source_value(source)

            rows = [
                {
                    "pilot_xws": pilot_xws,
                    "source": source_key,
                    "ship_xws": pilot_info.get("ship_xws", "") or "",
                }
                for pilot_xws, pilot_info in pilots.items()
                if pilot_info.get("ship_xws")
            ]

            if not rows:
                print(f"[{source_key}] no pilots with ship_xws found, skipping")
                continue

            # Bulk insert with ON CONFLICT DO NOTHING for idempotency.
            stmt = text(
                """
                INSERT INTO pilot_ship_mapping (pilot_xws, source, ship_xws)
                VALUES (:pilot_xws, :source, :ship_xws)
                ON CONFLICT (pilot_xws, source) DO NOTHING
                """
            )
            conn.execute(stmt, rows)

            print(
                f"[{source_key}] mapped {len(rows)} pilots -> ship_xws "
                f"(total pilots in source: {len(pilots)})"
            )
            total_inserted += len(rows)

    print(f"Done. Rows submitted: {total_inserted}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    populate()
