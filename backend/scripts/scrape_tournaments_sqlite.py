"""
Wrapper for running tournament scraping with a local SQLite database.

Usage:
    python -m backend.scripts.scrape_tournaments_sqlite --sqlite-path scraped_tournaments.db \
        --platform longshanks+rollbetter --time-range 7

All extra arguments are forwarded to backend.scripts.scrape_tournaments.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description=(
            "Run the tournament scraper using a local SQLite database as the "
            "primary data store."
        )
    )
    parser.add_argument(
        "--sqlite-path",
        default="scraped_tournaments.db",
        help=(
            "Path to the SQLite database file to create/use. "
            "Default: scraped_tournaments.db"
        ),
    )
    args, remaining = parser.parse_known_args()
    return args, remaining


def main() -> int:
    args, remaining = _parse_args()

    sqlite_path = Path(args.sqlite_path).expanduser().resolve()
    if sqlite_path.parent != Path(""):
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure the scrape script uses SQLite as the primary database.
    os.environ["DATABASE_URL"] = f"sqlite:///{sqlite_path}"

    # Defer import until after DATABASE_URL is set so database.py picks it up.
    from backend.scripts import scrape_tournaments

    sys.argv = ["scrape_tournaments"] + remaining
    return scrape_tournaments.main()


if __name__ == "__main__":
    raise SystemExit(main())
