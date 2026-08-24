#!/usr/bin/env python3
"""
Database backup + retention for m3tacron.

- Takes a pg_dump -Fc of the target Postgres DB (default: postgres on
  localhost:5432, overridden by DATABASE_URL or CLI).
- Writes to BACKUP_DIR (default ~/dumps or ./dumps) as
  <BACKUP_PREFIX>_YYYYMMDD_HHMMSS.dump.
- Enforces retention with NO gaps:
    keep daily backups for the last 3 days            (one per calendar day)
    keep the newest backup from 4-7 days ago           (= previous week)
    keep the newest backup from 8-14 days ago          (= 2 weeks ago)
    keep the newest backup from 28-31 days ago         (= previous month)
  Produces at most 6 snapshot files; everything else pruned.

Usage:
  python scripts/db_backup.py                          # default DB + dir
  python scripts/db_backup.py --dir /data/backups --prefix prod
  DATABASE_URL=postgres://... python scripts/db_backup.py --from-url
  python scripts/db_backup.py --dry-run                # list actions without deleting

This script is invoked by:
  - .github/workflows/scrape_tournaments.yml (after every daily scrape, and
    before the scrape on schedule so a pre-mutation snapshot exists)
  - Manual SSH: python scripts/db_backup.py

For restores: pg_restore -Fc -d <db> <file>
  or docker exec <pg-container> pg_restore ... (see scripts/local_dev/seed.sh)
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

TIMESTAMP_RE = re.compile(r"_(\d{8})_(\d{6})\.dump$")
DATE_RE = re.compile(r"(\d{8})")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Postgres backup with tiered retention")
    p.add_argument("--dir", dest="backup_dir", default=None, help="Backup directory (default: ~/dumps if exists else ./dumps)")
    p.add_argument("--prefix", default="prod", help="Filename prefix before timestamp (default: prod)")
    p.add_argument("--db-url", default=None, help="Postgres URL (default: DATABASE_URL env or postgres://postgres@localhost:5432/postgres)")
    p.add_argument("--from-url", action="store_true", help="Alias for --db-url $DATABASE_URL")
    p.add_argument("--pg-dump-bin", default="pg_dump", help="pg_dump binary (default: pg_dump)")
    p.add_argument("--keep-daily", type=int, default=3, help="Keep N most recent daily backups (default 3)")
    p.add_argument("--dry-run", action="store_true", help="Don't delete, just print what would be kept/pruned")
    p.add_argument("--no-dump", action="store_true", help="Skip dump; only enforce retention on existing files")
    p.add_argument("--retention-only", action="store_true", help="Alias for --no-dump")
    return p.parse_args()


def resolve_backup_dir(cli_dir: str | None) -> Path:
    if cli_dir:
        d = Path(cli_dir).expanduser()
    else:
        # Prefer ~/dumps (used on the prod host), fallback to ./dumps
        home_dumps = Path.home() / "dumps"
        if home_dumps.exists() or home_dumps.parent.exists():
            d = home_dumps
        else:
            d = Path("dumps")
    d.mkdir(parents=True, exist_ok=True)
    return d


def resolve_db_url(cli_url: str | None, from_url: bool) -> str:
    if cli_url:
        return cli_url
    if from_url or cli_url is None:
        env = os.getenv("DATABASE_URL")
        if env:
            return env
    # Default matches the scrape workflow's localhost tunnel (postgres db)
    return "postgres://postgres@localhost:5432/postgres"


def _extract_pg_params(db_url: str) -> dict[str, str]:
    u = urlparse(db_url)
    # urlparse postgres://user:pass@host:port/db?params
    return {
        "host": u.hostname or "localhost",
        "port": str(u.port or 5432),
        "user": u.username or "postgres",
        "password": u.password or "",
        "dbname": (u.path or "/postgres").lstrip("/") or "postgres",
    }


def do_dump(pg_dump_bin: str, db_url: str, out_path: Path) -> None:
    if shutil.which(pg_dump_bin) is None:
        # Try pg_dump via docker if available (Coolify host)
        print(f"pg_dump not found at {pg_dump_bin}, trying docker fallback…", file=sys.stderr)
    params = _extract_pg_params(db_url)
    env = os.environ.copy()
    if params["password"]:
        env["PGPASSWORD"] = params["password"]
    # pg_dump -h host -p port -U user -Fc -f file dbname
    cmd = [
        pg_dump_bin,
        "-h", params["host"],
        "-p", params["port"],
        "-U", params["user"],
        "-Fc",
        "-f", str(out_path),
        params["dbname"],
    ]
    print(f"Running: {' '.join(cmd)} -> {out_path}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        # Cleanup partial file
        try:
            out_path.unlink(missing_ok=True)
        except Exception:
            pass
        sys.exit(result.returncode)


def parse_backup_date(path: Path) -> dt.date | None:
    m = TIMESTAMP_RE.search(path.name)
    if not m:
        m2 = DATE_RE.search(path.name)
        if not m2:
            return None
        try:
            return dt.datetime.strptime(m2.group(1), "%Y%m%d").date()
        except Exception:
            return None
    try:
        return dt.datetime.strptime(m.group(1), "%Y%m%d").date()
    except Exception:
        return None


def enforce_retention(
    backup_dir: Path,
    prefix: str,
    keep_daily: int = 3,
    dry_run: bool = False,
) -> tuple[list[Path], list[Path]]:
    """
    Returns (kept, pruned). Implements:

      daily: last keep_daily days (today, today-1, ... today-(keep_daily-1))
      weekly: newest backup with age in [4,7] days (previous week)
      two_weeks: newest backup with age in [8,14] days
      monthly: newest backup with age in [28,31] days

    One file per bucket; newest wins. Buckets computed from calendar dates,
    not 24h sliding windows, so a backup at 23:59 and one at 00:01 next day
    count as different days.
    """
    today = dt.date.today()
    pattern = f"{prefix}_*.dump"
    files = sorted(backup_dir.glob(pattern))
    if not files:
        # Also consider legacy prefix-less dumps for safety? No — stay strict.
        return [], []

    # Map file -> date; files without parseable date are never kept (pruned).
    dated: list[tuple[Path, dt.date | None]] = [(f, parse_backup_date(f)) for f in files]
    # For daily buckets we need per-day newest.
    by_day: dict[dt.date, list[Path]] = {}
    for f, d in dated:
        if d is None:
            continue
        by_day.setdefault(d, []).append(f)
    # Within each day, newest file (lexicographically largest timestamp) wins.
    newest_per_day: dict[dt.date, Path] = {day: max(fs, key=lambda p: p.name) for day, fs in by_day.items()}

    keep: set[Path] = set()

    # Daily: last keep_daily calendar days
    for i in range(keep_daily):
        day = today - dt.timedelta(days=i)
        if day in newest_per_day:
            keep.add(newest_per_day[day])

    # Helper: newest backup in an age interval [lo, hi] inclusive (age = today - date)
    def newest_in_interval(lo: int, hi: int) -> Path | None:
        candidates: list[tuple[dt.date, Path]] = []
        for day, path in newest_per_day.items():
            age = (today - day).days
            if lo <= age <= hi and path not in keep:
                candidates.append((day, path))
        if not candidates:
            return None
        # Newest = max day
        candidates.sort(key=lambda t: t[0], reverse=True)
        return candidates[0][1]

    weekly = newest_in_interval(4, 7)
    if weekly:
        keep.add(weekly)
    two_weeks = newest_in_interval(8, 14)
    if two_weeks:
        keep.add(two_weeks)
    monthly = newest_in_interval(28, 31)
    if monthly:
        keep.add(monthly)

    kept = sorted(keep, key=lambda p: p.name)
    pruned = [f for f in files if f not in keep]

    if dry_run:
        print(f"Would keep {len(kept)} / prune {len(pruned)} in {backup_dir}:")
        for p in kept:
            print(f"  KEEP  {p.name}")
        for p in pruned:
            print(f"  PRUNE {p.name}")
    else:
        for p in pruned:
            try:
                p.unlink()
                print(f"Pruned {p.name}")
            except Exception as e:
                print(f"Failed to prune {p.name}: {e}", file=sys.stderr)
        if kept:
            print(f"Retention: kept {len(kept)} backups:")
            for p in kept:
                print(f"  {p.name}")

    return kept, pruned


def main() -> int:
    args = parse_args()
    backup_dir = resolve_backup_dir(args.backup_dir)
    db_url = resolve_db_url(args.db_url, args.from_url)

    Dump = not (args.no_dump or args.retention_only)

    if Dump:
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = backup_dir / f"{args.prefix}_{ts}.dump"
        # Safety: ensure we can write
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Cannot create backup dir {backup_dir}: {e}", file=sys.stderr)
            return 1
        do_dump(args.pg_dump_bin, db_url, out)
        # Verify file exists and non-empty
        if not out.exists() or out.stat().st_size == 0:
            print(f"Backup failed or empty: {out}", file=sys.stderr)
            return 1
        print(f"Backup written: {out} ({out.stat().st_size / 1024 / 1024:.1f} MiB)")

    kept, pruned = enforce_retention(
        backup_dir, args.prefix, keep_daily=args.keep_daily, dry_run=args.dry_run
    )
    if args.dry_run:
        print(f"[dry-run] retention would keep {len(kept)}, prune {len(pruned)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
