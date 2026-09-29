"""Tests for the first-party page-view analytics endpoint."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.database import create_db_and_tables, engine
from backend.main import app
from backend.models import PageView

client = TestClient(app)

TEST_VISITOR = "test-analytics-visitor"
TEST_SESSION = "test-analytics-session"
HUMAN_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

ORIGIN_HEADERS = {"Origin": "https://m3tacron.com"}


def setup_module():
    create_db_and_tables()


def teardown_module():
    _delete_test_rows()


def _delete_test_rows() -> None:
    with Session(engine) as session:
        for row in session.exec(select(PageView).where(PageView.visitor_id == TEST_VISITOR)).all():
            session.delete(row)
        session.commit()


def _rows() -> list[PageView]:
    with Session(engine) as session:
        return list(session.exec(select(PageView).where(PageView.visitor_id == TEST_VISITOR)).all())


def test_collect_records_human_page_view():
    _delete_test_rows()
    response = client.post(
        "/api/analytics/collect",
        json={
            "path": "/pilot/avenger",
            "visitor_id": TEST_VISITOR,
            "session_id": TEST_SESSION,
            "referrer_host": "reddit.com",
        },
        headers={**ORIGIN_HEADERS, "User-Agent": HUMAN_UA},
    )
    assert response.status_code == 202
    assert response.json() == {"ok": True}

    rows = _rows()
    assert len(rows) == 1
    assert rows[0].path == "/pilot/avenger"
    assert rows[0].session_id == TEST_SESSION
    assert rows[0].referrer_host == "reddit.com"
    assert rows[0].is_bot is False
    assert rows[0].ts is not None


def test_collect_flags_bots_but_keeps_the_row():
    _delete_test_rows()
    response = client.post(
        "/api/analytics/collect",
        json={"path": "/lists", "visitor_id": TEST_VISITOR, "session_id": TEST_SESSION},
        headers={**ORIGIN_HEADERS, "User-Agent": GOOGLEBOT_UA},
    )
    assert response.status_code == 202

    rows = _rows()
    assert len(rows) == 1
    assert rows[0].is_bot is True


def test_collect_drops_query_string():
    _delete_test_rows()
    response = client.post(
        "/api/analytics/collect",
        json={"path": "/lists?faction=rebel&sort=games#top", "visitor_id": TEST_VISITOR},
        headers={**ORIGIN_HEADERS, "User-Agent": HUMAN_UA},
    )
    assert response.status_code == 202
    assert _rows()[0].path == "/lists"


def test_collect_rejects_unknown_origin():
    _delete_test_rows()
    response = client.post(
        "/api/analytics/collect",
        json={"path": "/", "visitor_id": TEST_VISITOR},
        headers={"Origin": "https://evil.example", "User-Agent": HUMAN_UA},
    )
    assert response.status_code == 403
    assert _rows() == []


def test_collect_accepts_proxied_request_through_payload_host():
    """The SvelteKit same-origin proxy drops Origin/Referer headers."""
    _delete_test_rows()
    response = client.post(
        "/api/analytics/collect",
        json={"path": "/ships", "host": "m3tacron.com", "visitor_id": TEST_VISITOR},
        headers={"User-Agent": HUMAN_UA},
    )
    assert response.status_code == 202
    assert len(_rows()) == 1


def test_collect_rejects_request_without_any_host():
    response = client.post(
        "/api/analytics/collect",
        json={"path": "/", "visitor_id": TEST_VISITOR},
        headers={"User-Agent": HUMAN_UA},
    )
    assert response.status_code == 403


def test_collect_rejects_relative_path():
    response = client.post(
        "/api/analytics/collect",
        json={"path": "lists", "visitor_id": TEST_VISITOR},
        headers={**ORIGIN_HEADERS, "User-Agent": HUMAN_UA},
    )
    assert response.status_code == 422


def test_collect_rejects_oversized_identifiers():
    response = client.post(
        "/api/analytics/collect",
        json={"path": "/", "visitor_id": "x" * 65},
        headers={**ORIGIN_HEADERS, "User-Agent": HUMAN_UA},
    )
    assert response.status_code == 422


def test_summary_is_disabled_without_token(monkeypatch):
    monkeypatch.delenv("ANALYTICS_ADMIN_TOKEN", raising=False)
    response = client.get("/api/analytics/summary")
    assert response.status_code == 503


def test_summary_requires_the_configured_token(monkeypatch):
    monkeypatch.setenv("ANALYTICS_ADMIN_TOKEN", "test-token")
    assert client.get("/api/analytics/summary").status_code == 403
    assert (
        client.get("/api/analytics/summary", headers={"X-Analytics-Token": "wrong"}).status_code
        == 403
    )

    response = client.get("/api/analytics/summary", headers={"X-Analytics-Token": "test-token"})
    assert response.status_code == 200
    data = response.json()
    assert set(data) >= {
        "pageviews",
        "visitors",
        "sessions",
        "automated_pageviews",
        "dau",
        "wau",
        "mau",
        "daily",
        "top_paths",
    }
