#!/usr/bin/env bash
# Hard reset: stop, delete the Postgres volume, delete the local dump.
# Next `up.sh` will pull a fresh dump and re-seed.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "==> Stopping stack and removing Postgres volume..."
docker compose -f docker-compose.local.yml down -v

DUMP_FILE="$REPO_ROOT/local-data/dumps/dev_latest.dump"
if [[ -f "$DUMP_FILE" ]]; then
  echo "==> Removing cached dump at $DUMP_FILE"
  rm -f "$DUMP_FILE"
fi

echo "==> Done. Next 'up.sh' will pull a fresh dump."
