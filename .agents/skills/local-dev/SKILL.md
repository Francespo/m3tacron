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

## Container Resource Limits (Memory Safety)

The VPS has **10 GB RAM and 2 cores**. Without limits, a single heavy query can OOM-kill the host and force a reboot. The `docker-compose.local.yml` enforces strict memory ceilings:

| Container | Memory Limit | CPU Limit | PID Limit | Why |
|---|---|---|---|---|
| `postgres` | **2 GB** | 1.0 CPU | 128 | Holds shared_buffers (256MB) + work_mem per query. Prevents runaway query memory from starving the host. |
| `backend` | **1 GB** | 1.0 CPU | 128 | uvicorn + Python analytics. Prevents a single API call from loading unbounded JSON into memory. |
| `db-seed` | **512 MB** | 0.5 CPU | 64 | pg_restore can spike during large dump loads. Ephemeral container, exits after seeding. |

**Total reserved: 3.5 GB out of 10 GB.** Leaves 6.5 GB for the host, Vite dev server, and other processes.

### PostgreSQL memory tuning (applied via `postgres -c` command in docker-compose)

| Setting | Value | Rationale |
|---|---|---|
| `shared_buffers` | 256 MB | 2-3% of total RAM. PostgreSQL's shared memory cache. |
| `effective_cache_size` | 2 GB | Tells the planner how much OS cache is expected (shared_buffers + OS page cache). |
| `work_mem` | 4 MB | Per-operation memory for sorts, hashes, merges. Too high = OOM with concurrent queries. |
| `maintenance_work_mem` | 128 MB | For VACUUM, CREATE INDEX, ALTER TABLE. |
| `max_connections` | 20 | Each connection costs ~10 MB. Low concurrency for local dev. |
| `statement_timeout` | 60000 (60s) | Kills any query running longer than 60 seconds. Prevents runaway queries from hanging forever. |

### Crash prevention measures

1. **Container memory limits** — If a container exceeds its limit, Docker kills it (not the host). The host survives.
2. **`statement_timeout=60s`** — PostgreSQL auto-kills queries that run longer than 60 seconds. No query can hang indefinitely.
3. **Low `work_mem=4MB`** — Prevents a single sort/hash operation from consuming hundreds of MB.
4. **PID limits** — Prevents fork bombs or runaway process creation inside containers.
5. **Migration auto-applied on seed** — The db-seed container runs `migrate_performance.sql` after restoring the dump, so the jsonb conversion and indexes are always present.

### If a container gets OOM-killed

```bash
# Check which container died
docker ps -a | grep -v Up
# Check if it was OOM
docker inspect <container> --format '{{.State.OOMKilled}}'
# Restart the stack
bash scripts/local_dev/up.sh
```
