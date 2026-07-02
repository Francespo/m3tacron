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

ROUTES=("/" "/tournaments" "/lists" "/cards" "/ships")
URLS_JSON=$(python3 -c "
import json, sys
base = sys.argv[1].rstrip('/')
routes = sys.argv[2:]
urls = [base + r for r in routes]
print(json.dumps(urls))
" "$FRONTEND_URL" "${ROUTES[@]}")

TEMP_CONFIG=$(mktemp --suffix=.json)
python3 - "$LIGHTHOUSE_CONFIG" "$URLS_JSON" "$TEMP_CONFIG" <<'PYEOF'
import json, sys
base_cfg, urls_json, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
with open(base_cfg) as f:
    cfg = json.load(f)
cfg["ci"]["collect"]["url"] = json.loads(urls_json)
with open(out_path, "w") as f:
    json.dump(cfg, f, indent=2)
PYEOF

echo "Config: $TEMP_CONFIG (urls: $URLS_JSON)"

npx lhci autorun --config="$TEMP_CONFIG" 2>&1 || true

rm -f "$TEMP_CONFIG"

mkdir -p "$REPORTS_DIR/lighthouse"
if [ -d "$PROJECT_ROOT/.lighthouseci" ]; then
    cp "$PROJECT_ROOT/.lighthouseci"/*.json "$REPORTS_DIR/lighthouse/" 2>/dev/null || true
fi

echo "Lighthouse complete. Reports: $REPORTS_DIR/lighthouse/"
