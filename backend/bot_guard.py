"""
Bot guard for the public API.

Several endpoints run full-table aggregations over the whole tournament
history (ships, lists, squadrons, pilot/card details). They are expensive by
design, so a single scripted client looping over them can saturate the
database. This middleware rejects known crawlers and rate-limits scripted
clients per IP before the request reaches a handler.

Rules:

- Only ``/api/*`` is guarded. ``/``, ``/docs``, ``/openapi.json`` and CORS
  preflights always pass, and the Ko-fi webhook is exempt.
- Known crawlers (Googlebot, Ahrefs, GPTBot, headless browsers, ...) get a
  403 on the API. They can still crawl the rendered HTML: the SvelteKit pages
  are server-rendered and never go through the public ``/api`` path.
- Scripted clients (curl, python-requests, empty User-Agent, ...) are allowed
  so local tooling keeps working, but with a strict per-minute budget.
- The client IP is the *last* ``X-Forwarded-For`` entry. Traefik appends the
  real peer address, so everything to its left is client-supplied and must
  not be trusted.
- Loopback and private peers (health checks, warm-up probes, other
  containers) are never limited.

Counters live in process memory, so with N uvicorn workers the effective
limit is N times the configured value. That is intentional: this is abuse
protection, not billing.

Environment variables (all optional):

  BOT_GUARD_ENABLED          default "true"
  BOT_GUARD_RATE_DEFAULT     requests/minute for browser traffic (default 120)
  BOT_GUARD_RATE_HEAVY       requests/minute for expensive endpoints (default 40)
  BOT_GUARD_RATE_SCRIPTED    requests/minute for scripted clients (default 20)
  BOT_GUARD_WINDOW_SECONDS   sliding window size (default 60)
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
import threading
import time
from collections import deque

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

# Crawlers, scrapers and headless browsers. Deliberately a list of known
# tokens instead of a bare "bot" substring: "bot" alone matches real phones
# such as CUBOT devices.
BOT_PATTERN = re.compile(
    r"(?:"
    r"googlebot|google-inspectiontool|storebot-google|adsbot-google|apis-google|"
    r"mediapartners-google|feedfetcher-google|"
    r"bingbot|msnbot|adidxbot|yandexbot|yandex\.com/bots|baiduspider|duckduckbot|"
    r"slurp|sogou|exabot|petalbot|bytespider|"
    r"ahrefsbot|semrushbot|mj12bot|dotbot|seznambot|blexbot|"
    r"gptbot|chatgpt-user|oai-searchbot|ccbot|claudebot|claude-web|anthropic-ai|"
    r"perplexitybot|amazonbot|applebot|"
    r"facebookexternalhit|twitterbot|linkedinbot|redditbot|discordbot|"
    r"telegrambot|pinterestbot|embedly|quora link preview|vkshare|"
    r"w3c_validator|ia_archiver|archive\.org_bot|archivebot|commoncrawl|"
    r"headlesschrome|phantomjs|selenium|puppeteer|playwright|"
    r"crawler|spider|scraper"
    r")",
    re.IGNORECASE,
)

# Command-line and library HTTP clients: legitimate for local tooling and
# monitoring, but a loop through the analytics endpoints from one of these is
# the classic way to melt the database.
SCRIPTED_PATTERN = re.compile(
    r"(?:"
    r"python-requests|python-httpx|python-urllib|aiohttp|httpx|"
    r"curl/|wget/|libwww-perl|httpclient|"
    r"go-http-client|java/|okhttp|node-fetch|axios/|undici|got/|"
    r"postmanruntime|insomnia|powershell"
    r")",
    re.IGNORECASE,
)

# Endpoints that trigger a full history aggregation are worth a tighter
# budget than the rest of the API.
HEAVY_PREFIXES = (
    "/api/ships",
    "/api/lists",
    "/api/squadrons",
    "/api/squadron",
    "/api/list/",
    "/api/pilot",
    "/api/cards",
    "/api/meta-snapshot",
    "/api/tournaments",
)

EXEMPT_PREFIXES = ("/api/support/webhook",)

# Paths that never need guarding: they are cheap and used by monitoring.
ALWAYS_ALLOW = ("/", "/docs", "/redoc", "/openapi.json", "/favicon.ico")


def classify_user_agent(user_agent: str) -> str:
    """Return ``"bot"``, ``"scripted"`` or ``"browser"``."""
    ua = (user_agent or "").strip()
    if not ua:
        return "scripted"
    if BOT_PATTERN.search(ua):
        return "bot"
    if SCRIPTED_PATTERN.search(ua):
        return "scripted"
    return "browser"


def client_ip(scope: Scope, headers: Headers) -> str:
    """Real client IP: the last X-Forwarded-For hop added by our own proxy."""
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]
        if hops:
            return hops[-1]
    client = scope.get("client")
    if client:
        return client[0]
    return ""


_INTERNAL_NETWORKS = tuple(
    ipaddress.ip_network(net)
    for net in (
        "127.0.0.0/8",      # loopback
        "10.0.0.0/8",       # docker / RFC1918
        "172.16.0.0/12",    # RFC1918
        "192.168.0.0/16",   # RFC1918
        "169.254.0.0/16",   # link-local
        "::1/128",          # IPv6 loopback
        "fc00::/7",         # IPv6 ULA
        "fe80::/10",        # IPv6 link-local
    )
)


def is_internal(ip: str) -> bool:
    """Loopback/private peers are our own tooling, never rate-limited.

    Only real internal ranges count: Python's ``is_private`` also flags the
    documentation ranges (203.0.113.0/24 and friends), and those are valid
    public addresses to be limited like any other.
    """
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _INTERNAL_NETWORKS)


class BotGuardMiddleware:
    """Reject crawlers and rate-limit scripted clients on ``/api/*``."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool | None = None,
        rate_default: int | None = None,
        rate_heavy: int | None = None,
        rate_scripted: int | None = None,
        window_seconds: float | None = None,
    ) -> None:
        self.app = app
        self.enabled = _flag("BOT_GUARD_ENABLED", True) if enabled is None else enabled
        self.rate_default = rate_default or _int_env("BOT_GUARD_RATE_DEFAULT", 120)
        self.rate_heavy = rate_heavy or _int_env("BOT_GUARD_RATE_HEAVY", 40)
        self.rate_scripted = rate_scripted or _int_env("BOT_GUARD_RATE_SCRIPTED", 20)
        self.window_seconds = window_seconds or _float_env("BOT_GUARD_WINDOW_SECONDS", 60.0)

        self._buckets: dict[tuple[str, str], deque[float]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._last_cleanup = time.monotonic()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or "/"
        method = scope.get("method", "GET")

        if (
            method == "OPTIONS"
            or path in ALWAYS_ALLOW
            or not path.startswith("/api/")
            or path.startswith(EXEMPT_PREFIXES)
        ):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        ip = client_ip(scope, headers)
        if is_internal(ip):
            await self.app(scope, receive, send)
            return

        user_agent = headers.get("user-agent", "")
        kind = classify_user_agent(user_agent)

        if kind == "bot":
            _log("bot", ip, path, user_agent, 403)
            await _respond(send, 403, {"detail": "Automated crawling of the API is not allowed."})
            return

        bucket = "heavy" if path.startswith(HEAVY_PREFIXES) else "default"
        if kind == "scripted":
            limit = self.rate_scripted
        else:
            limit = self.rate_heavy if bucket == "heavy" else self.rate_default

        if not self._allow(f"{ip}|{bucket}", limit):
            _log(f"rate-limit {kind}", ip, path, user_agent, 429)
            await _respond(
                send,
                429,
                {"detail": "Too many requests. Please slow down."},
                extra_headers=[(b"retry-after", str(int(self.window_seconds)).encode())],
            )
            return

        await self.app(scope, receive, send)

    def _allow(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = deque()
                self._buckets[key] = bucket
            while bucket and now - bucket[0] >= self.window_seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            self._hits += 1
            if self._hits % 2048 == 0:
                self._cleanup(now)
            return True

    def _cleanup(self, now: float) -> None:
        stale = [
            key for key, bucket in self._buckets.items()
            if not bucket or now - bucket[-1] >= self.window_seconds
        ]
        for key in stale:
            self._buckets.pop(key, None)
        self._last_cleanup = now


async def _respond(
    send: Send,
    status: int,
    payload: dict,
    extra_headers: list[tuple[bytes, bytes]] | None = None,
) -> None:
    body = json.dumps(payload).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
        (b"cache-control", b"no-store"),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


def _log(reason: str, ip: str, path: str, user_agent: str, status: int) -> None:
    ua = (user_agent or "<empty>")[:80]
    print(f"[bot_guard] {reason} status={status} ip={ip} path={path} ua={ua!r}")


def _flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default
