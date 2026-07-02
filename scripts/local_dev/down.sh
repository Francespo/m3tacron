#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VITE_PID_FILE="/tmp/m3tacron-vite.pid"

if [[ -f "$VITE_PID_FILE" ]]; then
  pid=$(cat "$VITE_PID_FILE" 2>/dev/null || true)
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "==> Stopping frontend (Vite)..."
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
  rm -f "$VITE_PID_FILE"
fi

cd "$REPO_ROOT"
docker compose -f docker-compose.local.yml down
echo "==> Local stack stopped. Postgres volume + dump preserved."
