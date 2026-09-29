"""First-party, cookie-less traffic analytics.

The SvelteKit frontend posts one anonymous event per page view to
``POST /api/analytics/collect``. Nothing that identifies a person is stored:
no IP address, no user agent, no cookie, no full referrer URL. See
``docs/ANALYTICS.md``.

Two ways to read the data:

* ``scripts/analytics_report.py`` — direct database read, works anywhere the
  backend can reach the database (the normal path).
* ``GET /api/analytics/summary`` — HTTP read for quick checks, only enabled
  when the ``ANALYTICS_ADMIN_TOKEN`` environment variable is set.
"""
from __future__ import annotations

import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import Session, select

from ..database import engine
from ..models import PageView

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Only these hosts may post events, so a stray script or a scanner cannot
# inflate the counters. Override with ANALYTICS_ALLOWED_HOSTS (comma separated)
# to test from a preview deployment such as 123.dev.m3tacron.com.
DEFAULT_ALLOWED_HOSTS = "m3tacron.com,www.m3tacron.com"

# Automated clients do not run the tracking script themselves, but
# JavaScript-rendering crawlers, link previewers and uptime monitors do. They
# are flagged instead of dropped, so reports can show how much of the traffic
# is automated.
_BOT_UA = re.compile(
    r"(bot|crawler|crawl|spider|slurp|bingpreview|yandex|baidu|duckduckbot|"
    r"semrush|ahrefs|mj12|dotbot|petalbot|facebookexternalhit|whatsapp|telegram|"
    r"python-requests|python-httpx|httpx|curl|wget|headlesschrome|puppeteer|"
    r"playwright|lighthouse|pingdom|uptime|monitor|scrapy|go-http-client|okhttp)",
    re.IGNORECASE,
)

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,64}$")


class PageViewEvent(BaseModel):
    """Payload sent by the frontend tracker."""

    path: str = Field(min_length=1, max_length=512)
    visitor_id: str | None = Field(default=None, max_length=64)
    session_id: str | None = Field(default=None, max_length=64)
    referrer_host: str | None = Field(default=None, max_length=255)


def _allowed_hosts() -> set[str]:
    raw = os.getenv("ANALYTICS_ALLOWED_HOSTS", DEFAULT_ALLOWED_HOSTS)
    return {host.strip().lower() for host in raw.split(",") if host.strip()}


def _request_host(request: Request) -> str | None:
    """Return the host that issued the request, from Origin or Referer."""
    for header in ("origin", "referer"):
        value = request.headers.get(header)
        if not value:
            continue
        try:
            host = urlsplit(value).hostname
        except ValueError:
            continue
        if host:
            return host.lower()
    return None


def _clean_id(value: str | None) -> str | None:
    if value and _ID_RE.match(value):
        return value
    return None


def _clean_referrer(value: str | None) -> str | None:
    if not value:
        return None
    host = value.strip().lower()
    if not host or len(host) > 255 or "/" in host:
        return None
    return host


@router.post("/collect", status_code=status.HTTP_202_ACCEPTED)
def collect_page_view(event: PageViewEvent, request: Request) -> dict[str, bool]:
    """Record one anonymous page view. Never fails the caller's page."""
    host = _request_host(request)
    if host is None or host not in _allowed_hosts():
        raise HTTPException(status_code=403, detail="origin not allowed")

    # Keep only the route: query strings and fragments are filters/search terms
    # that are not needed to count usage or build a top-pages report.
    path = event.path.split("?", 1)[0].split("#", 1)[0][:512]
    if not path.startswith("/"):
        raise HTTPException(status_code=422, detail="path must be absolute")

    user_agent = request.headers.get("user-agent", "") or ""
    row = PageView(
        path=path,
        visitor_id=_clean_id(event.visitor_id),
        session_id=_clean_id(event.session_id),
        referrer_host=_clean_referrer(event.referrer_host),
        is_bot=bool(_BOT_UA.search(user_agent)),
    )

    try:
        with Session(engine) as session:
            session.add(row)
            session.commit()
    except Exception as exc:  # pragma: no cover - defensive, analytics is best-effort
        logger.warning("analytics collect failed: %s", exc)
        return {"ok": False}

    return {"ok": True}


def _count(session: Session, *conditions, column=PageView.id, distinct: bool = False) -> int:
    expr = func.count(func.distinct(column)) if distinct else func.count(column)
    result = session.exec(select(expr).where(*conditions)).one()
    return int(result or 0)


@router.get("/summary")
def analytics_summary(
    days: int = Query(default=30, ge=1, le=365),
    x_analytics_token: str | None = Header(default=None),
) -> dict:
    """Return usage totals for the last ``days`` days plus DAU/WAU/MAU.

    Disabled unless ``ANALYTICS_ADMIN_TOKEN`` is configured on the server;
    callers pass the same value in the ``X-Analytics-Token`` header.
    """
    expected = os.getenv("ANALYTICS_ADMIN_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="analytics summary disabled: ANALYTICS_ADMIN_TOKEN is not set",
        )
    if not x_analytics_token or not secrets.compare_digest(x_analytics_token, expected):
        raise HTTPException(status_code=403, detail="invalid analytics token")

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    human = PageView.is_bot.is_(False)  # type: ignore[attr-defined]
    automated = PageView.is_bot.is_(True)  # type: ignore[attr-defined]

    with Session(engine) as session:
        pageviews = _count(session, PageView.ts >= since, human)
        visitors = _count(session, PageView.ts >= since, human, column=PageView.visitor_id, distinct=True)
        sessions = _count(session, PageView.ts >= since, human, column=PageView.session_id, distinct=True)
        bots = _count(session, PageView.ts >= since, automated)

        def visitors_since(after: timedelta) -> int:
            return _count(
                session,
                PageView.ts >= now - after,
                human,
                column=PageView.visitor_id,
                distinct=True,
            )

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
            .limit(20)
        ).all()

        top_referrers = session.exec(
            select(PageView.referrer_host, func.count(PageView.id).label("views"))
            .where(PageView.ts >= since, human, PageView.referrer_host.is_not(None))
            .group_by(PageView.referrer_host)
            .order_by(func.count(PageView.id).desc())
            .limit(20)
        ).all()

    return {
        "window_days": days,
        "pageviews": pageviews,
        "visitors": visitors,
        "sessions": sessions,
        "automated_pageviews": bots,
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
