#!/usr/bin/env bash
# m3tacron local dev stack — background mode.
# Starts Docker stack + Vite in background. Binds to 0.0.0.0 for tailnet access.
set -euo pipefail

find_free_port() {
  local p="$1"
  while ss -tlnH "sport = :$p" 2>/dev/null | grep -q ":$p" || docker ps --format '{{.Ports}}' 2>/dev/null | grep -q "0.0.0.0:$p->"; do p=$((p+1)); done
  echo "$p"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DUMPS_DIR="$REPO_ROOT/local-data/dumps"
DUMP_FILE="$DUMPS_DIR/dev_latest.dump"
VITE_PID_FILE="/tmp/m3tacron-fix-filter-ux-restructure.pid"
VITE_LOG="/tmp/m3tacron-fix-filter-ux-restructure.log"
DEFAULT_PORT="${VITE_PORT:-3335}"
VITE_PORT="$DEFAULT_PORT"

# --- Detect tailnet hostname + MagicDNS ---
HOSTNAME_SHORT="$(hostname -s 2>/dev/null || echo localhost)"
TAILSCALE_HOST=""
TAILSCALE_FQDN=""
if command -v tailscale &>/dev/null; then
  TAILSCALE_HOST="$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('Self',{}).get('HostName',''))" 2>/dev/null || true)"
  TAILSCALE_FQDN="$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; j=json.load(sys.stdin); print(j.get('Self',{}).get('DNSName','').rstrip('.'))" 2>/dev/null || true)"
fi
TAILNET_HOST="${TAILSCALE_HOST:-$HOSTNAME_SHORT}"
TAILNET_FQDN="${TAILSCALE_FQDN:-$TAILNET_HOST}"
TAIL_IP4="$(tailscale ip -4 2>/dev/null | tr '\n' ',' | sed 's/,$//')"
TAIL_IP6="$(tailscale ip -6 2>/dev/null | head -1 | tr -d '\n')"

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

BACKEND_PORT="${BACKEND_PORT:-8890}"
POSTGRES_PORT="${POSTGRES_PORT:-5435}"
ORIG_BACKEND_PORT="$BACKEND_PORT"
ORIG_POSTGRES_PORT="$POSTGRES_PORT"
ORIG_VITE_PORT="$VITE_PORT"
BACKEND_PORT="$(find_free_port "$BACKEND_PORT")"
POSTGRES_PORT="$(find_free_port "$POSTGRES_PORT")"
VITE_PORT="$(find_free_port "$VITE_PORT")"
export BACKEND_PORT POSTGRES_PORT VITE_PORT
if [ "$BACKEND_PORT" != "$ORIG_BACKEND_PORT" ] || [ "$POSTGRES_PORT" != "$ORIG_POSTGRES_PORT" ] || [ "$VITE_PORT" != "$ORIG_VITE_PORT" ]; then
  echo "==> Ports auto-adjusted (occupied ports skipped):"
  [ "$BACKEND_PORT"  != "$ORIG_BACKEND_PORT"  ] && echo "    Backend:  $ORIG_BACKEND_PORT -> $BACKEND_PORT"
  [ "$POSTGRES_PORT" != "$ORIG_POSTGRES_PORT" ] && echo "    Postgres: $ORIG_POSTGRES_PORT -> $POSTGRES_PORT"
  [ "$VITE_PORT"     != "$ORIG_VITE_PORT"     ] && echo "    Frontend: $ORIG_VITE_PORT -> $VITE_PORT"
fi

echo "==> Bringing up backend stack (postgres + backend in Docker)..."
BACKEND_PORT="${BACKEND_PORT:-8890}"
docker compose -f docker-compose.local.yml up -d --build postgres db-seed backend

echo "==> Waiting for backend healthcheck..."
for i in {1..30}; do
  if curl -fsS "http://localhost:${BACKEND_PORT}/" -o /dev/null 2>/dev/null; then
    echo "==> Backend is up."
    break
  fi
  sleep 2
  if [[ $i -eq 30 ]]; then
    echo "!! Backend failed to come up in 60s on port ${BACKEND_PORT}. Run: bash scripts/local_dev/logs.sh backend"
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
VITE_ALLOWED="localhost,127.0.0.1,${TAILNET_HOST},${TAILNET_FQDN},${TAIL_IP4:-},${TAIL_IP6:-}"
VITE_ALLOWED="$(echo "$VITE_ALLOWED" | sed 's/,,*/,/g; s/^,//; s/,$//')"
nohup env \
  NODE_OPTIONS="--max-old-space-size=4096" \
  VITE_API_BASE="http://localhost:${BACKEND_PORT}/api" \
  VITE_ALLOWED_HOSTS="$VITE_ALLOWED" \
  ORIGIN="http://${TAILNET_HOST}:$VITE_PORT" \
  "$VITE_BIN" dev --host 0.0.0.0 --port "$VITE_PORT" \
  > "$VITE_LOG" 2>&1 &
echo $! > "$VITE_PID_FILE"
cd "$REPO_ROOT"

sleep 3

VITE_PORT=$VITE_PORT
if ! curl -fsS -o /dev/null "http://localhost:$VITE_PORT/" 2>/dev/null; then
  VITE_PORT=$(grep -oP 'Local:\s+http://localhost:\K[0-9]+' "$VITE_LOG" 2>/dev/null | tail -1 || echo "$DEFAULT_PORT")
fi

POSTGRES_PORT="${POSTGRES_PORT:-5435}"
cat <<EOF

============================================================
  m3tacron local stack is running

  Local access:
    Frontend: http://localhost:$VITE_PORT  (hot-reload via Vite)
    Backend:  http://localhost:${BACKEND_PORT}       (docs at /docs)

  Tailnet access (other users):
    Frontend: http://${TAILNET_HOST}:$VITE_PORT
    Backend:  http://${TAILNET_HOST}:${BACKEND_PORT}/docs

  Postgres: localhost:${POSTGRES_PORT}              (m3tacron / m3tacron)
  Dump age: $(stat -c %y "$DUMP_FILE" 2>/dev/null | cut -d. -f1 || echo "unknown")
============================================================
  To stop: bash scripts/local_dev/up.sh --stop
  Logs:    bash scripts/local_dev/logs.sh [backend|postgres]
EOF
