---
name: m3tacron
description: SSH access, database connection info, and Coolify deployment info for the m3tacron project (m3tacron.com, dev.m3tacron.com). Load whenever you need to connect to the server, inspect the database, or trigger/manage Coolify preview deployments via the coolify CLI.
---

## SSH Access

**Server:** `84.8.253.2` (port 22)
**User:** `audit-bot`
**Key:** `ssh_key` (this skill's directory)
**Fingerprint:** `SHA256:XLU/H7Xjyw2nw30+dwccshyXiHk0DYLowcwPdwzGtJ4`

### Connection command
```bash
ssh -i /home/ubuntu/projects/m3tacron/.agents/skills/m3tacron/ssh_key -o StrictHostKeyChecking=no audit-bot@84.8.253.2
```

### Docker access
The `audit-bot` user has docker group access. Use `docker ps` to list containers.

## Coolify Containers

### Dev deployment
- Frontend: `itn8u6i9fftynwj42kz92fao_frontend:pr-111`
- Backend: `itn8u6i9fftynwj42kz92fao_backend:pr-111`
- DB container: `h356grmw78dsf5qwsqb8l0xd` (postgres:18-alpine, host port 3001)
- DB URL: `postgres://postgres:D1h4oro6SR2U3NHPixSQGf8omscEOgP4A3xNZiR4zySNPLKidKUJOaVsksewE17f@h356grmw78dsf5qwsqb8l0xd:5432/postgres`

### Running database queries
```bash
docker exec <db-container> psql -U postgres -c "SELECT COUNT(*) FROM tournament;"
```

## Coolify CLI (preview deployments)

The `coolify` CLI is installed locally and configured with context `m3tacron`
(`https://coolify.m3tacron.com`, deploy-scoped API token in `~/.config/coolify/config.json`).

### Trigger a PR preview redeploy
```bash
coolify deploy uuid d1237bghfe3rxgm7ahj00z8l --pull-request-id <PR_NUMBER> --force
```
Application UUID `d1237bghfe3rxgm7ahj00z8l` = `francespo/m3tacron:main` (preview deployments are per-PR).

### Prerequisites / gotchas (already configured)
- Coolify API must be enabled: `instance_settings.is_api_enabled = true` (was disabled → CLI returned 403 "API is disabled").
- Token is a Laravel Sanctum personal access token created via tinker with abilities `["deploy","read","write"]`.
  Coolify's custom `createToken` requires `session(['currentTeam' => $team])` to be set first (team_id is NOT NULL).

### Preview proxy architecture (for debugging why a preview shows stale data)
- Each PR preview has its own backend container, reachable as `backend-pr-<N>` on the shared coolify network.
  The generic `backend` hostname belongs to the OLD shared backend — never use it for previews.
- Frontend proxy: `frontend/src/routes/api/[...path]/+server.js` resolves the backend via
  `previewBackendHost()` reading `COOLIFY_BRANCH`.
- Gotcha: Coolify sets `COOLIFY_BRANCH` **with literal quotes** (e.g. `"pull/131/head"`) — strip quotes
  before matching `/^pull\/(\d+)/`. Also the value has a `/head` suffix.
- Verify data freshness: `GET /api/pilot/ricolie` returns `cost` (old=4 on 20-pt scale, new=11 on 50-pt scale).
- Preview domains: `131.dev.m3tacron.com` (frontend) / `131.dev.api.m3tacron.com` (backend, internal only).
