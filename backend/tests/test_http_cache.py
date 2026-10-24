from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.cache import force_refresh_active
from backend.http_cache import CacheRefreshMiddleware, HttpCacheMiddleware


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(HttpCacheMiddleware)
    app.add_middleware(CacheRefreshMiddleware)

    @app.get("/api/thing")
    def thing():
        return {"ok": True, "forced": force_refresh_active()}

    @app.get("/api/cache/stats")
    def stats():
        return {"entries": 1}

    return app


def test_json_get_gets_etag_and_cache_control():
    client = TestClient(_make_app())
    res = client.get("/api/thing")
    assert res.status_code == 200
    assert res.headers["etag"].startswith('W/"')
    assert "max-age=" in res.headers["cache-control"]
    assert "stale-while-revalidate=" in res.headers["cache-control"]


def test_matching_etag_returns_304_without_body():
    client = TestClient(_make_app())
    first = client.get("/api/thing")
    res = client.get("/api/thing", headers={"if-none-match": first.headers["etag"]})
    assert res.status_code == 304
    assert res.content == b""
    assert res.headers["etag"] == first.headers["etag"]


def test_stale_generation_is_not_served_to_the_warm_up():
    # A public peer cannot force recomputations...
    external = TestClient(_make_app(), client=("8.8.8.8", 12345))
    assert external.get("/api/thing", headers={"x-cache-refresh": "1"}).json()["forced"] is False
    # ...but loopback can (the warm-up probes come from 127.0.0.1).
    internal = TestClient(_make_app(), client=("127.0.0.1", 12345))
    assert internal.get("/api/thing", headers={"x-cache-refresh": "1"}).json()["forced"] is True


def test_cache_stats_is_not_http_cached():
    client = TestClient(_make_app())
    res = client.get("/api/cache/stats")
    assert res.status_code == 200
    assert "etag" not in res.headers
    assert "cache-control" not in res.headers
