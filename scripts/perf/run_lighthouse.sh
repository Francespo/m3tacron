#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_URL="${LIGHTHOUSE_URL:-http://localhost:3333}"
REPORTS_DIR="${REPORTS_DIR:-$PROJECT_ROOT/reports}"
LIGHTHOUSE_CONFIG="$PROJECT_ROOT/lighthouserc.json"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Run Lighthouse CI frontend performance checks.

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

echo "Running Lighthouse CI against $FRONTEND_URL"
echo "Config: $LIGHTHOUSE_CONFIG"

npx lhci autorun --config="$LIGHTHOUSE_CONFIG" 2>&1 || true

mkdir -p "$REPORTS_DIR/lighthouse"
if [ -d "$PROJECT_ROOT/.lighthouseci" ]; then
    cp "$PROJECT_ROOT/.lighthouseci"/*.json "$REPORTS_DIR/lighthouse/" 2>/dev/null || true
fi

echo "Lighthouse complete. Reports: $REPORTS_DIR/lighthouse/"
