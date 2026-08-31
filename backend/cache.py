"""
In-memory cache with scrape-triggered invalidation.

Cache entries are invalidated when the data_version in scrape_meta changes
(after each scraper run). Between scrapes, all cache hits return instantly.

Usage:
    from backend.cache import get_cached_or_compute

    result = get_cached_or_compute(
        "lists|xwa|rebel|0",
        lambda: aggregate_list_stats(filters)
    )
"""
import threading
import time
from typing import Callable, TypeVar

T = TypeVar("T")

# Configuration
CACHE_CHECK_INTERVAL = 5.0  # seconds between version checks
MAX_CACHE_ENTRIES = 1000

# Internal state
_lock = threading.Lock()
_cache: dict[str, object] = {}
_cached_version: str | None = None
_last_version_check: float = 0.0
# In-flight computations: dedupe concurrent compute_fn() calls for the same key
_in_flight: dict[str, threading.Event] = {}
_in_flight_errors: dict[str, BaseException] = {}


def get_db_version() -> str | None:
    """Public: read data_version from scrape_meta (used by auto-rewarm)."""
    return _get_db_version_impl()


def _get_db_version() -> str | None:
    """Backward-compat alias; prefer get_db_version()."""
    return _get_db_version_impl()


def _get_db_version_impl() -> str | None:
    """
    Read the current data_version from scrape_meta table.
    Returns None if the table doesn't exist (e.g. SQLite test DB).
    """
    try:
        from .database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT value FROM scrape_meta WHERE key = 'data_version'")
            )
            row = result.fetchone()
            return row[0] if row else None
    except Exception:
        # Table may not exist (SQLite test DB) — treat as version None
        return None


def _check_version() -> bool:
    """
    Check if the database version changed since last check.

    Fix 1 (stale-while-revalidate): keep serving the previous warm cache
    while the new data_version is being rewarmed in the background. The
    old behaviour did ``_cache.clear()`` here, which left every request
    cold (25s seq scan) for the ~13 min it takes to rewarm 1472 ship
    keys on the 1-CPU prod box. Preview builds share the same DB, so a
    preview warm at the same minute as a scheduled scrape made prod
    appear to be invalidated by the preview.

    Now: bump ``_cached_version`` and clear only the in-flight deduplication
    state, but keep ``_cache`` entries as stale. The background auto-rewarm
    (``main.py:_start_cache_auto_rewarm``) overwrites hot keys with fresh
    data; until then stale hits are fast (0.1s) instead of cold (25s).
    Fix 2: always bump ``_cached_version`` so we do not loop-clear on
    every request (the 2026-08-31 prod incident left ``_cached_version``
    at ``None`` with ``entries:0`` after a warm).
    """
    global _cached_version, _last_version_check

    now = time.monotonic()
    if now - _last_version_check < CACHE_CHECK_INTERVAL:
        return False  # Not time to check yet

    _last_version_check = now
    db_version = _get_db_version()

    if db_version is not None and db_version != _cached_version:
        old = _cached_version
        _cached_version = db_version
        # Do NOT clear _cache — keep stale entries (Fix 1).
        _in_flight.clear()
        _in_flight_errors.clear()
        if old is not None:
            print(f"[cache] data_version {old} -> {db_version}, keeping {len(_cache)} stale entries while rewarming")
        return True

    return False


def get_cached_or_compute(key: str, compute_fn: Callable[[], T]) -> T:
    """
    Get a value from cache, or compute and cache it.

    Thread-safe. Checks for data version changes every 5 seconds.
    Cache is bounded to MAX_CACHE_ENTRIES via LRU eviction.
    """
    # Loop handles the case where we become a follower, wait for the leader,
    # but the leader's result isn't yet in _cache (race) or the leader failed
    # and we need to become the new leader.
    event: threading.Event | None = None
    is_leader = False
    for _attempt in range(3):
        # Check for version change (at most every 5 seconds)
        with _lock:
            _check_version()

            if key in _cache:
                return _cache[key]  # type: ignore

            # If another worker is already computing this key, follow it.
            # Otherwise, become the leader.
            if key in _in_flight:
                event = _in_flight[key]
                is_leader = False
            else:
                event = threading.Event()
                _in_flight[key] = event
                is_leader = True

        if is_leader:
            break  # Proceed to compute below

        assert event is not None
        # Follower: wait for the leader to finish
        if event.wait(timeout=120):
            with _lock:
                if key in _cache:
                    return _cache[key]  # type: ignore
                if key in _in_flight_errors:
                    raise _in_flight_errors[key]
            # Leader set the event but the result isn't in cache and no error:
            # this can happen if the leader process died mid-way. Loop and try again
            # — we'll become the leader.
            continue
        # Timed out — loop and try again as a new leader

    assert event is not None
    # Cache miss — compute outside the lock (computation may be slow)
    try:
        result = compute_fn()
    except BaseException as e:
        with _lock:
            _in_flight_errors[key] = e
            _in_flight.pop(key, None)
            event.set()
        raise
    else:
        with _lock:
            # Evict oldest entries if cache is full
            if len(_cache) >= MAX_CACHE_ENTRIES and key not in _cache:
                # Remove the oldest entry (first inserted)
                oldest_key = next(iter(_cache))
                del _cache[oldest_key]
            _cache[key] = result
            # Wake up waiters and clean up in-flight state
            event.set()
            _in_flight.pop(key, None)
            _in_flight_errors.pop(key, None)

        return result


def set_cached_version(version: str | None) -> None:
    """Sync the in-memory version after a successful warm (Fix 2).

    Called from ``main.py`` after startup / auto-rewarm so ``_check_version``
    does not re-trigger a clear on the next request. Updates ``_last_version_check``
    as well so we do not immediately re-poll.
    """
    global _cached_version, _last_version_check
    with _lock:
        _cached_version = version
        _last_version_check = time.monotonic()


def invalidate_cache():
    """
    Manually invalidate the entire cache.
    Useful for testing or manual data updates.
    """
    with _lock:
        _cache.clear()
        _in_flight.clear()
        _in_flight_errors.clear()


def cache_stats() -> dict:
    """Return cache statistics for debugging."""
    with _lock:
        return {
            "entries": len(_cache),
            "version": _cached_version,
            "last_check": _last_version_check,
        }
