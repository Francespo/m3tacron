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
import os
from pathlib import Path
import pickle
import threading
import time
from typing import Callable, TypeVar

T = TypeVar("T")

# Configuration
CACHE_CHECK_INTERVAL = 5.0  # seconds between version checks
MAX_CACHE_ENTRIES = 10000
CACHE_DIR = Path(__file__).parent / "data"

# Internal state
_lock = threading.RLock()
_cache: dict[str, object] = {}
_cached_version: str | None = None
_last_version_check: float = 0.0
_in_flight: dict[str, threading.Event] = {}
_in_flight_errors: dict[str, BaseException] = {}
_writes_since_save: int = 0


def _get_cache_file_path(version: str | None) -> Path | None:
    if not version:
        return None
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        clean_v = "".join(c for c in str(version) if c.isalnum() or c in ("-", "_"))
        return CACHE_DIR / f"api_cache_{clean_v}.pkl"
    except Exception:
        return None


def _load_disk_cache(version: str | None) -> bool:
    path = _get_cache_file_path(version)
    if not path or not path.exists():
        return False
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        if isinstance(data, dict) and data:
            with _lock:
                _cache.update(data)
            print(f"[cache] restored {len(data)} warm entries from disk cache for data_version {version}")
            return True
    except Exception as exc:
        print(f"[cache] failed to load disk cache for {version}: {exc}")
    return False


def _save_disk_cache(version: str | None):
    path = _get_cache_file_path(version)
    if not path:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            snapshot = dict(_cache)
        if not snapshot:
            return
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "wb") as f:
            pickle.dump(snapshot, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp_path.replace(path)
    except Exception as exc:
        print(f"[cache] disk cache save skipped: {exc}")


def _purge_old_disk_caches(keep_version: str | None):
    try:
        if not CACHE_DIR.exists():
            return
        keep_path = _get_cache_file_path(keep_version)
        for p in CACHE_DIR.glob("api_cache_*.pkl*"):
            if keep_path and p == keep_path:
                continue
            try:
                p.unlink()
            except Exception:
                pass
    except Exception:
        pass


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
        return None


def _check_version() -> bool:
    """
    Check if the database version changed since last check.
    Invalidates cache ONLY when data_version changes (after a successful scrape).
    """
    global _cached_version, _last_version_check

    now = time.monotonic()
    if now - _last_version_check < CACHE_CHECK_INTERVAL:
        return False

    _last_version_check = now
    db_version = _get_db_version()

    if db_version is None:
        return False

    if _cached_version is None:
        _cached_version = db_version
        _load_disk_cache(db_version)
        return False

    if db_version != _cached_version:
        old = _cached_version
        _cached_version = db_version
        _cache.clear()
        _in_flight.clear()
        _in_flight_errors.clear()
        _purge_old_disk_caches(db_version)
        print(f"[cache] data_version {old} -> {db_version}: invalidated cache after scrape")
        return True

    return False


def get_cached_or_compute(key: str, compute_fn: Callable[[], T], force: bool = False) -> T:
    """
    Get a value from cache, or compute and cache it.
    Thread-safe. Checks for data version changes every 5 seconds.
    """
    global _writes_since_save
    if not force:
        with _lock:
            _check_version()
            if key in _cache:
                return _cache[key]  # type: ignore

    event: threading.Event | None = None
    is_leader = False
    for _attempt in range(3):
        with _lock:
            _check_version()

            if not force and key in _cache:
                return _cache[key]  # type: ignore

            if key in _in_flight:
                event = _in_flight[key]
                is_leader = False
            else:
                event = threading.Event()
                _in_flight[key] = event
                is_leader = True

        if is_leader:
            break

        assert event is not None
        if event.wait(timeout=120):
            with _lock:
                if key in _cache:
                    return _cache[key]  # type: ignore
                if key in _in_flight_errors:
                    raise _in_flight_errors[key]
            continue

    assert event is not None
    try:
        result = compute_fn()
    except BaseException as e:
        with _lock:
            _in_flight_errors[key] = e
            _in_flight.pop(key, None)
            event.set()
        raise
    else:
        save_needed = False
        with _lock:
            if len(_cache) >= MAX_CACHE_ENTRIES and key not in _cache:
                oldest_key = next(iter(_cache))
                del _cache[oldest_key]
            _cache[key] = result
            _writes_since_save += 1
            if _writes_since_save >= 10:
                _writes_since_save = 0
                save_needed = True
            event.set()
            _in_flight.pop(key, None)
            _in_flight_errors.pop(key, None)

        if save_needed:
            _save_disk_cache(_cached_version)

        return result


def set_cached_version(version: str | None) -> None:
    """Sync the in-memory version after startup / warm."""
    global _cached_version, _last_version_check
    with _lock:
        if version is not None:
            _cached_version = version
        _last_version_check = time.monotonic()
        if not _cache and _cached_version:
            _load_disk_cache(_cached_version)


def save_cache():
    """Explicitly save in-memory cache to disk."""
    _save_disk_cache(_cached_version)


def invalidate_cache():
    """
    Manually invalidate the entire cache.
    """
    with _lock:
        _cache.clear()
        _in_flight.clear()
        _in_flight_errors.clear()
        _purge_old_disk_caches(None)


def cache_stats() -> dict:
    """Return cache statistics for debugging."""
    with _lock:
        return {
            "entries": len(_cache),
            "version": _cached_version,
            "last_check": _last_version_check,
        }
