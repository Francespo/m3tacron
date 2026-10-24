"""HTTP caching for the public analytics API.

Every ``GET /api/*`` response is a pure function of the data version, so it is
safe to let browsers and proxies reuse it for a short window and revalidate it
afterwards with an ETag. Revalidation is cheap (a hash, no database access) and
turns repeat visits into 304s instead of downloading the payload again — the
dashboard snapshot alone is ~2 MB (~235 KB gzipped).

Two middlewares live here:

``HttpCacheMiddleware``
    Adds ``ETag`` and ``Cache-Control`` to JSON GET responses and answers
    ``If-None-Match`` with 304. The tag is weak because the proxy may gzip the
    body before it reaches the client.

``CacheRefreshMiddleware``
    Lets the warm-up force a recompute (``x-cache-refresh: 1``) so it does not
    read the previous generation. Accepted only from loopback/private peers:
    an anonymous client must not be able to force expensive recomputations.

Environment variables (optional):

  HTTP_CACHE_MAX_AGE_SECONDS   browser max-age (default 60)
  HTTP_CACHE_SWR_SECONDS       stale-while-revalidate window (default 600)
"""

from __future__ import annotations

import hashlib
import os

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .bot_guard import client_ip, is_internal
from .cache import reset_force_refresh, set_force_refresh

# The warm trigger and the live cache statistics change on every request.
_UNCACHEABLE_PREFIXES = ("/api/cache/", "/api/support")

_MAX_AGE = int(os.getenv("HTTP_CACHE_MAX_AGE_SECONDS", "60"))
_STALE_WHILE_REVALIDATE = int(os.getenv("HTTP_CACHE_SWR_SECONDS", "600"))

_CACHE_CONTROL = f"public, max-age={_MAX_AGE}, stale-while-revalidate={_STALE_WHILE_REVALIDATE}"

_HOP_HEADERS = (b"etag", b"cache-control")


def _etag_matches(if_none_match: str, etag: str) -> bool:
    """Weak comparison of an If-None-Match header against our ETag."""
    if not if_none_match:
        return False
    if if_none_match.strip() == "*":
        return True
    ours = etag[2:] if etag.startswith("W/") else etag
    for candidate in if_none_match.split(","):
        candidate = candidate.strip()
        if candidate.startswith("W/"):
            candidate = candidate[2:]
        if candidate == ours:
            return True
    return False


class HttpCacheMiddleware:
    """ETag + Cache-Control on JSON GET responses, with 304 support."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "GET":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        if not path.startswith("/api/") or path.startswith(_UNCACHEABLE_PREFIXES):
            await self.app(scope, receive, send)
            return

        if_none_match = Headers(scope=scope).get("if-none-match", "")
        start: Message | None = None
        chunks: list[bytes] = []

        async def send_cached(message: Message) -> None:
            nonlocal start
            if message["type"] == "http.response.start":
                start = message
                return
            if message["type"] != "http.response.body":
                await send(message)
                return
            chunks.append(message.get("body", b""))
            if message.get("more_body", False):
                return
            await _flush()

        async def _flush() -> None:
            assert start is not None
            status = start["status"]
            raw_headers = list(start.get("headers", []))
            content_type = ""
            for key, value in raw_headers:
                if key.lower() == b"content-type":
                    content_type = value.decode("latin-1")
                    break

            if status != 200 or "application/json" not in content_type:
                await send(start)
                await send({"type": "http.response.body", "body": b"".join(chunks)})
                return

            body = b"".join(chunks)
            etag = 'W/"' + hashlib.md5(body).hexdigest() + '"'
            headers = [
                (k, v) for k, v in raw_headers if k.lower() not in _HOP_HEADERS
            ]
            headers.append((b"etag", etag.encode("latin-1")))
            headers.append((b"cache-control", _CACHE_CONTROL.encode("latin-1")))

            if _etag_matches(if_none_match, etag):
                await send(
                    {
                        "type": "http.response.start",
                        "status": 304,
                        "headers": headers,
                    }
                )
                await send({"type": "http.response.body", "body": b""})
                return

            await send({**start, "headers": headers})
            await send({"type": "http.response.body", "body": body})

        await self.app(scope, receive, send_cached)


class CacheRefreshMiddleware:
    """Honour ``x-cache-refresh`` from internal peers for the warm-up."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            if headers.get("x-cache-refresh") and is_internal(
                client_ip(scope, headers)
            ):
                token = set_force_refresh(True)
                try:
                    await self.app(scope, receive, send)
                finally:
                    reset_force_refresh(token)
                return
        await self.app(scope, receive, send)
