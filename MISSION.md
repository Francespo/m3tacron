# Mission: Dockerize m3tacron for Coolify

## Goal
Containerize the project to allow self-hosted deployment on Coolify with automatic GitHub CI/CD.

## Context
- **Backend**: Python (FastAPI + SQLModel). Uses Playwright (needs system dependencies).
- **Frontend**: SvelteKit. Needs to switch from `adapter-auto` to `adapter-node`.
- **Database**: SQLite (local `test.db` / `seed.db`). Needs persistence via Docker Volumes.
- **Coolify**: Plans to use automatic rebuilds on push to `main`.

## Required Tasks (Issue #87)
1.  **Frontend**: 
    - Install `@sveltejs/adapter-node`.
    - Update `svelte.config.js` to use `adapter-node`.
    - Create `frontend/Dockerfile` (multi-stage build).
2.  **Backend**:
    - Create `backend/Dockerfile` ensuring Playwright system deps are installed (e.g. `playwright install-deps`).
3.  **Orchestration**:
    - Create `docker-compose.yml` in the root.
    - Setup volume for SQLite persistence.
4.  **Verification**:
    - `docker compose build`
    - `docker compose up -d`
    - Verify connectivity.

Refer to the implementation plan in the parent brain directory for details.
