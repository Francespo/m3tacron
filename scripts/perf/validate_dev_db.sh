#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

DB_URL=""
EVIDENCE_DIR="$PROJECT_ROOT/.omo/evidence"
MIN_TOURNAMENTS="${MIN_TOURNAMENTS:-10}"
CI_MODE=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Validate local dev or live database schema and row counts before performance runs.

Options:
  --ci             Non-interactive mode for CI
  --url URL        Use a PostgreSQL connection URL (e.g. postgres://user:pass@host:5432/db)
                   When set, overrides LOCAL_DB_* and uses read-only connection.
  --output-dir DIR Output directory for the manifest (default: .omo/evidence/)
  -h, --help       Show this help

Environment:
  LOCAL_DB_HOST     PostgreSQL host (default: localhost)
  LOCAL_DB_PORT     PostgreSQL port (default: 5433)
  LOCAL_DB_NAME     PostgreSQL database (default: m3tacron_perf)
  LOCAL_DB_USER     PostgreSQL user (default: perf_user)
  LOCAL_DB_PASSWORD PostgreSQL password (default: perf_password)
  DB_URL            Same as --url (overrides LOCAL_DB_*)
  MIN_TOURNAMENTS   Minimum tournament count for smoke (default: 10)
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ci) CI_MODE=true; shift ;;
        --url) DB_URL="$2"; shift 2 ;;
        --output-dir) EVIDENCE_DIR="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

DB_URL="${DB_URL:-}"

if [ -n "$DB_URL" ]; then
    if [[ "$DB_URL" =~ ^postgres(ql)?:// ]]; then
        DB_HOST=$(echo "$DB_URL" | sed -E 's|^postgres(ql)?://([^:]+):[^@]+@([^:/]+):?([0-9]*)/[^?]+|\3|')
        DB_PORT=$(echo "$DB_URL" | sed -E 's|^postgres(ql)?://([^:]+):[^@]+@([^:/]+):?([0-9]*)/[^?]+|\4|')
        DB_NAME=$(echo "$DB_URL" | sed -E 's|^postgres(ql)?://[^/]+/([^?]+)(\?.*)?$|\2|')
        DB_USER=$(echo "$DB_URL" | sed -E 's|^postgres(ql)?://([^:]+):[^@]+@.*$|\1|')
        DB_PASSWORD=$(echo "$DB_URL" | sed -E 's|^postgres(ql)?://[^:]+:([^@]+)@.*$|\1|')
        DB_PORT="${DB_PORT:-5432}"
        DB_LABEL="live"
    else
        echo "ERROR: --url must be a postgres:// or postgresql:// URL"
        exit 1
    fi
else
    DB_HOST="${LOCAL_DB_HOST:-localhost}"
    DB_PORT="${LOCAL_DB_PORT:-5433}"
    DB_NAME="${LOCAL_DB_NAME:-m3tacron_perf}"
    DB_USER="${LOCAL_DB_USER:-perf_user}"
    DB_PASSWORD="${LOCAL_DB_PASSWORD:-perf_password}"
    DB_LABEL="local"
fi

mkdir -p "$EVIDENCE_DIR"

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
MANIFEST_FILE="$EVIDENCE_DIR/validation_manifest_${TIMESTAMP}.json"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

run_query() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "$1" 2>/dev/null || echo ""
}

check_passed=0
check_failed=0
all_checks=()

record_check() {
    local name="$1"
    local status="$2"
    local expected="$3"
    local actual="$4"
    all_checks+=("{\"name\":\"$name\",\"status\":\"$status\",\"expected\":$expected,\"actual\":$actual}")
    if [ "$status" = "passed" ]; then
        ((check_passed++))
    else
        ((check_failed++))
    fi
}

log "Validating $DB_LABEL database ($DB_NAME on $DB_HOST:$DB_PORT)"

REQUIRED_TABLES=("tournament" "playerresult" "match" "supporter" "contribution" "playerstanding" "teammatch" "teamstanding")
CRITICAL_COLUMNS=(
    "tournament:id,name,date"
    "playerresult:id,tournament_id,player_name"
    "match:id,tournament_id,round_number"
)

log "--- Table and Row Count Checks ---"
for table in "${REQUIRED_TABLES[@]}"; do
    row_count=$(run_query "SELECT COUNT(*) FROM \"$table\";")
    if [ -z "$row_count" ] || [ "$row_count" = "" ]; then
        log "  FAIL: Table '$table' does not exist"
        record_check "table_$table" "failed" 1 0
    else
        log "  OK: Table '$table' has $row_count rows"
        record_check "table_$table" "passed" 1 1
        record_check "rows_$table" "passed" 0 "$row_count"
    fi
done

log "--- Column Checks ---"
for entry in "${CRITICAL_COLUMNS[@]}"; do
    IFS=":" read -r table columns <<< "$entry"
    for col in $(echo "$columns" | tr ',' ' '); do
        col_exists=$(run_query "SELECT 1 FROM information_schema.columns WHERE table_name='$table' AND column_name='$col';")
        if [ -n "$col_exists" ] && [ "$col_exists" = "1" ]; then
            log "  OK: Column '$table.$col' exists"
            record_check "column_${table}_${col}" "passed" 1 1
        else
            log "  FAIL: Column '$table.$col' missing"
            record_check "column_${table}_${col}" "failed" 1 0
        fi
    done
done

log "--- Smoke Query ---"
smoke_result=$(run_query "SELECT COUNT(*) FROM tournament WHERE player_count > 0;")
if [ -n "$smoke_result" ]; then
    log "  OK: Smoke query returned $smoke_result tournaments with players"
    record_check "smoke_query" "passed" 1 "$smoke_result"
else
    log "  FAIL: Smoke query failed"
    record_check "smoke_query" "failed" 1 0
fi

total_checks=$((check_passed + check_failed))
overall_status="passed"
if [ "$check_failed" -gt 0 ]; then
    overall_status="failed"
fi

cat > "$MANIFEST_FILE" <<EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "database": "$DB_NAME",
  "host": "$DB_HOST:$DB_PORT",
  "source": "$DB_LABEL",
  "status": "$overall_status",
  "total_checks": $total_checks,
  "passed": $check_passed,
  "failed": $check_failed,
  "checks": [
    $(IFS=,; echo "${all_checks[*]}")
  ]
}
EOF

echo ""
log "Validation complete: $check_passed passed, $check_failed failed"
log "Manifest saved to: $MANIFEST_FILE"

if [ "$check_failed" -gt 0 ]; then
    echo ""
    log "ERROR: $check_failed check(s) failed. Database validation did not pass."
    exit 1
fi

log "Database validation PASSED. Ready for performance tests."
