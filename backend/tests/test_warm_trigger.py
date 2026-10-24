"""Tests for the on-demand cache warm-up trigger."""

import pytest
from fastapi.testclient import TestClient

import backend.main as main
from backend.main import _cache_warm_enabled, app

client = TestClient(app)


def test_default_is_on_for_prod_off_for_previews(monkeypatch):
    monkeypatch.delenv("PREWARM_CACHE", raising=False)
    assert _cache_warm_enabled("PREWARM_CACHE", preview=False) is True
    assert _cache_warm_enabled("PREWARM_CACHE", preview=True) is False


def test_preview_can_opt_in_explicitly(monkeypatch):
    monkeypatch.setenv("PREWARM_CACHE", "true")
    assert _cache_warm_enabled("PREWARM_CACHE", preview=True) is True


def test_explicit_false_disables_prod(monkeypatch):
    monkeypatch.setenv("PREWARM_CACHE", "false")
    assert _cache_warm_enabled("PREWARM_CACHE", preview=False) is False


def test_empty_value_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("CACHE_AUTO_REWARM", "  ")
    assert _cache_warm_enabled("CACHE_AUTO_REWARM", preview=True) is False
    assert _cache_warm_enabled("CACHE_AUTO_REWARM", preview=False) is True


def test_warm_endpoint_disabled_without_token(monkeypatch):
    monkeypatch.delenv("CACHE_WARM_TOKEN", raising=False)
    response = client.post("/api/cache/warm")
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


def test_warm_endpoint_rejects_bad_token(monkeypatch):
    monkeypatch.setenv("CACHE_WARM_TOKEN", "s3cret")
    response = client.post("/api/cache/warm", headers={"x-cache-warm-token": "wrong"})
    assert response.status_code == 403
    assert "invalid" in response.json()["detail"].lower()


def test_warm_endpoint_starts_a_warm(monkeypatch):
    monkeypatch.setenv("CACHE_WARM_TOKEN", "s3cret")
    calls = []

    def fake_prewarm(trigger="startup"):
        calls.append(trigger)
        return True

    monkeypatch.setattr(main, "_prewarm_cache", fake_prewarm)
    response = client.post("/api/cache/warm", headers={"x-cache-warm-token": "s3cret"})
    assert response.status_code == 202
    assert response.json()["started"] is True
    assert calls == ["http"]


def test_warm_endpoint_conflict_when_already_running(monkeypatch):
    monkeypatch.setenv("CACHE_WARM_TOKEN", "s3cret")
    monkeypatch.setattr(main, "_prewarm_cache", lambda trigger="startup": False)
    response = client.post("/api/cache/warm", headers={"x-cache-warm-token": "s3cret"})
    assert response.status_code == 409


def test_prewarm_returns_false_when_already_running():
    # The in-process lock is a real threading.Lock: hold it and expect a skip.
    assert main._warm_running.acquire(blocking=False)
    try:
        assert main._prewarm_cache(trigger="test") is False
    finally:
        main._warm_running.release()
