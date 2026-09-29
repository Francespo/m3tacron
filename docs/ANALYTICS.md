# Traffic analytics

First-party, cookie-less page-view analytics. The goal is to answer "how many
people use the site" (DAU / WAU / MAU, sessions, top pages) without adding a
third-party script and without storing anything that identifies a visitor.

## What is collected

The frontend tracker (`frontend/src/lib/analytics.ts`) posts one event per page
view to `POST /api/analytics/collect` on the API host. The backend stores it in
the `pageview` table (`backend/models.py`, `PageView`):

| Column | Example | Notes |
|---|---|---|
| `ts` | `2026-09-29T21:14:03Z` | server time (UTC) |
| `path` | `/pilot/avenger` | route only; query string and fragment are dropped |
| `visitor_id` | `7f3c...` | random id generated in the browser (`localStorage`) |
| `session_id` | `b91a...` | random id, renewed after 30 minutes of inactivity (`sessionStorage`) |
| `referrer_host` | `reddit.com` | external referrer host only, never the full URL |
| `is_bot` | `false` | flagged from the request's user agent |

Not stored: IP address, user agent string, cookies, full referrer URL, search
or filter values, account data (there are no accounts).

The endpoint only accepts requests whose `Origin`/`Referer` host is in
`ANALYTICS_ALLOWED_HOSTS` (default `m3tacron.com,www.m3tacron.com`), so other
sites or scanners cannot inflate the counters.

## Privacy

* No cookies and no fingerprinting, so no consent banner is required.
* `Do Not Track` and `Global Privacy Control` are honoured: the tracker sends
  nothing when either is enabled.
* Automated requests (crawlers, link previewers, uptime monitors, headless
  browsers) are recorded but flagged `is_bot`, and every report separates them.
  They are useful signal: they show how much of the request volume is not human.

## Reading the numbers

Directly from the database (works wherever the backend can reach it):

```bash
python3 scripts/analytics_report.py --days 30
python3 scripts/analytics_report.py --days 90 --json
```

On the Coolify host, run it inside the backend container:

```bash
docker exec <backend-container> python scripts/analytics_report.py --days 30
```

Over HTTP, when `ANALYTICS_ADMIN_TOKEN` is set on the backend:

```bash
curl -H "X-Analytics-Token: $ANALYTICS_ADMIN_TOKEN" \
  "https://api.m3tacron.com/api/analytics/summary?days=30"
```

Without that environment variable the summary endpoint answers `503` and only
the script/DB path is available. The token is deliberately not stored in the
repository.

## Configuration

Backend environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `ANALYTICS_ALLOWED_HOSTS` | `m3tacron.com,www.m3tacron.com` | hosts allowed to post events |
| `ANALYTICS_ADMIN_TOKEN` | unset | enables `GET /api/analytics/summary` |

Frontend build-time variables (SvelteKit `PUBLIC_*`):

| Variable | Default | Purpose |
|---|---|---|
| `PUBLIC_ANALYTICS_ENABLED` | enabled | set to `false` to disable the tracker |
| `PUBLIC_ANALYTICS_HOSTS` | `m3tacron.com,www.m3tacron.com` | allowlist for the browser host |

To test from a preview deployment, add its host on both sides, for example
`ANALYTICS_ALLOWED_HOSTS=m3tacron.com,www.m3tacron.com,123.dev.m3tacron.com` and
`PUBLIC_ANALYTICS_HOSTS=m3tacron.com,www.m3tacron.com,123.dev.m3tacron.com`.
Preview events land in the same production table, so remove the host again when
the test is done.

## Crawlers

`frontend/static/robots.txt` allows the pages and disallows `/api/`, and the
backend serves `User-agent: * / Disallow: /` on `/robots.txt` so crawlers stay
out of the API host entirely. Robots rules are advisory; the `is_bot` flag and
the counts in the report are the authoritative view of automated traffic.

## Why not a hosted dashboard (Umami / Plausible)

A self-hosted dashboard needs its own hostname (for example
`analytics.m3tacron.com`), which requires a DNS record that this repository
cannot create. The first-party endpoint reuses the existing API host and
deployment pipeline, so it works today and needs no extra container. If a
subdomain is added later, Coolify's one-click Umami service can run in parallel
and the frontend tracker can be pointed at it.
