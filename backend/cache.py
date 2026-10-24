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

Persistence: entries are pickled to ``data/`` so a restart keeps the warm
cache. The dump is throttled (``CACHE_SAVE_MIN_INTERVAL_SECONDS``) because
rewriting hundreds of MB on every few keys dominates warm-up I/O, and each
worker watches the file so the ones that did not run the warm-up adopt the
same snapshot instead of staying cold.
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

# Writing the whole cache to disk is expensive (tens to hundreds of MB), so
# the per-write dump used to dominate warm-up I/O. Persist at most once per
# interval; the warm-up always calls save_cache() explicitly at the end.
SAVE_MIN_INTERVAL = float(os.getenv("CACHE_SAVE_MIN_INTERVAL_SECONDS", "60"))

# Every uvicorn worker keeps its own in-memory copy. This watcher lets a
# worker that did not run the warm-up adopt the snapshot another worker wrote,
# instead of staying cold and recomputing every page on first hit.
DISK_RELOAD_INTERVAL = float(os.getenv("CACHE_DISK_RELOAD_INTERVAL_SECONDS", "20"))

# Never delete a cache file younger than this: a rolling deploy may still be
# reading/writing it.
STALE_CACHE_MIN_AGE = 900.0

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
_last_save_at: float = time.monotonic()
_disk_mtime: float = 0.0  # mtime of the snapshot we last loaded or wrote
_watcher: threading.Thread | None = None


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
    global _disk_mtime
    path = _get_cache_file_path(version)
    _purge_old_disk_caches(version)
    if not path or not path.exists():
        return False
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        if isinstance(data, dict) and data:
            with _lock:
                _cache.update(data)
                _disk_mtime = path.stat().st_mtime
            print(f"[cache] restored {len(data)} warm entries from disk cache for data_version {version}")
            return True
    except Exception as exc:
        print(f"[cache] failed to load disk cache for {version}: {exc}")
    return False


def _reload_disk_cache_if_newer() -> int:
    """Adopt a snapshot written by another worker, if it is newer than ours.

    Returns the number of entries added. Used by the watcher thread and before
    every save, so a worker with a partial cache never overwrites a fuller one.
    """
    global _disk_mtime
    with _lock:
        path = _get_cache_file_path(_cached_version)
    if not path:
        return 0
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return 0
    with _lock:
        if mtime <= _disk_mtime:
            return 0
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
    except Exception as exc:
        print(f"[cache] disk cache reload skipped: {exc}")
        return 0
    if not isinstance(data, dict) or not data:
        return 0
    with _lock:
        if mtime <= _disk_mtime:
            return 0
        before = len(_cache)
        _cache.update(data)
        _disk_mtime = mtime
        added = len(_cache) - before
    print(f"[cache] adopted {len(data)} entries from disk cache ({added} new in this worker)")
    return added


def _save_disk_cache(version: str | None):
    global _disk_mtime
    path = _get_cache_file_path(version)
    if not path:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Merge a newer snapshot from another worker before writing, otherwise
        # a worker that warmed less would shrink the shared disk cache.
        _reload_disk_cache_if_newer()
        with _lock:
            snapshot = dict(_cache)
        if not snapshot:
            return
        # Per-process temp name: two workers saving at once must not interleave
        # writes into the same file.
        tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        with open(tmp_path, "wb") as f:
            pickle.dump(snapshot, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp_path.replace(path)
        with _lock:
            _disk_mtime = path.stat().st_mtime
        _purge_old_disk_caches(version)
    except Exception as exc:
        print(f"[cache] disk cache save skipped: {exc}")


def _purge_old_disk_caches(keep_version: str | None):
    """Delete pickles left by older data versions or code fingerprints.

    Left unattended they pile up (hundreds of MB per deploy on production).
    Files touched recently are kept so a rolling deploy can finish with them.
    """
    try:
        if not CACHE_DIR.exists():
            return
        keep_path = _get_cache_file_path(keep_version)
        now = time.time()
        for p in CACHE_DIR.glob("api_cache_*"):
            if keep_path and p == keep_path:
                continue
            try:
                if now - p.stat().st_mtime < STALE_CACHE_MIN_AGE:
                    continue
                p.unlink()
            except Exception:
                pass
    except Exception:
        pass


def start_disk_cache_watcher() -> None:
    """Keep every worker on the same warm snapshot.

    Only one process wins the warm advisory lock, so the others start empty
    and used to recompute every page on first hit. Polling the snapshot file
    (a cheap stat) closes that gap without a shared cache server.
    """
    global _watcher
    if _watcher is not None and _watcher.is_alive():
        return

    def _loop():
        while True:
            time.sleep(DISK_RELOAD_INTERVAL)
            try:
                _reload_disk_cache_if_newer()
            except Exception as exc:
                print(f"[cache] disk cache watcher error: {exc}")

    _watcher = threading.Thread(target=_loop, daemon=True, name="cache-disk-watcher")
    _watcher.start()


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
    global _cached_version, _last_version_check, _disk_mtime

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
        _disk_mtime = 0.0
        _purge_old_disk_caches(db_version)
        print(f"[cache] data_version {old} -> {db_version}: invalidated cache after scrape")
        return True

    return False


def get_cached_or_compute(key: str, compute_fn: Callable[[], T], force: bool = False) -> T:
    """
    Get a value from cache, or compute and cache it.
    Thread-safe. Checks for data version changes every 5 seconds.
    """
    global _last_save_at
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
        save_version: str | None = None
        with _lock:
            if len(_cache) >= MAX_CACHE_ENTRIES and key not in _cache:
                oldest_key = next(iter(_cache))
                del _cache[oldest_key]
            _cache[key] = result
            # Persist at most once per SAVE_MIN_INTERVAL: rewriting the whole
            # pickle on every few keys hammered the disk during warm-up.
            now = time.monotonic()
            if now - _last_save_at >= SAVE_MIN_INTERVAL:
                _last_save_at = now
                save_version = _cached_version
            event.set()
            _in_flight.pop(key, None)
            _in_flight_errors.pop(key, None)

        if save_version:
            _save_disk_cache(save_version)

        return result


def has_cached(key: str) -> bool:
    """True when the key is already warm in this process.

    Used by the pre-warmer to skip whole aggregation rounds when the disk cache
    was restored at startup: recomputing a key that is already there is pure
    waste, and the ship-detail fan-out is the expensive half of the warm-up.
    """
    with _lock:
        _check_version()
        return key in _cache


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
    global _last_save_at
    _last_save_at = time.monotonic()
    _save_disk_cache(_cached_version)


def invalidate_cache():
    """
    Manually invalidate the entire cache.
    """
    global _disk_mtime
    with _lock:
        _cache.clear()
        _in_flight.clear()
        _in_flight_errors.clear()
        _disk_mtime = 0.0
        _purge_old_disk_caches(None)


def cache_stats() -> dict:
    """Return cache statistics for debugging."""
    with _lock:
        return {
            "entries": len(_cache),
            "version": _cached_version,
            "last_check": _last_version_check,
            "seconds_since_save": round(time.monotonic() - _last_save_at, 1),
            "disk_mtime": _disk_mtime,
            "save_min_interval_s": SAVE_MIN_INTERVAL,
        }
