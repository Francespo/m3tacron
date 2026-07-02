#!/usr/bin/env bash
# Open a psql shell against the local Postgres.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"
docker compose -f docker-compose.local.yml exec postgres psql -U m3tacron -d m3tacron
