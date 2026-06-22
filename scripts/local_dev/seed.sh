#!/usr/bin/env bash
# Pull a fresh dump of the dev DB from the production server
# and stage it at local-data/dumps/dev_latest.dump.
#
# Usage:
#   bash scripts/local_dev/seed.sh             # SSH to server, pull latest
#   bash scripts/local_dev/seed.sh --from-server
#
# Environment overrides (all optional):
#   LOCAL_DEV_SSH_KEY      path to ssh key   (default: <project>/.agents/skills/m3tacron/ssh_key)
#   LOCAL_DEV_SSH_USER     ssh user          (default: audit-bot)
#   LOCAL_DEV_SSH_HOST     ssh host          (default: 84.8.253.2)
#   LOCAL_DEV_DB_CONTAINER dev DB container  (default: h356grmw78dsf5qwsqb8l0xd)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DUMPS_DIR="$REPO_ROOT/local-data/dumps"
mkdir -p "$DUMPS_DIR"

SSH_KEY="${LOCAL_DEV_SSH_KEY:-$REPO_ROOT/.agents/skills/m3tacron/ssh_key}"
SSH_USER="${LOCAL_DEV_SSH_USER:-audit-bot}"
SSH_HOST="${LOCAL_DEV_SSH_HOST:-84.8.253.2}"
DB_CONTAINER="${LOCAL_DEV_DB_CONTAINER:-h356grmw78dsf5qwsqb8l0xd}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
REMOTE_DUMP="/tmp/local_seed_${TS}.dump"

REMOTE_HOST_DUMP="/tmp/local_seed_${TS}.dump"

echo "==> Dumping dev DB ($DB_CONTAINER) on $SSH_USER@$SSH_HOST ..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" \
  "docker exec $DB_CONTAINER pg_dump -U postgres -Fc -f $REMOTE_HOST_DUMP postgres && docker cp $DB_CONTAINER:$REMOTE_HOST_DUMP $REMOTE_HOST_DUMP"

echo "==> Copying dump to local-data/dumps/ ..."
mkdir -p "$DUMPS_DIR"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
  "$SSH_USER@$SSH_HOST:$REMOTE_HOST_DUMP" "$DUMPS_DIR/dev_latest.dump"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" \
  "rm -f $REMOTE_HOST_DUMP" || true

DUMP_SIZE=$(du -h "$DUMPS_DIR/dev_latest.dump" | cut -f1)
echo "==> Seed ready: $DUMPS_DIR/dev_latest.dump ($DUMP_SIZE)"
