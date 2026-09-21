"""
In-memory cache with scrape- and code-change-triggered invalidation.

Cache entries are invalidated when EITHER changes:
  - the ``data_version`` in ``scrape_meta`` (after each scraper run), or
  - the fingerprint of the source code that computes cached results.

Why a code fingerprint instead of the deployed git SHA: entries are pickled to
disk and restored on startup, so a deploy must not restore results computed by
older logic (that bug made a deployed fix silently ineffective). Keying on the
commit alone would over-invalidate, though — a frontend or docs change would
discard a cache whose rebuild costs tens of minutes. The fingerprint covers
only the modules that actually produce cached data, so frontend-only deploys
keep the warm cache while analytics changes correctly force a recompute.

Usage:
    from backend.cache import get_cached_or_compute

    result = get_cached_or_compute(
        "lists|xwa|rebel|0",
        lambda: aggregate_list_stats(filters)
    )
"""
import hashlib
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

# Source paths whose contents can change a cached value. Deliberately narrow:
# anything not listed here (frontend, workflows, docs, scrapers, scripts) can
# be deployed without paying for a cache rebuild. Backend modules that serve
# requests but never feed the cache are excluded on purpose.
_CACHE_CODE_PATHS = (
    "analytics",       # all aggregations behind the cached endpoints
    "api",             # formatters + detail snapshots stored in the cache
    "utils",           # xwing_data, list_keys, stats used during aggregation
    "data_structures",  # Faction/Format/Source vocabularies used in results
    "cache.py",        # key semantics
    "main.py",         # endpoint definitions and cache keys
)


def _source_commit() -> str:
    """The git SHA this container was built from, for drift detection only.

    Coolify injects ``SOURCE_COMMIT``. This is reported via /api/cache/stats so
    the deploy-drift check can compare production against ``main``. It is NOT
    used as a cache key — see :func:`_code_fingerprint`.
    """
    for var in ("SOURCE_COMMIT", "CACHE_CODE_VERSION", "GIT_COMMIT"):
        value = (os.getenv(var) or "").strip().strip('"')
        if value:
            return value
    return ""


def _code_fingerprint() -> str:
    """Content hash of the modules that can change a cached value.

    Returns a short hex digest, stable across machines and environments for
    identical source. Returns ``""`` if the tree cannot be read (e.g. an
    unusual packaging layout), in which case callers fall back to the commit.
    """
    base = Path(__file__).parent
    files: list[Path] = []
    for rel in _CACHE_CODE_PATHS:
        target = base / rel
        if target.is_dir():
            files.extend(
                p for p in target.rglob("*.py") if "__pycache__" not in p.parts
            )
        elif target.is_file():
            files.append(target)

    if not files:
        return ""

    digest = hashlib.sha256()
    for path in sorted(files):
        try:
            digest.update(path.relative_to(base).as_posix().encode())
            digest.update(path.read_bytes())
        except OSError:
            continue
    return digest.hexdigest()[:16]


# Cache identity. Computed once at import: source cannot change while the
# process is alive. Falls back to the commit when the tree is unreadable, and
# to "dev" for local runs so the cache still works in a bare checkout.
_CODE_FINGERPRINT = _code_fingerprint()
_SOURCE_COMMIT = _source_commit()
_CODE_VERSION = _CODE_FINGERPRINT or _SOURCE_COMMIT or "dev"

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
        # Include the code version so a new deploy never picks up a pickle
        # written by older code (see module docstring).
        combined = f"{version}_{_CODE_VERSION}"
        clean_v = "".join(c for c in combined if c.isalnum() or c in ("-", "_"))
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
