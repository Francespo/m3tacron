#!/usr/bin/env python3
"""Print a first-party traffic report: page views, sessions, DAU/WAU/MAU.

Reads the ``PageView`` table filled by ``POST /api/analytics/collect`` (see
``backend/api/analytics.py`` and ``docs/ANALYTICS.md``). Automated requests are
reported separately and excluded from the visitor/session numbers.

Examples:
    python3 scripts/analytics_report.py
    python3 scripts/analytics_report.py --days 90 --json
    DATABASE_URL=postgres://... python3 scripts/analytics_report.py

On the Coolify host, run it inside the backend container:
    docker exec <backend-container> python scripts/analytics_report.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import func  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from backend.database import engine  # noqa: E402
from backend.models import PageView  # noqa: E402


def _count(session: Session, *conditions, column=PageView.id, distinct: bool = False) -> int:
    expr = func.count(func.distinct(column)) if distinct else func.count(column)
    return int(session.exec(select(expr).where(*conditions)).one() or 0)


def build_report(days: int) -> dict:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    human = PageView.is_bot.is_(False)  # type: ignore[attr-defined]
    automated = PageView.is_bot.is_(True)  # type: ignore[attr-defined]

    with Session(engine) as session:
        def visitors_since(after: timedelta) -> int:
            return _count(
                session,
                PageView.ts >= now - after,
                human,
                column=PageView.visitor_id,
                distinct=True,
            )

        human_views = _count(session, PageView.ts >= since, human)
        bot_views = _count(session, PageView.ts >= since, automated)
        daily_rows = session.exec(
            select(
                func.date(PageView.ts).label("day"),
                func.count(PageView.id).label("pageviews"),
                func.count(func.distinct(PageView.visitor_id)).label("visitors"),
            )
            .where(PageView.ts >= since, human)
            .group_by("day")
            .order_by("day")
        ).all()
        top_paths = session.exec(
            select(PageView.path, func.count(PageView.id).label("views"))
            .where(PageView.ts >= since, human)
            .group_by(PageView.path)
            .order_by(func.count(PageView.id).desc())
            .limit(25)
        ).all()
        top_referrers = session.exec(
            select(PageView.referrer_host, func.count(PageView.id).label("views"))
            .where(PageView.ts >= since, human, PageView.referrer_host.is_not(None))
            .group_by(PageView.referrer_host)
            .order_by(func.count(PageView.id).desc())
            .limit(15)
        ).all()

        return {
            "generated_at": now.isoformat(),
            "window_days": days,
            "since": since.isoformat(),
            "pageviews": human_views,
            "visitors": _count(session, PageView.ts >= since, human, column=PageView.visitor_id, distinct=True),
            "sessions": _count(session, PageView.ts >= since, human, column=PageView.session_id, distinct=True),
            "automated_pageviews": bot_views,
            "dau": visitors_since(timedelta(days=1)),
            "wau": visitors_since(timedelta(days=7)),
            "mau": visitors_since(timedelta(days=30)),
            "daily": [
                {"date": str(row[0]), "pageviews": int(row[1]), "visitors": int(row[2])}
                for row in daily_rows
            ],
            "top_paths": [{"path": row[0], "views": int(row[1])} for row in top_paths],
            "top_referrers": [{"host": row[0], "views": int(row[1])} for row in top_referrers],
        }


def print_report(report: dict) -> None:
    total_events = report["pageviews"] + report["automated_pageviews"]
    bot_share = (report["automated_pageviews"] / total_events * 100) if total_events else 0.0

    print(f"M3tacron traffic report — last {report['window_days']} days")
    print(f"since {report['since']}\n")
    print(f"  Page views (humans)   {report['pageviews']:>8}")
    print(f"  Unique visitors       {report['visitors']:>8}")
    print(f"  Sessions              {report['sessions']:>8}")
    print(f"  Automated page views  {report['automated_pageviews']:>8}  ({bot_share:.0f}% of all events)")
    print()
    print(f"  DAU (24h)             {report['dau']:>8}")
    print(f"  WAU (7d)              {report['wau']:>8}")
    print(f"  MAU (30d)             {report['mau']:>8}")

    if not report["daily"]:
        print("\nNo human page views recorded yet.")
        return

    print("\nDaily")
    print(f"  {'date':<12}{'views':>8}{'visitors':>10}")
    for row in report["daily"]:
        print(f"  {row['date']:<12}{row['pageviews']:>8}{row['visitors']:>10}")

    print("\nTop pages")
    for row in report["top_paths"]:
        print(f"  {row['views']:>7}  {row['path']}")

    if report["top_referrers"]:
        print("\nTop external referrers")
        for row in report["top_referrers"]:
            print(f"  {row['views']:>7}  {row['host']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=30, help="window size in days (default: 30)")
    parser.add_argument("--json", action="store_true", help="print the raw report as JSON")
    args = parser.parse_args()

    if args.days < 1:
        parser.error("--days must be >= 1")

    if not os.getenv("DATABASE_URL"):
        print(
            "note: DATABASE_URL is not set, falling back to the local SQLite test.db\n",
            file=sys.stderr,
        )

    try:
        report = build_report(args.days)
    except Exception as exc:
        print(f"failed to read analytics data: {exc}", file=sys.stderr)
        print(
            "hint: the pageview table is created by the backend on startup; make sure "
            "DATABASE_URL points at the production database.",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
