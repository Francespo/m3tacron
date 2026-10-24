"""Normalized pilot/upgrade index over ``list.list_json``.

Why
---
Every analytics query used to open ``list.list_json`` (55.7k lists, ~118 MB)
and unnest its pilots/upgrades with ``jsonb_array_elements``. That is the
dominant cost of a cold ships/cards/detail aggregation (3–10 s) and of the
cache warm-up.

This module keeps two flat tables derived from the JSON:

  ``list_pilot``         (list_id, pilot_xws)                  ~231k rows
  ``list_pilot_upgrade`` (list_id, pilot_xws, upgrade_xws)      ~556k rows

Aggregations join these instead of parsing JSON. The JSON stays the source of
truth: the tables are rebuilt from it once per ``data_version``.

Lifecycle
---------
* ``ensure_list_index(version)`` rebuilds both tables in a single transaction
  (readers keep the previous snapshot until it commits) and records the version
  in ``list_index_meta``. It runs inside the cache warm-up, which already holds
  the cross-process advisory lock, so only one worker rebuilds.
* ``list_index_ready()`` tells the query builders which path to use. If the
  tables are missing, empty, stale, or the rebuild failed, every query falls
  back to the JSON unnest — i.e. today's behaviour, never broken.
* ``list_pilots_cte()`` / ``list_pilot_upgrades_cte()`` return the same CTE
  name for both paths, so the calling SQL is identical apart from the source.
"""

from __future__ import annotations

import threading
import time

from sqlalchemy import text

from .cache import current_version
from .database import engine

# Re-check list_index_meta at most this often. One tiny SELECT per interval.
_READY_CHECK_INTERVAL = 10.0

_lock = threading.Lock()
_checked_at: float = 0.0
_ready_version: str | None = None


def _stored_version() -> str | None:
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT data_version FROM list_index_meta WHERE id = 1")
            ).fetchone()
        return row[0] if row else None
    except Exception:
        return None


def list_index_ready() -> bool:
    """True when the derived tables match the data version being served."""
    global _checked_at, _ready_version
    version = current_version()
    if not version:
        return False
    now = time.monotonic()
    with _lock:
        if now - _checked_at < _READY_CHECK_INTERVAL:
            return _ready_version == version
        _checked_at = now
    stored = _stored_version()
    with _lock:
        _ready_version = stored
    return stored == version


def ensure_list_index(version: str | None) -> bool:
    """Build the derived tables if they do not match ``version``.

    Returns True when the tables are ready for ``version``. Never raises: on
    failure the callers fall back to the JSON unnest.
    """
    global _checked_at, _ready_version
    if not version:
        return False
    if _stored_version() == version:
        with _lock:
            _checked_at = time.monotonic()
            _ready_version = version
        return True

    t0 = time.time()
    try:
        with engine.begin() as conn:
            # DELETE + INSERT in one transaction: concurrent readers keep the
            # previous snapshot (MVCC) and see either generation, never a mix.
            conn.execute(text("DELETE FROM list_pilot"))
            conn.execute(text("DELETE FROM list_pilot_upgrade"))
            conn.execute(
                text(
                    """
                    INSERT INTO list_pilot (list_id, entry_idx, pilot_xws)
                    SELECT l.id, p.ord, p.value->>'id'
                    FROM list l
                    JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') WITH ORDINALITY AS p(value, ord) ON true
                    WHERE p.value->>'id' IS NOT NULL
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO list_pilot_upgrade (list_id, entry_idx, pilot_xws, upgrade_xws)
                    SELECT l.id, p.ord, p.value->>'id', u
                    FROM list l
                    JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') WITH ORDINALITY AS p(value, ord) ON true
                    JOIN jsonb_array_elements_text(
                        CASE
                            WHEN jsonb_typeof(p.value->'upgrades') = 'array' THEN p.value->'upgrades'
                            WHEN jsonb_typeof(p.value->'upgrades') = 'object' THEN
                                COALESCE(
                                    (SELECT jsonb_agg(v)
                                     FROM jsonb_each(p.value->'upgrades') e,
                                          jsonb_array_elements_text(e.value) v
                                     WHERE jsonb_typeof(e.value) = 'array'),
                                    '[]'::jsonb
                                )
                            ELSE '[]'::jsonb
                        END
                    ) u ON true
                    WHERE p.value->>'id' IS NOT NULL AND u IS NOT NULL
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO list_index_meta (id, data_version, rebuilt_at)
                    VALUES (1, :version, now())
                    ON CONFLICT (id) DO UPDATE
                       SET data_version = EXCLUDED.data_version,
                           rebuilt_at = EXCLUDED.rebuilt_at
                    """
                ),
                {"version": version},
            )
        try:
            with engine.begin() as conn:
                conn.execute(text("ANALYZE list_pilot"))
                conn.execute(text("ANALYZE list_pilot_upgrade"))
        except Exception:
            pass
        with _lock:
            _checked_at = time.monotonic()
            _ready_version = version
        print(f"[list-index] rebuilt for data_version {version} in {time.time()-t0:.1f}s")
        return True
    except Exception as exc:
        print(f"[list-index] rebuild failed (falling back to JSON): {exc}")
        with _lock:
            _checked_at = time.monotonic()
            _ready_version = None
        return False


_PILOTS_CTE_FAST = (
    "list_pilots AS (SELECT list_id, entry_idx, pilot_xws FROM list_pilot)"
)

_PILOTS_CTE_JSON = """
list_pilots AS (
    SELECT l.id AS list_id, p.ord AS entry_idx, p.value->>'id' AS pilot_xws
    FROM list l
    JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') WITH ORDINALITY AS p(value, ord) ON true
    WHERE p.value->>'id' IS NOT NULL
)
"""

_UPGRADES_CTE_FAST = """
list_pilot_upgrades AS (
    SELECT list_id, entry_idx, pilot_xws, upgrade_xws FROM list_pilot_upgrade
)
"""

_UPGRADES_CTE_JSON = """
list_pilot_upgrades AS (
    SELECT l.id AS list_id, p.ord AS entry_idx, p.value->>'id' AS pilot_xws, u AS upgrade_xws
    FROM list l
    JOIN jsonb_array_elements(l.list_json::jsonb->'pilots') WITH ORDINALITY AS p(value, ord) ON true
    JOIN jsonb_array_elements_text(
        CASE
            WHEN jsonb_typeof(p.value->'upgrades') = 'array' THEN p.value->'upgrades'
            WHEN jsonb_typeof(p.value->'upgrades') = 'object' THEN
                COALESCE(
                    (SELECT jsonb_agg(v)
                     FROM jsonb_each(p.value->'upgrades') e,
                          jsonb_array_elements_text(e.value) v
                     WHERE jsonb_typeof(e.value) = 'array'),
                    '[]'::jsonb
                )
            ELSE '[]'::jsonb
        END
    ) u ON true
    WHERE p.value->>'id' IS NOT NULL AND u IS NOT NULL
)
"""


def list_pilots_cte() -> str:
    """CTE body exposing (list_id, pilot_xws), from the index or the JSON."""
    return _PILOTS_CTE_FAST if list_index_ready() else _PILOTS_CTE_JSON


def list_pilot_upgrades_cte() -> str:
    """CTE body exposing (list_id, pilot_xws, upgrade_xws)."""
    return _UPGRADES_CTE_FAST if list_index_ready() else _UPGRADES_CTE_JSON
