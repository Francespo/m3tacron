"""Tests for the API bot guard middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.bot_guard import (
    BotGuardMiddleware,
    classify_user_agent,
    client_ip,
    is_internal,
)

CHROME_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
CUBOT_UA = (
    "Mozilla/5.0 (Linux; Android 10; CUBOT X19) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
)
GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


def make_client(client_ip="1.2.3.4", **middleware_kwargs):
    app = FastAPI()

    @app.get("/")
    def root():
        return {"status": "ok"}

    @app.get("/api/ships")
    def ships():
        return {"ok": True}

    @app.get("/api/meta-snapshot")
    def meta():
        return {"ok": True}

    @app.post("/api/support/webhook/kofi")
    def kofi():
        return {"ok": True}

    app.add_middleware(BotGuardMiddleware, **middleware_kwargs)
    return TestClient(app, client=(client_ip, 50000))


def test_classify_user_agent():
    assert classify_user_agent(CHROME_UA) == "browser"
    assert classify_user_agent(CUBOT_UA) == "browser"
    assert classify_user_agent(GOOGLEBOT_UA) == "bot"
    assert classify_user_agent("python-requests/2.32.3") == "scripted"
    assert classify_user_agent("") == "scripted"


@pytest.mark.parametrize(
    "ua",
    [
        GOOGLEBOT_UA,
        "Mozilla/5.0 (compatible; bingbot/2.0)",
        "Mozilla/5.0 (compatible; AhrefsBot/7.0)",
        "Mozilla/5.0 (compatible; GPTBot/1.1)",
        "Mozilla/5.0 (compatible; SemrushBot/7)",
        "Mozilla/5.0 HeadlessChrome/120.0.0.0",
    ],
)
def test_known_bots_blocked_on_api(ua):
    client = make_client()
    response = client.get("/api/ships", headers={"user-agent": ua})
    assert response.status_code == 403
    assert "crawling" in response.json()["detail"].lower()


def test_bot_allowed_on_root_and_docs():
    client = make_client()
    assert client.get("/", headers={"user-agent": GOOGLEBOT_UA}).status_code == 200


def test_browser_is_not_limited_at_normal_rates():
    client = make_client(rate_default=2, rate_heavy=2)
    for _ in range(2):
        assert client.get("/api/ships", headers={"user-agent": CHROME_UA}).status_code == 200


def test_heavy_endpoint_budget_enforced():
    client = make_client(rate_heavy=2)
    for _ in range(2):
        assert client.get("/api/ships", headers={"user-agent": CHROME_UA}).status_code == 200
    blocked = client.get("/api/ships", headers={"user-agent": CHROME_UA})
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"] == "60"


def test_scripted_client_uses_scripted_budget():
    client = make_client(rate_scripted=2)
    for _ in range(2):
        assert client.get("/api/meta-snapshot", headers={"user-agent": "curl/8.5.0"}).status_code == 200
    assert client.get("/api/meta-snapshot", headers={"user-agent": "curl/8.5.0"}).status_code == 429


def test_missing_user_agent_counts_as_scripted():
    client = make_client(rate_scripted=1)
    assert client.get("/api/meta-snapshot", headers={"user-agent": ""}).status_code == 200
    assert client.get("/api/meta-snapshot", headers={"user-agent": ""}).status_code == 429


def test_options_preflight_never_blocked():
    client = make_client()
    response = client.options("/api/ships", headers={"user-agent": GOOGLEBOT_UA})
    assert response.status_code != 403


def test_webhook_exempt_from_bot_blocking():
    client = make_client()
    response = client.post("/api/support/webhook/kofi", headers={"user-agent": "Ko-fi/1.0"})
    assert response.status_code == 200


def test_internal_peer_is_never_limited():
    client = make_client(client_ip="127.0.0.1", rate_heavy=1)
    for _ in range(5):
        assert client.get("/api/ships", headers={"user-agent": GOOGLEBOT_UA}).status_code == 200


def test_spoofed_forwarded_for_cannot_bypass_limit():
    client = make_client(rate_heavy=1)
    headers = {"user-agent": CHROME_UA, "x-forwarded-for": "8.8.8.8, 9.9.9.9"}
    assert client.get("/api/ships", headers=headers).status_code == 200
    # Different spoofed left hop, same real peer (last hop) -> still limited.
    headers["x-forwarded-for"] = "1.1.1.1, 9.9.9.9"
    assert client.get("/api/ships", headers=headers).status_code == 429


def test_can_be_disabled():
    client = make_client(enabled=False)
    response = client.get("/api/ships", headers={"user-agent": GOOGLEBOT_UA})
    assert response.status_code == 200


def test_client_ip_and_internal_helpers():
    from starlette.datastructures import Headers

    scope = {"type": "http", "client": ("10.0.0.5", 1234)}
    headers = Headers(headers={"x-forwarded-for": "6.6.6.6, 203.0.113.9"})

    assert client_ip(scope, headers) == "203.0.113.9"
    assert is_internal("127.0.0.1")
    assert is_internal("10.0.2.15")
    assert not is_internal("203.0.113.9")
    assert not is_internal("testclient")
