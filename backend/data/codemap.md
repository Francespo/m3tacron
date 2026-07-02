# backend/data/

## Responsibility
Persistent on-disk data store for the application. Currently holds a single JSON file, `geocoding_cache.json`, that caches resolved venue locations (city, country, continent) keyed by raw tournament location strings. Acts as a write-through cache so the app avoids re-hitting the Nominatim geocoding API for previously seen queries.

## Design
- Single JSON document, not a Python module: there are no `.py` files in this directory, so there are no module-level constants, dataclasses, or Pydantic models defined here.
- Schema per entry: a flat object with three string fields — `city`, `country`, `continent` — e.g. `"SD, US"` -> `{"city": "South Dakota", "country": "United States", "continent": "North America"}`.
- Sentinel value `"Unknown"` is used for the `city` field when only the country is known; this is read by the consumer to decide whether to re-attempt the API call.
- The cache is mutated and rewritten as a whole on every new geocode hit; the file is the durable counterpart to an in-memory `_GEO_CACHE` dict.
- Container/deploy: `docker-compose.yml` mounts this directory as a volume (`data:/app/backend/data`) so cache writes survive container restarts.

## Flow
1. `backend/utils/geocoding.py` resolves `Path(__file__).parent.parent / "data" / "geocoding_cache.json"` at import time and ensures the parent directory exists.
2. `_load_cache()` reads the JSON into the module-level `_GEO_CACHE` dict on first import.
3. `resolve_location(query)` is called by the scraper layer with a raw venue string (e.g. `"Turbulent Games, SD, US"`).
4. If a non-`Unknown` entry exists, it is returned as a `Location`; otherwise Nominatim is called, the result is normalized, written back to `_GEO_CACHE`, and persisted via `_save_cache()`.
5. On scheduled/manual runs, `.github/workflows/scrape_tournaments.yml` does `git add backend/data/geocoding_cache.json` and commits the updated cache so newly resolved venues are shared with future deployments.

## Integration
- **Consumed by**: `backend/utils/geocoding.py` (defines `CACHE_FILE`, `_load_cache`, `_save_cache`, and the `_GEO_CACHE` in-memory mirror; `resolve_location` is the public entry point used by the scrapers).
- **Depends on**: No Python imports. The file is read/written as raw JSON via `json.loads` / `json.dumps`. The data model it persists matches `backend/data_structures/location.py:Location` (`city`, `country`, `continent`).
- **Exposes**: A single shared resource file — `geocoding_cache.json` — mapping raw location strings to `{city, country, continent}` records. Not imported as a module; only read by path.
