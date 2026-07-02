#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DUMPS_DIR="$REPO_ROOT/local-data/dumps"
DUMP_FILE="$DUMPS_DIR/dev_latest.dump"
VITE_PID_FILE="/tmp/m3tacron-vite.pid"
VITE_LOG="/tmp/m3tacron-vite.log"
DEFAULT_PORT=3333
VITE_PORT="$DEFAULT_PORT"

cd "$REPO_ROOT"

cleanup_vite() {
  if [[ -f "$VITE_PID_FILE" ]]; then
    local pid
    pid=$(cat "$VITE_PID_FILE" 2>/dev/null || true)
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "==> Stopping frontend (Vite)..."
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
    rm -f "$VITE_PID_FILE"
  fi
}

usage() {
  cat <<USAGE
Usage: bash scripts/local_dev/up.sh [OPTIONS]

Options:
  --port <PORT>   Port for the Vite dev server (default: $DEFAULT_PORT).
                  Must be between 1 and 65535.
  --stop          Stop the local stack (postgres + backend + Vite).
  -h, --help      Show this help.

With no options, starts the full local stack.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      if [[ $# -lt 2 ]]; then
        echo "!! --port requires a value"
        usage
        exit 1
      fi
      if ! [[ "$2" =~ ^[0-9]+$ ]] || [[ "$2" -lt 1 ]] || [[ "$2" -gt 65535 ]]; then
        echo "!! --port must be a number between 1 and 65535 (got: $2)"
        exit 1
      fi
      VITE_PORT="$2"
      shift 2
      ;;
    --port=*)
      local_port="${1#--port=}"
      if ! [[ "$local_port" =~ ^[0-9]+$ ]] || [[ "$local_port" -lt 1 ]] || [[ "$local_port" -gt 65535 ]]; then
        echo "!! --port must be a number between 1 and 65535 (got: $local_port)"
        exit 1
      fi
      VITE_PORT="$local_port"
      shift
      ;;
    --stop)
      cleanup_vite
      docker compose -f docker-compose.local.yml down
      echo "==> Local stack stopped."
      exit 0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "!! Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "$DUMP_FILE" ]]; then
  echo "==> No local dump found. Pulling fresh dev dump from server..."
  bash "$SCRIPT_DIR/seed.sh"
fi

cleanup_vite

echo "==> Bringing up backend stack (postgres + backend in Docker)..."
docker compose -f docker-compose.local.yml up -d --build postgres db-seed backend

echo "==> Waiting for backend healthcheck..."
for i in {1..30}; do
  if curl -fsS http://localhost:8890/ -o /dev/null 2>/dev/null; then
    echo "==> Backend is up."
    break
  fi
  sleep 2
  if [[ $i -eq 30 ]]; then
    echo "!! Backend failed to come up in 60s. Run: bash scripts/local_dev/logs.sh backend"
    exit 1
  fi
done

echo "==> Starting frontend on host (Vite dev server with hot-reload)..."
cd "$REPO_ROOT/frontend"
VITE_BIN="$REPO_ROOT/frontend/node_modules/.bin/vite"
if [[ ! -x "$VITE_BIN" ]]; then
  echo "!! vite not found. Running npm install in frontend/..."
  (cd "$REPO_ROOT/frontend" && npm install --no-audit --no-fund)
fi
nohup env \
  NODE_OPTIONS="--max-old-space-size=4096" \
  VITE_API_BASE=http://localhost:8890/api \
  VITE_ALLOWED_HOSTS=localhost,127.0.0.1 \
  ORIGIN=http://localhost:$VITE_PORT \
  "$VITE_BIN" dev --host 0.0.0.0 --port "$VITE_PORT" \
  > "$VITE_LOG" 2>&1 &
echo $! > "$VITE_PID_FILE"
cd "$REPO_ROOT"

sleep 3

VITE_PORT=$VITE_PORT
if ! curl -fsS -o /dev/null "http://localhost:$VITE_PORT/" 2>/dev/null; then
  VITE_PORT=$(grep -oP 'Local:\s+http://localhost:\K[0-9]+' "$VITE_LOG" 2>/dev/null | tail -1 || echo "$DEFAULT_PORT")
fi

cat <<EOF

============================================================
  m3tacron local stack is running
  Frontend: http://localhost:$VITE_PORT  (hot-reload via Vite)
  Backend:  http://localhost:8890       (docs at /docs)
  Postgres: localhost:5435              (m3tacron / m3tacron)
  Dump age: $(stat -c %y "$DUMP_FILE" 2>/dev/null | cut -d. -f1 || echo "unknown")
============================================================
  To stop: bash scripts/local_dev/up.sh --stop
  Logs:    bash scripts/local_dev/logs.sh [backend|postgres]
EOF
