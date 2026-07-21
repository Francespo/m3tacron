#!/usr/bin/env bash
# Show status of the local stack + DB row counts.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "==> Container status:"
docker compose -f docker-compose.local.yml ps

echo
echo "==> Health probes:"
curl -fsS -o /dev/null -w "  backend  (http://localhost:8890/)    -> HTTP %{http_code}\n" http://localhost:8890/ 2>/dev/null \
  || echo "  backend  -> DOWN"
curl -fsS -o /dev/null -w "  frontend (http://localhost:3335/)    -> HTTP %{http_code}\n" http://localhost:3335/ 2>/dev/null \
  || echo "  frontend -> DOWN"

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
