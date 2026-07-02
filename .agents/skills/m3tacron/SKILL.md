---
name: m3tacron
description: SSH access and database connection info for the m3tacron project servers (m3tacron.com, dev.m3tacron.com). Load whenever you need to connect to the server or inspect the database.
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
