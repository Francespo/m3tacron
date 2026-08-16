---
name: m3tacron
description: SSH access and database connection info for the m3tacron project servers (m3tacron.com, dev.m3tacron.com). Load whenever you need to connect to the server or inspect the database.
---

## SSH Access

**Server:** `84.8.253.2` (port 22)
**User:** `audit-bot`
**Key:** `~/.ssh/m3tacron_audit_bot` (must exist on the machine — not in the repo)

### Prerequisites

The SSH key must be present on the machine at `~/.ssh/m3tacron_audit_bot`. This is a machine-level prerequisite — the key is never stored in the repository.

To set up on a new machine:
```bash
# Generate a keypair (if you don't have one for this server)
ssh-keygen -t ed25519 -f ~/.ssh/m3tacron_audit_bot -C "m3tacron-audit-bot"

# Copy the public key to the server
ssh-copy-id -i ~/.ssh/m3tacron_audit_bot.pub audit-bot@84.8.253.2
```

To override the key path, set `LOCAL_DEV_SSH_KEY`:
```bash
LOCAL_DEV_SSH_KEY=/path/to/your/key bash scripts/local_dev/seed.sh
```

### Connection command
```bash
ssh -i ~/.ssh/m3tacron_audit_bot -o StrictHostKeyChecking=no audit-bot@84.8.253.2
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
