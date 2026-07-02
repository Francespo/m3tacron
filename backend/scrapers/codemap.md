# backend/scrapers/

## Responsibility
External data ingestion — fetching X-Wing squad, tournament, and match data from third-party tournament platforms (ListFortress, Longshanks, Rollbetter) and YASB builder URLs, and persisting them into the local DB via the ORM.

## Design
- **Abstract interface**: `BaseScraper` (in `base.py`) defines the contract — `list_tournaments`, `get_tournament_data`, `get_participants`, `get_matches`, plus an orchestration method `run_full_scrape` that runs participants first so the format can be inferred from XWS data before fetching tournament metadata.
- **HTTP clients**: mixed. `ListFortressScraper` uses `httpx.Client` against the REST API. `RollbetterScraper` uses the public Rollbetter API (`urllib.request`) for listing and player lookup, then drives the Playwright UI for ListFortress JSON export, date, location, and detailed match tables. `LongshanksScraper` is fully Playwright-driven (no JSON API).
- **Sync Playwright** is used per-scraper-call (`sync_playwright()` context with headless Chromium) — each public method opens and closes its own browser instance.
- **Pagination**: explicit on Longshanks (`/events/history/?page=N`, iterated up to `max_pages`); ListFortress and Rollbetter APIs return the full result set in a single call.
- **Retries / fallbacks**: `RollbetterScraper._ensure_data` retries 3× then falls back to `_try_fetch_api_data` and finally a UI-only fallback (`_build_fallback_from_ui`). `LongshanksScraper` has a parallel `pop_info.php` popup fetch (`_fetch_lists_from_popups`) for missing XWS lists, executed via `ThreadPoolExecutor` with 10 workers.
- **Error handling**: every fetch is wrapped in `try/except` with `logger.error` and a safe default (empty list or a `Tournament` placeholder). `BaseScraper._compute_stats_from_matches` fills in W/L/D and tie-breakers when platforms only expose match data (sentinel `-1` triggers compute).
- **Validation**: `validation.is_scrapable` is a pre-flight gate that opens a Playwright page and confirms the URL is an X-Wing event with sufficient players and a Games/Rounds tab before the full scrape.
- **Mapping**: platform JSON / HTML → ORM models (`Tournament`, `PlayerStanding`, `Match`) with `Source.{LISTFORTRESS,LONGSHANKS,ROLLBETTER}`, `RoundType`, `Scenario`, `Location` (via `utils.geocoding.resolve_location`).
- **Persistence**: scrapers return model instances; the caller (`backend/scripts/scrape_tournaments.py`) handles the upsert via `dedup_utils.check_for_duplicates` + `save_tournament_data` + `session.commit`.

## Flow
1. CLI / scheduler (`backend/scripts/scrape_tournaments.py`) instantiates a `BaseScraper` subclass for the target host (ListFortress, Longshanks 2.5, Longshanks Legacy, Rollbetter AMG/XWA/Legacy).
2. `list_tournaments(date_from, date_to, max_pages)` discovers tournament URLs in the date range.
3. For each URL, `run_full_scrape(tournament_id)` orchestrates: `get_participants` (also yields XWS for format inference) → `get_tournament_data` (with inferred format) → `get_matches`.
4. Optional pre-flight `is_scrapable(url, platform, page)` rejects non-X-Wing or in-progress events.
5. Optional `fetch_xws_from_builder(url)` (`web_utils.py`) drives YASB UI to export XWS JSON for a list URL.
6. Caller maps results to ORM models, dedupes against existing tournaments (protecting non-ListFortress sources from LF overwrites), then `session.add` / `session.commit`.

## Integration
- **Consumed by**: `backend/scripts/scrape_tournaments.py` (URL-keyed dispatch, `scrape_platform`, and per-URL scrape). `validation.is_scrapable` and `web_utils.fetch_xws_from_builder` are currently internal helpers (no external callers in `backend/api` or `routers`).
- **Depends on**: `backend.models` (`Tournament`, `PlayerStanding`, `Match`), `backend.data_structures` (`formats.Format` + `infer_format_from_xws`, `round_types.RoundType`, `scenarios.Scenario`, `location.Location`, `factions.Faction`, `source.Source`, `platforms.Platform`), `backend.utils.geocoding.resolve_location`, `backend.utils.parse_builder_url`, `backend.database.SessionLocal` (via the calling script's `Session(engine)`).
- **Exposes**:
  - Classes: `BaseScraper`, `ListFortressScraper`, `LongshanksScraper(subdomain="xwing"|"xwing-legacy")`, `RollbetterScraper(game_id=5|17|4)`.
  - Methods: `BaseScraper.run_full_scrape`, `LongshanksScraper.run_full_scrape` (overridden for runtime subdomain), module-level helper `scrape_longshanks_event(event_id, subdomain)`.
  - Utilities: `validation.is_scrapable`, `web_utils.fetch_xws_from_builder`.
