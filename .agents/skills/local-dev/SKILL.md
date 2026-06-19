---
name: local-dev
description: Spin up the full m3tacron stack locally (Postgres + FastAPI backend + SvelteKit frontend) seeded with a fresh dump of the live dev database. Use when the user wants to test frontend or backend changes against real data before deploying to the real server. Triggers - "run locally", "local dev", "test locally", "host locally", "local stack", "seed local db", "preview m3tacron", "test against real data".
---

# m3tacron — local dev stack

One-command local hosting against a fresh copy of the live dev DB.

## Prereqs

- Docker + Docker Compose v2 (`docker compose` CLI)
- Node.js 20+ on the host (for native Vite dev server)
- `ssh` + `scp` on PATH
- Access to the dev DB container via the `audit-bot` SSH key
- ~5 GB free disk for the Postgres volume + the dump cache

## Quick start

```bash
bash scripts/local_dev/up.sh
```

Output:
```
============================================================
  m3tacron local stack is running
  Frontend: http://localhost:3335  (hot-reload via Vite)
  Backend:  http://localhost:8890  (docs at /docs)
  Postgres: localhost:5435         (m3tacron / m3tacron)
  Dump age: 2026-06-18 21:30:01
============================================================
  To stop: bash scripts/local_dev/up.sh --stop
  Logs:    bash scripts/local_dev/logs.sh [backend|postgres]
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Host (your machine)                            │
│                                                 │
│   Vite dev server ──── http://localhost:3335     │
│   (npx vite dev)    │    (hot-reload)           │
│                     │                           │
│                     ▼                           │
│   ┌───────────────────────────────────────┐     │
│   │  Docker (backend + DB stack)          │     │
│   │                                       │     │
│   │   Backend  ──── http://localhost:8890  │     │
│   │   (uvicorn --reload)                  │     │
│   │      │                                │     │
│   │      ▼                                │     │
│   │   Postgres ──── localhost:5435        │     │
│   │   (volume: pgdata)                    │     │
│   └───────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
```

- **Frontend**: runs natively on the host via `npx vite dev` with `VITE_API_BASE=http://localhost:8890/api`. Editing `frontend/src/` triggers instant Vite HMR.
- **Backend**: runs in Docker with `uvicorn --reload` watching `backend/`. Editing backend files triggers instant reload.
- **Database**: runs in Docker on port 5435 with a named volume (`pgdata`). Seeded from the dev server's dump on first `up`.

## Helper commands

| Command | What it does |
|---|---|
| `bash scripts/local_dev/up.sh` | Bring up backend+DB in Docker, frontend on host with hot-reload |
| `bash scripts/local_dev/up.sh --stop` | Stop everything (Docker + Vite) |
| `bash scripts/local_dev/seed.sh` | Force a fresh dev dump from the server |
| `bash scripts/local_dev/status.sh` | Container status, health probes, DB row counts, dump age |
| `bash scripts/local_dev/logs.sh [service]` | Tail logs (omit service for all) |
| `bash scripts/local_dev/db.sh` | Open psql against the local DB |
| `bash scripts/local_dev/down.sh` | Stop the stack; keeps the Postgres volume + cached dump |
| `bash scripts/local_dev/reset.sh` | Stop + delete the Postgres volume + delete the cached dump |

## Common workflows

### I just changed a frontend component
```bash
bash scripts/local_dev/up.sh   # only needed the first time
# edit frontend/src/ — Vite HMR shows the change instantly
```

### I want fresh dev data
```bash
bash scripts/local_dev/seed.sh
docker compose -f docker-compose.local.yml restart db-seed
```

### I want a clean DB
```bash
bash scripts/local_dev/reset.sh
bash scripts/local_dev/up.sh
```

### I want to test backend only (no frontend)
```bash
docker compose -f docker-compose.local.yml up -d postgres db-seed backend
curl -s http://localhost:8890/api/tournaments | jq '.total'
```

## Troubleshooting

**Port 3335 already in use**
The Vite server will automatically try 3336, 3337, etc. Check:
```bash
grep -oP 'Local:\s+http://localhost:\K[0-9]+' /tmp/m3tacron-vite.log
```

**Frontend shows "ECONNREFUSED" on API calls**
Backend is not healthy yet. Wait ~30s or check `bash scripts/local_dev/status.sh`.

**`up.sh` hangs on "Waiting for backend healthcheck"**
Tail logs: `bash scripts/local_dev/logs.sh backend`

**Test against prod DB instead of dev**
```bash
LOCAL_DEV_DB_CONTAINER=rdvq2p6xwxho16pbcyd40w0d bash scripts/local_dev/seed.sh
```

## Data locations

- Cached dump: `local-data/dumps/dev_latest.dump` (gitignored)
- Postgres volume: Docker named volume `pgdata`
- Backend code: bind-mounted (no rebuild on edit)
- Frontend code: runs natively (Vite watches for changes)

To nuke everything: `bash scripts/local_dev/reset.sh`
