#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_URL="${LIGHTHOUSE_URL:-http://localhost:3333}"
REPORTS_DIR="${REPORTS_DIR:-$PROJECT_ROOT/reports}"
PLAYWRIGHT_CONFIG="$PROJECT_ROOT/playwright.config.ts"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Run Playwright Web Vitals performance tests.

Options:
  --url URL     Frontend URL (default: http://localhost:3333)
  --output DIR  Report output directory (default: reports/)
  -h, --help    Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --url) FRONTEND_URL="$2"; shift 2 ;;
        --output) REPORTS_DIR="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

mkdir -p "$REPORTS_DIR"

export LIGHTHOUSE_URL="$FRONTEND_URL"

echo "Running Playwright Web Vitals tests against $FRONTEND_URL"
echo "Config: $PLAYWRIGHT_CONFIG"

cd "$PROJECT_ROOT"
npx playwright test "$PROJECT_ROOT/tests/performance/playwright/web-vitals.spec.ts" \
    --config="$PLAYWRIGHT_CONFIG" \
    --output="$REPORTS_DIR" 2>&1 || true

echo "Playwright complete. Output: $REPORTS_DIR/"
