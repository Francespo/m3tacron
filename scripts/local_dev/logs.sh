#!/usr/bin/env bash
# Tail logs. Pass a service name (postgres, backend, frontend, db-seed) or no arg for all.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"
docker compose -f docker-compose.local.yml logs -f --tail=200 "${1:-}"
