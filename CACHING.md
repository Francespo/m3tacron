# Response Caching Implementation

## Overview

This document describes the response caching system implemented in the M3taCron backend API to improve performance and reduce database load.

## Problem Statement

The M3taCron API performs expensive database aggregations for analytics endpoints (lists, ships, pilots, upgrades, squadrons, and detail routes). Since new tournament data is inserted only **once per day**, most API responses remain static for long periods. Without caching, repeated requests to these endpoints cause unnecessary database queries and slow response times.

## Solution: Time-Based Response Caching

### Architecture

**File**: `backend/cache.py`

The caching system uses a simple in-memory cache with time-to-live (TTL) expiration:

```python
@cached_response(ttl_seconds=3600)
def get_lists(...):
    # API endpoint implementation
    ...
```

### Features

- **Automatic Caching**: Decorator-based approach requires minimal code changes
- **TTL-based Expiration**: Cache entries automatically expire after 1 hour (3600 seconds)
- **Per-Parameter Caching**: Different parameter combinations create separate cache entries
- **Manual Invalidation**: Admin endpoint to clear cache immediately after data refresh

### Cached Endpoints

The following endpoints benefit from caching (1-hour TTL):

#### Main Analytics Endpoints
- `GET /api/lists` - List statistics
- `GET /api/ships` - Ship statistics
- `GET /api/ships/all` - All available ships
- `GET /api/cards/pilots` - Pilot statistics
- `GET /api/cards/upgrades` - Upgrade statistics
- `GET /api/squadrons` - Squadron statistics

#### Meta Endpoint
- `GET /api/meta-snapshot` - Overall meta snapshot (factions, ships, lists, pilots, upgrades, stats)

#### Detail Pages
- `GET /api/pilot/{pilot_xws}` - Pilot info
- `GET /api/pilot/{pilot_xws}/upgrades` - Pilot-compatible upgrades
- `GET /api/pilot/{pilot_xws}/chart` - Pilot usage history
- `GET /api/pilot/{pilot_xws}/configurations` - Pilot upgrade configurations
- `GET /api/ship/{ship_xws}` - Ship info
- `GET /api/ship/{ship_xws}/pilots` - Pilots in this ship
- `GET /api/ship/{ship_xws}/lists` - Lists using this ship
- `GET /api/ship/{ship_xws}/squadrons` - Squadrons using this ship
- `GET /api/squadron/{signature}/stats` - Squadron statistics
- `GET /api/squadron/{signature}/pilots` - Pilots in this squadron
- `GET /api/squadron/{signature}/lists` - Lists with this squadron
- `GET /api/list/{list_id}/stats` - List statistics

## Usage

### For API Users

No changes required. Responses are transparently cached. To get fresh data:

1. Wait for cache expiration (1 hour by default)
2. OR trigger manual cache invalidation (see below)

### For Administrators: Manual Cache Invalidation

When new tournament data is imported, invalidate the cache immediately:

```bash
curl -X POST http://localhost:8000/api/cache/invalidate
```

Response:
```json
{
  "status": "success",
  "message": "Cache invalidated"
}
```

### For Developers: Adjusting Cache TTL

To change the cache time-to-live for any endpoint, modify the `ttl_seconds` parameter:

```python
@cached_response(ttl_seconds=7200)  # 2 hours
def get_lists(...):
    ...
```

**Recommended TTL values:**
- `3600` (1 hour): Most analytics endpoints (default)
- `1800` (30 minutes): Frequently changing data
- `7200` (2 hours): Static metadata (ships, pilots)

## Implementation Details

### Cache Key Generation

Cache keys are generated from:
1. Function name
2. Positional arguments
3. Keyword arguments

Example:
```python
get_lists(
    page=0,
    size=20,
    data_source="xwa",
    formats=["Extended"],
    factions=["rebel-alliance"]
)
# Generates unique cache key for this parameter combination
```

Different parameter values create separate cache entries, allowing:
- Page 0 and Page 1 results to be cached separately
- XWA and Legacy data sources to be cached independently
- Filtered and unfiltered results to coexist in cache

### Cache Statistics

Debug cache state:

```python
from backend.cache import get_cache_stats
stats = get_cache_stats()
print(stats)
# Output: {'total_entries': 5, 'keys': [...]}
```

## Performance Impact

### Expected Improvements

- **First request**: Full database query (baseline)
- **Cached requests** (within TTL): ~10-100x faster (instant memory lookup)
- **After TTL expires**: Returns to baseline (cache expired)

### Memory Overhead

- Negligible for typical API traffic
- Each cache entry stores: response object + timestamp
- ~1-10 MB per 100 concurrent cache entries (depends on response size)

## Monitoring

### To Monitor Cache Hits

Add logging to `backend/cache.py` if needed:

```python
@cached_response(ttl_seconds=3600)
def cached_func(...):
    print("Cache miss - executing function")  # Only on cache misses
    ...
```

## Future Enhancements

Potential improvements:
1. **Redis integration**: For distributed/multi-instance deployments
2. **Cache warmup**: Pre-load common queries on startup
3. **Partial invalidation**: Clear only specific endpoints (e.g., only lists, not ships)
4. **Metrics**: Track cache hit rates and effectiveness
5. **Adaptive TTL**: Adjust TTL based on data freshness

## Troubleshooting

### Cache Not Working?

1. Verify the decorator is applied: Check the function definition in the source code
2. Check cache stats: `from backend.cache import get_cache_stats; print(get_cache_stats())`
3. Verify TTL hasn't expired: Check timestamp in cache store

### Cache Not Clearing?

1. Use the `/api/cache/invalidate` endpoint
2. Or restart the application (cache is in-memory)

### Wrong Data Returned?

If you see stale data:
1. Wait for TTL to expire (default 1 hour)
2. Or call `POST /api/cache/invalidate` to clear immediately
3. Or check if you're using different query parameters (creates separate cache entry)

## References

- **Decorator Pattern**: Python `functools.wraps`
- **Cache Keys**: MD5 hash of function name + arguments
- **TTL Mechanism**: `datetime.now()` comparison
- **Thread Safety**: Current implementation is single-threaded; use locks for concurrent access if needed
