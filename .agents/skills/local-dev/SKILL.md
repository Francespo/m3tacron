---
name: local-dev
description: Spin up the full m3tacron stack locally (Postgres + FastAPI backend + SvelteKit frontend) seeded with a fresh dump of the live dev database. Use when the user wants to test frontend or backend changes against real data before deploying to the real server. Triggers - "run locally", "local dev", "test locally", "host locally", "local stack", "seed local db", "preview m3tacron", "test against real data".
---

# m3tacron — local dev stack

One-command local hosting against a fresh copy of the live dev DB. Use this whenever you need to:

- preview a frontend change against real tournament data
- profile / debug a backend endpoint with real rows
- reproduce a bug that only happens on the dev server
- sanity-check a scraper / migration locally before deploying

## Prereqs

- Docker + Docker Compose v2 (`docker compose` CLI)
- `ssh` + `scp` on PATH
- Access to the dev DB container via the `audit-bot` SSH key (already wired into the m3tacron skill)
- ~5 GB free disk for the Postgres volume + the dump cache

The first `up` will:
1. SSH to the server and `pg_dump` the live dev DB
2. `scp` the dump to `local-data/dumps/dev_latest.dump`
3. Bring up Postgres, restore the dump, then start backend + frontend

Subsequent `up` calls reuse the cached dump (skip step 1-2) so they take ~30 s.

## One-command bring-up

```bash
bash scripts/local_dev/up.sh
```

That's it. Output will look like:

```
============================================================
  m3tacron local stack is running
  Frontend: http://localhost:3335
  Backend:  http://localhost:8890  (docs at /docs)
  Postgres: localhost:5435  (user: m3tacron / pass: m3tacron / db: m3tacron)
  Dump age: 2026-06-18 21:30:01
============================================================
```

## Helper commands

| Command | What it does |
|---|---|
| `bash scripts/local_dev/up.sh` | Bring up the stack; auto-pulls fresh dev dump if no cached one |
| `bash scripts/local_dev/seed.sh` | Force a fresh dev dump from the server (use when dev data has changed) |
| `bash scripts/local_dev/status.sh` | Container status, health probes, DB row counts, dump age |
| `bash scripts/local_dev/logs.sh [service]` | Tail logs (omit service for all) |
| `bash scripts/local_dev/db.sh` | Open psql against the local DB |
| `bash scripts/local_dev/down.sh` | Stop the stack; **keeps** the Postgres volume + cached dump |
| `bash scripts/local_dev/reset.sh` | Stop + delete the Postgres volume + delete the cached dump |

## Common workflows

### I just changed a backend endpoint

```bash
bash scripts/local_dev/up.sh   # only needed the first time
# edit backend/... — uvicorn --reload picks up changes instantly
curl -s http://localhost:8890/api/tournaments | jq '.total'
```

### I want fresh dev data

```bash
bash scripts/local_dev/seed.sh     # pull latest
docker compose -f docker-compose.local.yml restart db-seed
# or just `reset && up` for a clean restart
```

### I want a clean DB

```bash
bash scripts/local_dev/reset.sh   # wipes volume + dump cache
bash scripts/local_dev/up.sh      # rebuilds with fresh dump
```

## What runs where

| Service | Container name | Port (host) | What it does |
|---|---|---|---|
| `postgres` | `m3tacron-postgres-1` | 5435 | Local Postgres 17 (volume: `pgdata`) |
| `db-seed` | `m3tacron-db-seed-1` | — | One-shot: `pg_restore` from bind-mounted dump |
| `backend` | `m3tacron-backend-1` | 8890 | FastAPI + uvicorn `--reload`, watches `backend/` |
| `frontend` | `m3tacron-frontend-1` | 3335 | SvelteKit SPA (adapter-static + `npx serve`) |

DB connection inside the backend container uses `DATABASE_URL=postgresql://m3tacron:m3tacron@postgres:5432/m3tacron` set directly in `docker-compose.local.yml`.

## Frontend notes

The frontend uses `frontend/Dockerfile.local` which builds a **static SPA** via `adapter-static`. This avoids the SvelteKit Node adapter's OOM issue on this machine. The tradeoff: pages render client-side only (no SSR). For local testing this is fine — the data all comes from the same API.

To switch to the production Dockerfile (adapter-node + SSR), edit `docker-compose.local.yml` and change `frontend/Dockerfile.local` → `frontend/Dockerfile`. This requires ~4GB heap and may OOM.

## Pulling a fresh dump manually (without bringing up the stack)

```bash
bash scripts/local_dev/seed.sh
# or against a non-default server:
LOCAL_DEV_SSH_HOST=10.0.0.5 \
LOCAL_DEV_DB_CONTAINER=other-dev-db \
  bash scripts/local_dev/seed.sh
```

All connection params can be overridden with `LOCAL_DEV_SSH_KEY`, `LOCAL_DEV_SSH_USER`, `LOCAL_DEV_SSH_HOST`, `LOCAL_DEV_DB_CONTAINER` env vars (see `scripts/local_dev/seed.sh` for the full list).

## Troubleshooting

**`up.sh` hangs on "Waiting for backend healthcheck"**

The backend might be slow on first start (downloading + building wheels for Python deps). Tail the logs:

```bash
bash scripts/local_dev/logs.sh backend
```

**`db-seed` complains about no dump file**

You ran `up.sh` without an existing cache and the SSH pull failed. Run `bash scripts/local_dev/seed.sh` to see the actual SSH error, fix it, then re-run `up.sh`.

**Frontend shows 502 / "Network error"**

Backend isn't healthy yet. Wait ~30 s for the first build, or check with `bash scripts/local_dev/status.sh`.

**Port 5435 / 8890 / 3335 already in use**

Edit `docker-compose.local.yml` and change the host-side port mappings (the ones before the `:`). The container-internal ports (5432 / 8888 / 3333) must NOT change — the env vars in the backend + frontend depend on them.

**I want to test against the prod DB instead of dev**

Override the container name when seeding:

```bash
LOCAL_DEV_DB_CONTAINER=rdvq2p6xwxho16pbcyd40w0d \
  bash scripts/local_dev/seed.sh
```

**Note**: prod is 1.4 MB (596 tournaments), dev is 12.8 MB (6,002 tournaments). For real data use dev.

## Where the data lives

- Cached dump: `local-data/dumps/dev_latest.dump` (gitignored)
- Postgres volume: Docker named volume `pgdata` (persists across `down`/`up`)
- Backend code: bind-mounted live (no rebuild on edit)

To nuke both and start clean: `bash scripts/local_dev/reset.sh`
