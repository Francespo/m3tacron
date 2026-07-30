#!/usr/bin/env bash
# m3tacron local dev — single entry point.
# Auto-runs setup if first time, then starts the stack.
#
# Usage:
#   bash scripts/local_dev/launch.sh              # setup + launch (full stack, Vite foreground)
#   bash scripts/local_dev/launch.sh --setup-only # setup only, don't start servers
#   bash scripts/local_dev/launch.sh --port 4335  # custom frontend port
#
# Ports are configurable via env or flags:
#   BACKEND_PORT, POSTGRES_PORT, VITE_PORT (or --backend-port, --postgres-port, --port)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# --- Parse args ---
BACKEND_PORT="${BACKEND_PORT:-8890}"
POSTGRES_PORT="${POSTGRES_PORT:-5435}"
VITE_PORT="${VITE_PORT:-3335}"
SETUP_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) VITE_PORT="$2"; shift 2 ;;
    --backend-port) BACKEND_PORT="$2"; shift 2 ;;
    --postgres-port) POSTGRES_PORT="$2"; shift 2 ;;
    --setup-only) SETUP_ONLY=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

export BACKEND_PORT POSTGRES_PORT VITE_PORT

# --- Setup if needed ---
bash "$SCRIPT_DIR/ensure-setup.sh"

if $SETUP_ONLY; then
  echo "==> Setup-only mode. Exiting."
  exit 0
fi

# --- Bring up Docker stack ---
echo "==> Starting Postgres (:$POSTGRES_PORT) + Backend (:$BACKEND_PORT)..."
docker compose -f docker-compose.local.yml up -d --build postgres db-seed backend

# --- Wait for backend ---
echo "==> Waiting for backend..."
for i in $(seq 1 30); do
  if curl -fsS "http://localhost:${BACKEND_PORT}/" -o /dev/null 2>/dev/null; then
    echo "==> Backend is up."
    break
  fi
  sleep 2
  if [ "$i" -eq 30 ]; then
    echo "!! Backend didn't start in 60s. Check: bash scripts/local_dev/logs.sh backend"
    exit 1
  fi
done

# --- Start Vite in foreground ---
echo ""
echo "============================================================"
echo "  m3tacron dev stack"
echo "  Postgres: localhost:${POSTGRES_PORT}  (m3tacron / m3tacron)"
echo "  Backend:  http://localhost:${BACKEND_PORT}  (docs at /docs)"
echo "  Frontend: starting on port ${VITE_PORT}..."
echo "============================================================"
echo ""

cd "$REPO_ROOT/frontend"
VITE_BIN="$REPO_ROOT/frontend/node_modules/.bin/vite"
if [ ! -x "$VITE_BIN" ]; then
  npm install --no-audit --no-fund
fi

exec env \
  NODE_OPTIONS="--max-old-space-size=4096" \
  VITE_API_BASE="http://localhost:${BACKEND_PORT}/api" \
  VITE_ALLOWED_HOSTS=localhost,127.0.0.1 \
  ORIGIN="http://localhost:${VITE_PORT}" \
  "$VITE_BIN" dev --host 0.0.0.0 --port "$VITE_PORT"
