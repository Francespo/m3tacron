# backend/scripts/

## Responsibility
Operational and maintenance scripts — tournament data scraping, cross-platform deduplication, one-off schema backfills, and SQLite↔PostgreSQL data import for the M3taCron X-Wing tournament tracker.

## Design
- Standalone executable Python scripts with `if __name__ == "__main__"` entry points and explicit `sys.exit(main())` return codes.
- `argparse` everywhere for flags; `logging` to stdout for ops visibility.
- All scripts are idempotent: scrapers check existing URLs and skip duplicates, migration scripts are safe to re-run, imports use `TRUNCATE ... RESTART IDENTITY CASCADE` (opt-out via `--skip-truncate`).
- `scrape_tournaments.py` is the largest module: parallel `ThreadPoolExecutor` for independent scrapers (Longshanks, Rollbetter), sequential stage for the dependent ListFortress scraper, and a module-level `_DB_WRITE_LOCK` to serialise `MAX+1` ID assignments across workers.
- `dedup_utils.py` centralises cross-platform duplicate detection (5-day window + `DedupService` similarity) and is shared by both the scraper and the dedup runner.

## Flow
1. Operator / CI invokes a script via `python -m backend.scripts.<name> [flags]`.
2. `argparse` parses flags; logging configured.
3. Script opens a SQLAlchemy `Session` against `backend.database.engine` (or SQLite via `DATABASE_URL` env override).
4. Job runs — list tournaments / scrape per-URL / backfill team IDs / import rows / dedupe.
5. Dedup check, save with explicit IDs, `session.commit()`, close.
6. Optional SQLite artifact written (e.g. for CI artifact upload).

## Integration
- **Consumed by**: GitHub Actions workflow `.github/workflows/scrape_tournaments.yml` (calls `scrape_tournaments_sqlite.py` and `scrape_tournaments.py`); local dev and ops runs (`python -m backend.scripts.*`).
- **Depends on**: `backend.database` (engine, `create_db_and_tables`), `backend.models` (`Tournament`, `PlayerStanding`, `Match`, `TeamMatch`, `TeamStanding`), `backend.scrapers` (`LongshanksScraper`, `RollbetterScraper`, `ListFortressScraper`), `backend.data_structures.{round_types,source}`, `backend.utils.deduplication.DedupService`. Uses `psycopg2` + `sqlite3` stdlib (import script only).
- **Exposes**:
  - `scrape_tournaments.py` — main multi-platform X-Wing scraper (Longshanks 2.5/Legacy, Rollbetter AMG/XWA/Legacy, ListFortress) with dedup, dry-run, overwrite, and SQLite artifact output.
  - `scrape_tournaments_sqlite.py` — thin wrapper that forces `DATABASE_URL=sqlite:///...` then forwards to `scrape_tournaments.main()`.
  - `run_deduplication.py` — CLI to detect (and optionally `--prune`) duplicate tournaments by ID/range, with source-priority ordering (Longshanks > Rollbetter > ListFortress).
  - `migrate_team_names.py` — one-off backfill creating `TeamStanding` rows from existing `playerstanding.team_name` values and linking `team_id` (does not drop the legacy column).
  - `import_sqlite_to_postgres.py` — bulk copy of `tournament`, `playerstanding`, `teamstanding`, `match`, `teammatch` from a local SQLite DB into PostgreSQL, normalising `is_bye` and JSON columns.
  - `dedup_utils.py` — shared `check_for_duplicates(session, tournament, players, overwrite)` helper used by the scraper and the dedup runner.
  - `__init__.py` — empty package marker.
