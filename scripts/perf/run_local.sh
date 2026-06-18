#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MODE="${1:-smoke}"
REPORTS_DIR="$PROJECT_ROOT/reports"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.perf.yml"

usage() {
    cat <<EOF
Usage: $(basename "$0") --mode MODE

Run performance tests locally.

Modes:
  smoke      Quick validation (default)
  baseline   Moderate load
  soak       Extended duration
  stress     High load
  all        Run all suites
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode) MODE="${2:-smoke}"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

case "$MODE" in
    smoke|baseline|soak|stress|all) ;;
    *) echo "ERROR: Invalid mode '$MODE'"; usage; exit 1 ;;
esac

mkdir -p "$REPORTS_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

cleanup() {
    log "Cleaning up..."
    docker compose -f "$COMPOSE_FILE" down -v 2>/dev/null || true
}
trap cleanup EXIT

log "Starting performance stack..."
docker compose -f "$COMPOSE_FILE" up -d --build --wait postgres backend frontend evidence 2>&1

log "Waiting for backend..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8888/ > /dev/null 2>&1; then
        log "Backend ready"
        break
    fi
    log "Waiting... ($i/30)"
    sleep 5
done

log "Validating database..."
if ! bash "$SCRIPT_DIR/validate_dev_db.sh" --ci; then
    log "ERROR: Database validation failed. Aborting."
    exit 1
fi

run_smoke() {
    log "Running k6 smoke..."
    k6 run "$PROJECT_ROOT/tests/performance/k6/smoke.js" --out json="$REPORTS_DIR/k6-smoke.json" || true
    log "Running Lighthouse..."
    npx lhci autorun --config="$PROJECT_ROOT/lighthouserc.json" 2>/dev/null || true
    log "Running pytest-benchmark..."
    cd "$PROJECT_ROOT"
    python -m pytest backend/tests/performance/test_db_queries.py \
        --benchmark-only --benchmark-min-rounds=1 \
        --benchmark-json="$REPORTS_DIR/benchmark.json" -v 2>&1 || true
    cd "$PROJECT_ROOT"
    log "Capturing Docker stats..."
    bash "$SCRIPT_DIR/capture_docker_stats.sh" --duration 30 --output "$REPORTS_DIR"
}

run_baseline() {
    log "Running k6 baseline..."
    k6 run "$PROJECT_ROOT/tests/performance/k6/baseline.js" --out json="$REPORTS_DIR/k6-baseline.json" || true
}

run_soak() {
    log "Running k6 soak..."
    DURATION="${SOAK_DURATION:-300}" k6 run "$PROJECT_ROOT/tests/performance/k6/soak.js" --out json="$REPORTS_DIR/k6-soak.json" || true
}

run_stress() {
    log "Running k6 stress..."
    k6 run "$PROJECT_ROOT/tests/performance/k6/stress.js" --out json="$REPORTS_DIR/k6-stress.json" || true
}

case "$MODE" in
    smoke)
        run_smoke
        ;;
    baseline)
        run_smoke
        run_baseline
        ;;
    soak)
        run_smoke
        run_soak
        ;;
    stress)
        run_smoke
        run_stress
        ;;
    all)
        run_smoke
        run_baseline
        run_soak
        run_stress
        ;;
esac

log "Generating report..."
bash "$SCRIPT_DIR/generate_report.sh" --reports-dir "$REPORTS_DIR" --output "$REPORTS_DIR/report.json" --run-id "perf_${MODE}_$(date '+%Y%m%d_%H%M%S')" --env "local-docker"

log "Performance suite ($MODE) complete."
