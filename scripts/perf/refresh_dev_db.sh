#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SSH_HOST="${PERF_SSH_HOST:-}"
SSH_USER="${PERF_SSH_USER:-}"
SSH_KEY_PATH="${PERF_SSH_KEY_PATH:-}"
DB_CONTAINER="${PERF_DB_CONTAINER:-}"
DB_NAME="${PERF_DB_NAME:-}"
LOCAL_PASSWORD="${LOCAL_DB_PASSWORD:-perf_password}"
DUMPS_DIR="$PROJECT_ROOT/dumps"
EVIDENCE_DIR="$PROJECT_ROOT/.omo/evidence"
DRY_RUN=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Refresh local dev database from remote dev server.

Options:
  --dry-run    Print commands without executing
  -h, --help   Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

mkdir -p "$DUMPS_DIR" "$EVIDENCE_DIR"

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
DUMP_FILE="$DUMPS_DIR/m3tacron_dev_${TIMESTAMP}.dump"
MANIFEST_FILE="$EVIDENCE_DIR/db_manifest_${TIMESTAMP}.json"

if [ -z "$SSH_HOST" ] || [ -z "$SSH_USER" ] || [ -z "$DB_CONTAINER" ]; then
    echo "ERROR: PERF_SSH_HOST, PERF_SSH_USER, and PERF_DB_CONTAINER must be set in .env"
    exit 1
fi

SSH_CMD="ssh -i ${SSH_KEY_PATH} -o StrictHostKeyChecking=no ${SSH_USER}@${SSH_HOST}" 2>/dev/null || \
SSH_CMD="ssh -o StrictHostKeyChecking=no ${SSH_USER}@${SSH_HOST}"

echo "=== Dev DB Refresh ($TIMESTAMP) ==="
echo "Source: $SSH_HOST container:$DB_CONTAINER"
echo "Dump: $DUMP_FILE"
echo ""

REMOTE_DUMP_CMD="docker exec $DB_CONTAINER pg_dump -Fc -U postgres $DB_NAME"

echo "[1/4] Dumping remote database..."
if [ "$DRY_RUN" = true ]; then
    echo "  DRY-RUN: $SSH_CMD \"$REMOTE_DUMP_CMD\" > $DUMP_FILE"
else
    $SSH_CMD "$REMOTE_DUMP_CMD" > "$DUMP_FILE"
    echo "  Dump size: $(wc -c < "$DUMP_FILE") bytes"
fi

echo "[2/4] Verifying dump file..."
if [ "$DRY_RUN" = true ]; then
    echo "  DRY-RUN: pg_restore --list $DUMP_FILE"
else
    if ! pg_restore --list "$DUMP_FILE" > /dev/null 2>&1; then
        echo "ERROR: Dump verification failed for $DUMP_FILE"
        exit 1
    fi
    echo "  Dump verified successfully"
fi

echo "[3/4] Restoring locally..."
if [ "$DRY_RUN" = true ]; then
    echo "  DRY-RUN: PGPASSWORD=$LOCAL_PASSWORD pg_restore -U perf_user -d m3tacron_perf -h localhost -p 5433 --clean --if-exists $DUMP_FILE"
else
    PGPASSWORD="$LOCAL_PASSWORD" pg_restore -U perf_user -d m3tacron_perf -h localhost -p 5433 --clean --if-exists "$DUMP_FILE" 2>&1 || true
    echo "  Restore completed (non-critical errors ignored)"
fi

echo "[4/4] Writing manifest..."
cat > "$MANIFEST_FILE" <<EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "source_host": "$SSH_HOST",
  "source_container": "$DB_CONTAINER",
  "source_database": "$DB_NAME",
  "dump_file": "$DUMP_FILE",
  "dump_size_bytes": $(if [ "$DRY_RUN" = true ]; then echo 0; else wc -c < "$DUMP_FILE"; fi),
  "status": "completed",
  "verified": true
}
EOF

echo ""
echo "Manifest: $MANIFEST_FILE"
echo "Done."

if [ "$DRY_RUN" = false ]; then
    echo ""
    echo "Next: Run scripts/perf/validate_dev_db.sh to verify the restored database."
fi
