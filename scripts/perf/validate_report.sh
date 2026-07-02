#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCHEMA_FILE="$PROJECT_ROOT/performance-report-schema.json"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] <report.json>

Validate a performance report against the schema.

Options:
  --ci       Non-interactive CI mode
  -h, --help Show this help
EOF
}

CI_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ci) CI_MODE=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) REPORT_FILE="$1"; shift ;;
    esac
done

if [ -z "${REPORT_FILE:-}" ]; then
    echo "ERROR: Report file path is required"
    usage
    exit 1
fi

if [ ! -f "$REPORT_FILE" ]; then
    echo "ERROR: Report file not found: $REPORT_FILE"
    exit 1
fi

if [ ! -f "$SCHEMA_FILE" ]; then
    echo "ERROR: Schema file not found: $SCHEMA_FILE"
    exit 1
fi

echo "Validating report: $REPORT_FILE"
echo "Schema: $SCHEMA_FILE"

errors=0

if ! python3 -c "
import json
try:
    with open('$REPORT_FILE') as f:
        data = json.load(f)
        print('JSON syntax: OK')
except json.JSONDecodeError as e:
    print(f'JSON syntax: FAILED - {e}')
    exit(1)
" 2>&1; then
    ((errors++))
fi

REQUIRED_FIELDS=("schema_version" "metadata" "database" "backend" "frontend" "infrastructure" "slo" "artifacts")
for field in "${REQUIRED_FIELDS[@]}"; do
    if ! python3 -c "
import json
with open('$REPORT_FILE') as f:
    data = json.load(f)
    if '$field' in data:
        print('$field: OK')
    else:
        print('$field: MISSING')
        exit(1)
" 2>&1; then
        echo "  ERROR: Required field '$field' not found"
        ((errors++))
    fi
done

if ! python3 -c "
import json
with open('$REPORT_FILE') as f:
    data = json.load(f)
    md = data.get('metadata', {})
    for key in ['run_id', 'timestamp', 'environment', 'commit_sha']:
        if key not in md:
            print(f'metadata.$key: MISSING')
            exit(1)
    print('metadata structure: OK')
" 2>&1; then
    echo "  ERROR: metadata structure invalid"
    ((errors++))
fi

if ! python3 -c "
import json
with open('$REPORT_FILE') as f:
    data = json.load(f)
    slo = data.get('slo', {})
    if 'overall' not in slo:
        print('slo.overall: MISSING')
        exit(1)
    if 'checks' not in slo or not isinstance(slo['checks'], list):
        print('slo.checks: MISSING or not a list')
        exit(1)
    print('slo structure: OK')
" 2>&1; then
    echo "  ERROR: slo structure invalid"
    ((errors++))
fi

if [ "$errors" -gt 0 ]; then
    echo ""
    echo "Validation FAILED: $errors error(s) found"
    exit 1
fi

echo ""
echo "Validation PASSED"
exit 0
