"""
Response caching utility for API endpoints.
Provides time-based caching for frequently accessed endpoints that don't change often.
"""
import functools
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

# In-memory cache storage
_CACHE_STORE: dict[str, tuple[Any, datetime]] = {}


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a unique cache key based on function name and arguments."""
    key_data = {
        "func": func_name,
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in kwargs.items()},
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached_response(ttl_seconds: int = 3600):
    """
    Decorator to cache API response for a specified TTL.

    Args:
        ttl_seconds: Time-to-live in seconds (default: 1 hour)

    Usage:
        @cached_response(ttl_seconds=3600)
        def get_lists(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            now = datetime.now()

            # Check if cached value exists and is still valid
            if cache_key in _CACHE_STORE:
                cached_value, cached_time = _CACHE_STORE[cache_key]
                if now - cached_time < timedelta(seconds=ttl_seconds):
                    return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            _CACHE_STORE[cache_key] = (result, now)

            return result

        return wrapper

    return decorator


def clear_cache():
    """Clear all cached responses."""
    global _CACHE_STORE
    _CACHE_STORE.clear()


def clear_cache_for(pattern: Optional[str] = None):
    """
    Clear cache entries matching a pattern.
    If pattern is None, clears all cache.
    """
    global _CACHE_STORE
    if pattern is None:
        _CACHE_STORE.clear()
    else:
        keys_to_remove = [k for k in _CACHE_STORE.keys() if pattern in k]
        for key in keys_to_remove:
            del _CACHE_STORE[key]


def get_cache_stats() -> dict:
    """Return cache statistics."""
    return {
        "total_entries": len(_CACHE_STORE),
        "keys": list(_CACHE_STORE.keys()),
    }
