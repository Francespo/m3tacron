#!/usr/bin/env bash
# Bring the local m3tacron stack up.
#   - Postgres (port 5435)
#   - Backend API  (port 8890)
#   - Frontend     (port 3335)
# Auto-seeds the local DB from the most recent dev dump on the server
# (skipped if local-data/dumps/dev_latest.dump is already present).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DUMPS_DIR="$REPO_ROOT/local-data/dumps"
DUMP_FILE="$DUMPS_DIR/dev_latest.dump"

cd "$REPO_ROOT"

if [[ ! -f "$DUMP_FILE" ]]; then
  echo "==> No local dump found. Pulling fresh dev dump from server..."
  bash "$SCRIPT_DIR/seed.sh" --from-server
fi

echo "==> Bringing up local stack (postgres, backend, frontend)..."
docker compose -f docker-compose.local.yml up -d --build

echo "==> Waiting for backend healthcheck..."
for i in {1..30}; do
  if curl -fsS http://localhost:8890/ -o /dev/null; then
    echo "==> Backend is up."
    break
  fi
  sleep 2
  if [[ $i -eq 30 ]]; then
    echo "!! Backend failed to come up in 60s. Tail logs with: bash scripts/local_dev/logs.sh backend"
    exit 1
  fi
done

cat <<EOF

============================================================
  m3tacron local stack is running
  Frontend: http://localhost:3335
  Backend:  http://localhost:8890  (docs at /docs)
  Postgres: localhost:5435  (user: m3tacron / pass: m3tacron / db: m3tacron)
  Dump age: $(stat -c %y "$DUMP_FILE" 2>/dev/null | cut -d. -f1)
============================================================
EOF
