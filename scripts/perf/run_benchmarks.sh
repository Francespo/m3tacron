#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORTS_DIR="${REPORTS_DIR:-$PROJECT_ROOT/reports}"

usage() {
    cat <<EOF
Usage: $(basename "$0") [MODE]

Run pytest-benchmark DB query microbenchmarks.

Modes:
  all        Run all benchmarks (default)
  smoke      Run with minimal rounds for quick check

Options:
  -h, --help Show this help
EOF
}

MODE="${1:-all}"

case "$MODE" in
    all)
        python -m pytest "$PROJECT_ROOT/backend/tests/performance/test_db_queries.py" \
            --benchmark-only \
            --benchmark-json="$REPORTS_DIR/benchmark.json" \
            -v 2>&1
        ;;
    smoke)
        python -m pytest "$PROJECT_ROOT/backend/tests/performance/test_db_queries.py" \
            --benchmark-only \
            --benchmark-min-rounds=1 \
            --benchmark-json="$REPORTS_DIR/benchmark.json" \
            -v 2>&1
        ;;
    *)
        echo "Unknown mode: $MODE"
        usage
        exit 1
        ;;
esac

echo "Benchmarks complete. Output: $REPORTS_DIR/benchmark.json"
