#!/usr/bin/env bash
# Stop the local stack (keeps Postgres volume + dump file for fast restart).

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"
docker compose -f docker-compose.local.yml down
echo "==> Local stack stopped. Postgres volume + dump preserved."
