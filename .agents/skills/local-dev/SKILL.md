---
name: local-dev
description: Spin up the full m3tacron stack locally (Postgres + FastAPI backend + SvelteKit frontend) seeded with a fresh dump of the live dev database. Use when the user wants to test frontend or backend changes against real data before deploying to the real server. Triggers - "run locally", "local dev", "test locally", "host locally", "local stack", "seed local db", "preview m3tacron", "test against real data".
---

# m3tacron — local dev stack

One-command local hosting against a fresh copy of the live dev DB.

## Prereqs

- Docker + Docker Compose v2 (`docker compose` CLI)
- Node.js 20+ on the host (for native Vite dev server)
- ~5 GB free disk for the Postgres volume + the dump cache
- **SSH key at `~/.ssh/m3tacron_audit_bot`** (only for `seed.sh` to pull fresh dumps from the dev server — not needed if you already have a cached dump)

## Quick start

```bash
bash scripts/local_dev/launch.sh
```

This auto-detects whether dependencies are installed. First run does full setup (submodules, venv, npm, dump copy), then starts the stack. Subsequent runs skip setup and launch directly.

Output:
```
============================================================
  m3tacron dev stack
  Postgres: localhost:5435  (m3tacron / m3tacron)
  Backend:  http://localhost:8890  (docs at /docs)
  Frontend: starting on port 3335...
============================================================
```

Press Ctrl+C to stop Vite. Docker stack keeps running (stop with `up.sh --stop`).

**Port auto-selection:** If 3335/8890/5435 are taken (multiple worktrees), ports auto-increment to the next free port and the banner shows the actual ports.

### Setup only

```bash
bash scripts/local_dev/launch.sh --setup-only
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

- **Frontend**: runs natively on the host via Vite with `VITE_API_BASE=http://localhost:8890/api`. Editing `frontend/src/` triggers instant HMR.
- **Backend**: runs in Docker with `uvicorn --reload` watching `backend/`. Editing backend files triggers instant reload.
- **Database**: runs in Docker on port 5435 with a named volume (`pgdata`). Seeded from the dev server's dump on first `up`.

## Tailnet access

All services bind to `0.0.0.0` so other users in the tailnet can access them. The tailnet hostname is auto-detected via `tailscale` (falls back to `hostname`).

After launching, the banner shows both local and tailnet URLs:

```
  Local access:
    Frontend: http://localhost:3335
    Backend:  http://localhost:8890/docs

  Tailnet access (other users):
    Frontend: http://server-francesco:3335
    Backend:  http://server-francesco:8890/docs
```

`VITE_ALLOWED_HOSTS` is set automatically to include the tailnet hostname, so CORS works for tailnet users without manual configuration.

## Configurable ports

All ports are configurable via environment variables, so parallel worktrees can coexist:

| Variable | Default | Used by |
|---|---|---|
| `BACKEND_PORT` | `8890` | Backend container host mapping, healthcheck, Vite API base |
| `POSTGRES_PORT` | `5435` | Postgres container host mapping |
| `VITE_PORT` | `3335` | Vite dev server, `up.sh` background process |

Override per invocation:

```bash
BACKEND_PORT=9890 VITE_PORT=4335 bash scripts/local_dev/launch.sh
```

Or pass flags to `launch.sh`:

```bash
bash scripts/local_dev/launch.sh --port 4335 --backend-port 9890
```

## Paseo worktree integration

When Paseo creates a worktree, `paseo.json` triggers `scripts/local_dev/worktree_setup.sh` which:

1. Initializes git submodules (`external_data/`) with retry — falls back to copying from the source checkout if clone fails
2. Creates a Python venv and installs backend + dev dependencies
3. Runs `npm ci` in `frontend/`
4. Copies the cached DB dump from the source checkout (`local-data/dumps/dev_latest.dump`)

After setup, agents start the stack with:

```bash
bash scripts/local_dev/launch.sh
```

Or use the Paseo `launch` service (registered as a foreground service on port 3335).

### Parallel worktrees

Paseo assigns unique ports from the `9000-9100` range per worktree. Docker port mappings use `$BACKEND_PORT` and `$POSTGRES_PORT` env vars, so each worktree's stack binds to different host ports.

## Helper commands

| Command | What it does |
|---|---|
| `bash scripts/local_dev/launch.sh` | One-command start: auto-setup + Docker + Vite (foreground) |
| `bash scripts/local_dev/launch.sh --setup-only` | Run setup only (submodules, venv, npm, dump) |
| `bash scripts/local_dev/launch.sh --port 4335` | Start with custom frontend port |
| `bash scripts/local_dev/up.sh` | Alternative: start full stack with Vite in background |
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
bash scripts/local_dev/launch.sh  # or up.sh
# edit frontend/src/ — Vite HMR shows the change instantly
```

### I just changed a backend endpoint
```bash
# launch.sh/up.sh must already be running
# edit backend/ — uvicorn --reload picks it up
curl -s http://localhost:8890/api/your-endpoint
```

### I want fresh dev data
```bash
bash scripts/local_dev/seed.sh
docker compose -f docker-compose.local.yml restart db-seed
```

### I want a clean DB
```bash
bash scripts/local_dev/reset.sh
bash scripts/local_dev/launch.sh
```

### I want to test backend only (no frontend)
```bash
docker compose -f docker-compose.local.yml up -d postgres db-seed backend
curl -s http://localhost:8890/api/tournaments | jq '.total'
```

## Troubleshooting

**Port already in use**
Override via env: `BACKEND_PORT=9890 bash scripts/local_dev/launch.sh`

**Frontend shows "ECONNREFUSED" on API calls**
Backend is not healthy yet. Wait ~30s or check `bash scripts/local_dev/status.sh`.

**`up.sh` hangs on "Waiting for backend healthcheck"**
Tail logs: `bash scripts/local_dev/logs.sh backend`

**Submodule clone fails in worktree**
`worktree_setup.sh` retries once, then falls back to copying `external_data/` from the source checkout. If that also fails, run manually:
```bash
git submodule update --init --recursive
# or
cp -a "$PASEO_SOURCE_CHECKOUT_PATH/external_data" external_data
```

**Test against prod DB instead of dev**
```bash
LOCAL_DEV_DB_CONTAINER=rdvq2p6xwxho16pbcyd40w0d bash scripts/local_dev/seed.sh
```

## Data locations

- Cached dump: `local-data/dumps/dev_latest.dump` (gitignored)
- Postgres volume: Docker named volume `pgdata`
- Backend code: bind-mounted (no rebuild on edit)
- Frontend code: runs natively (Vite watches for changes)
- SSH key: `~/.ssh/m3tacron_audit_bot` (machine-level, not in repo)

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
| `statement_timeout` | 120000 (120s) | Kills any query running longer than 120 seconds. Prevents runaway queries from hanging forever. |

### Crash prevention measures

1. **Container memory limits** — If a container exceeds its limit, Docker kills it (not the host). The host survives.
2. **`statement_timeout=120s`** — PostgreSQL auto-kills queries that run longer than 120 seconds. No query can hang indefinitely.
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
bash scripts/local_dev/launch.sh
```
