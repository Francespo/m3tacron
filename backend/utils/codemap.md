# backend/utils/

## Responsibility
Cross-cutting helper modules providing reusable, mostly stateless functions for HTTP geocoding, fuzzy tournament deduplication, XWS squadron parsing/canonicalization, YASB URL generation, and location hierarchy queries. These utilities bridge raw scraper data and the domain models used across `api/`, `scrapers/`, and `analytics/`.

## Design
- **Pure or near-pure functions / small classes** — no routers, no FastAPI surface, no DB models defined here.
- **Stateless by default**, with two exceptions that hold process-local state: `geocoding._GEO_CACHE` (loaded from `data/geocoding_cache.json`) and `geocoding.LAST_REQUEST_TIME` (Nominatim throttle).
- **Throttled external I/O**: `geocoding.resolve_location` enforces `MIN_DELAY_SECONDS = 1.1` and a `User-Agent`, plus custom overrides and a normalization/dedup of candidate queries.
- **Lazy imports inside functions** are used in `squadron.py` and `geocoding.py` to avoid circular imports with `..data_structures` and `..models`.
- **XWS canonicalization** lives here so squadrons with different pilot/upgrade orderings hash to the same signature (`list_keys.get_list_key`, `squadron.get_list_signature`).
- **Public surface re-exported** through `__init__.py`: only `parse_builder_url` from `squadron`.

## Flow
1. Caller (scraper, API, or analytics) imports a utility function (e.g. `from ..utils.geocoding import resolve_location`).
2. Caller invokes the function with raw input (URL string, location string, XWS dict, list of `Tournament`).
3. Utility applies normalization, fuzzy matching, or signature generation and returns a result (`Location`, `Tournament | None`, signature string, etc.).
4. Optional side effects: `geocoding` writes to the on-disk cache; `deduplication` logs at `DEBUG`.
5. Stateless functions have no further steps; `deduplication.find_duplicate` short-circuits on the first match.

## Integration
- **Consumed by**:
  - `backend/scrapers/longshanks_scraper.py`, `rollbetter_scraper.py`, `listfortress_scraper.py` — use `parse_builder_url` and `resolve_location`.
  - `backend/api/list_detail.py` — uses `get_list_key`.
  - `backend/analytics/factions.py`, `analytics/ships.py` — use `get_list_key`.
  - `backend/scripts/dedup_utils.py` — uses `DedupService`.
  - (Also referenced via `xwing_data/` subpackage, documented separately.)
- **Depends on**:
  - Stdlib: `json`, `re`, `time`, `logging`, `urllib.parse`, `difflib`, `unicodedata`, `datetime`, `pathlib`.
  - Third-party: `httpx` (Nominatim calls in `geocoding.py`).
  - Internal: `..models` (Tournament, PlayerStanding), `..database.engine`, `..data_structures.location.Location`, `..data_structures.factions.Faction`, `..data_structures.formats.Format`, and `.xwing_data.pilots.get_pilot_info`.
- **Exposes**:
  - `parse_builder_url(url)` (`squadron`) — dispatch to `_parse_yasb` / `_parse_lbn`; re-exported in `__init__`.
  - `get_squadron_signature(xws)` / `get_list_signature(xws)` / `parse_squadron_signature(sig)` (`squadron`) — XWS canonicalization keys.
  - `get_list_key(xws)` (`list_keys`) — JSON-based canonical key from pilots + upgrades.
  - `resolve_location(query)` (`geocoding`) — Nominatim lookup with cache, throttle, custom overrides, online/virtual detection; returns a `Location`.
  - `get_all_locations()` (`locations`) — DB query returning `{continent: {country: [cities]}}` hierarchy.
  - `DedupService.find_duplicate(target, candidates, …)` (`deduplication`) — date + name similarity + Jaccard player-overlap matcher.
  - `get_yasb_base_url(format)` / `xws_to_yasb_url(xws, format)` / `get_xws_string(xws)` (`yasb`) — builder URL helpers.
- **Subpackage**: `xwing_data/` (see `backend/utils/xwing_data/codemap.md`).
