#!/usr/bin/env bash
# Show status of the local stack + DB row counts.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# --- Detect tailnet hostname ---
HOSTNAME_SHORT="$(hostname -s 2>/dev/null || echo localhost)"
TAILSCALE_HOST=""
if command -v tailscale &>/dev/null; then
  TAILSCALE_HOST="$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['Self']['HostName'])" 2>/dev/null || true)"
fi
TAILNET_HOST="${TAILSCALE_HOST:-$HOSTNAME_SHORT}"

echo "==> Container status:"
docker compose -f docker-compose.local.yml ps

echo
BACKEND_PORT="${BACKEND_PORT:-8890}"
VITE_PORT="${VITE_PORT:-3335}"
echo "==> Health probes:"
curl -fsS -o /dev/null -w "  backend  (http://localhost:${BACKEND_PORT}/)    -> HTTP %{http_code}\n" "http://localhost:${BACKEND_PORT}/" 2>/dev/null \
  || echo "  backend  -> DOWN"
curl -fsS -o /dev/null -w "  frontend (http://localhost:${VITE_PORT}/)    -> HTTP %{http_code}\n" "http://localhost:${VITE_PORT}/" 2>/dev/null \
  || echo "  frontend -> DOWN"

echo
echo "==> Tailnet access:"
echo "  Frontend: http://${TAILNET_HOST}:${VITE_PORT}"
echo "  Backend:  http://${TAILNET_HOST}:${BACKEND_PORT}/docs"

echo
echo "==> DB row counts (if Postgres container is up):"
if docker ps --format '{{.Names}}' | grep -q 'local-postgres'; then
  docker exec local-postgres psql -U m3tacron -d m3tacron -c "
    SELECT 'tournament' AS tbl, COUNT(*) FROM tournament
    UNION ALL SELECT 'playerstanding', COUNT(*) FROM playerstanding
    UNION ALL SELECT 'match', COUNT(*) FROM match
    UNION ALL SELECT 'teamstanding', COUNT(*) FROM teamstanding
    UNION ALL SELECT 'teammatch', COUNT(*) FROM teammatch
    UNION ALL SELECT 'supporter', COUNT(*) FROM supporter
    UNION ALL SELECT 'contribution', COUNT(*) FROM contribution
    ORDER BY tbl;
  "
else
  echo "  (postgres not running)"
fi

DUMP_FILE="$REPO_ROOT/local-data/dumps/dev_latest.dump"
if [[ -f "$DUMP_FILE" ]]; then
  echo
  echo "==> Cached dump: $DUMP_FILE"
  echo "    age:    $(stat -c %y "$DUMP_FILE" 2>/dev/null | cut -d. -f1)"
  echo "    size:   $(du -h "$DUMP_FILE" | cut -f1)"
fi
