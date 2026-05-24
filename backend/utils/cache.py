from __future__ import annotations

import hashlib
import inspect
import json
import sqlite3
import threading
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

from fastapi.encoders import jsonable_encoder

CACHE_DIR = Path(__file__).resolve().parents[1] / "data"
CACHE_DB_PATH = CACHE_DIR / "analytics_cache.sqlite3"
CACHE_VERSION_PATH = CACHE_DIR / "analytics_cache.version"
_CACHE_LOCK = threading.Lock()
T = TypeVar("T")


CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_schema() -> None:
    with sqlite3.connect(CACHE_DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_cache (
                cache_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


_ensure_schema()


def get_cache_version() -> str:
    if CACHE_VERSION_PATH.exists():
        version = CACHE_VERSION_PATH.read_text(encoding="utf-8").strip()
        if version:
            return version
    return "bootstrap"


def bump_cache_version(reason: str | None = None) -> str:
    version = datetime.now(timezone.utc).isoformat()
    CACHE_VERSION_PATH.write_text(version, encoding="utf-8")
    return version


def _hash_payload(namespace: str, bound_arguments: dict[str, Any]) -> str:
    payload = json.dumps(
        jsonable_encoder(bound_arguments),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{namespace}:{get_cache_version()}:{digest}"


def _read_cached_value(cache_key: str) -> Any | None:
    with sqlite3.connect(CACHE_DB_PATH) as connection:
        row = connection.execute(
            "SELECT payload FROM analytics_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def _write_cached_value(cache_key: str, value: Any) -> None:
    payload = json.dumps(jsonable_encoder(value), sort_keys=True, default=str)
    with sqlite3.connect(CACHE_DB_PATH) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO analytics_cache (cache_key, payload, created_at)
            VALUES (?, ?, ?)
            """,
            (cache_key, payload, datetime.now(timezone.utc).isoformat()),
        )
        connection.commit()


def cached(namespace: str | None = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Persist the return value of a pure function in a versioned SQLite cache."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        signature = inspect.signature(func)
        cache_namespace = namespace or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            bound = signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            cache_key = _hash_payload(cache_namespace, dict(bound.arguments))

            with _CACHE_LOCK:
                cached_value = _read_cached_value(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)

            with _CACHE_LOCK:
                _write_cached_value(cache_key, result)

            return result

        wrapper.__signature__ = signature  # type: ignore[attr-defined]
        return wrapper

    return decorator


def warm_default_cache() -> None:
    """Prime the common dashboard and catalog responses after data refreshes."""
    from backend.api.cards import get_pilots, get_upgrades
    from backend.api.lists import get_lists
    from backend.main import get_snapshot

    for data_source in ("xwa", "legacy"):
        get_snapshot(data_source=data_source)
        get_lists(data_source=data_source)
        get_pilots(data_source=data_source)
        get_upgrades(data_source=data_source)
