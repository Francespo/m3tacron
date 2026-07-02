#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MODE="smoke"
TARGET="local"
REPORTS_DIR="$PROJECT_ROOT/reports"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.perf.yml"

LIVE_FRONTEND_URL="${LIVE_FRONTEND_URL:-https://m3tacron.com}"
LIVE_API_URL="${LIVE_API_URL:-https://api.m3tacron.com}"
LIVE_DB_URL="${LIVE_DB_URL:-}"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Run performance tests against a local Docker stack or a live deployment.

Options:
  --target TARGET   local (default) or live
  --mode MODE       smoke (default) | baseline | soak | stress | spike | all
  --reports-dir DIR Reports directory (default: reports/)
  -h, --help        Show this help

Environment:
  LIVE_FRONTEND_URL   Live frontend URL (default: https://m3tacron.com)
  LIVE_API_URL        Live API base URL (default: https://api.m3tacron.com)
  LIVE_DB_URL         Read-only Postgres URL for live DB validation
                      (e.g. postgres://user:pass@host:5432/db)
  TARGET_URL          Override k6 target (auto-set for --target live)
  LIGHTHOUSE_URL      Override Lighthouse target (auto-set for --target live)
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target) TARGET="${2:-local}"; shift 2 ;;
        --mode) MODE="${2:-smoke}"; shift 2 ;;
        --reports-dir) REPORTS_DIR="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

case "$TARGET" in
    local|live) ;;
    *) echo "ERROR: Invalid target '$TARGET' (expected local|live)"; usage; exit 1 ;;
esac

case "$MODE" in
    smoke|baseline|soak|stress|spike|all) ;;
    *) echo "ERROR: Invalid mode '$MODE'"; usage; exit 1 ;;
esac

RUN_TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
RUN_ID="perf_${TARGET}_${MODE}_${RUN_TIMESTAMP}"

if [ "$TARGET" = "live" ]; then
    REPORTS_DIR="$REPORTS_DIR/live-${MODE}-${RUN_TIMESTAMP}"
    export TARGET_URL="$LIVE_API_URL"
    export LIGHTHOUSE_URL="$LIVE_FRONTEND_URL"
    export PLAYWRIGHT_BASE_URL="$LIVE_FRONTEND_URL"
    export TARGET_NAME="live"
    export ENVIRONMENT_NAME="production"
else
    REPORTS_DIR="$REPORTS_DIR/local-${MODE}-${RUN_TIMESTAMP}"
    export TARGET_NAME="local"
    export ENVIRONMENT_NAME="local-docker"
fi

mkdir -p "$REPORTS_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "Performance suite starting"
log "  target:    $TARGET"
log "  mode:      $MODE"
log "  reports:   $REPORTS_DIR"
log "  run id:    $RUN_ID"
if [ "$TARGET" = "live" ]; then
    log "  frontend:  $LIVE_FRONTEND_URL"
    log "  api:       $LIVE_API_URL"
    if [ -n "$LIVE_DB_URL" ]; then
        log "  db:        $LIVE_DB_URL"
    else
        log "  db:        (skipped, LIVE_DB_URL not set)"
    fi
fi

cleanup() {
    if [ "$TARGET" = "local" ]; then
        log "Cleaning up local stack..."
        docker compose -f "$COMPOSE_FILE" down -v 2>/dev/null || true
    fi
}
trap cleanup EXIT

if [ "$TARGET" = "local" ]; then
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
    if ! bash "$SCRIPT_DIR/validate_dev_db.sh" --ci --output-dir "$PROJECT_ROOT/.omo/evidence"; then
        log "ERROR: Database validation failed. Aborting."
        exit 1
    fi
else
    if [ -n "$LIVE_DB_URL" ]; then
        log "Validating live database (read-only)..."
        if ! bash "$SCRIPT_DIR/validate_dev_db.sh" --ci --output-dir "$PROJECT_ROOT/.omo/evidence" --url "$LIVE_DB_URL"; then
            log "ERROR: Live database validation failed. Aborting."
            exit 1
        fi
    else
        log "Skipping DB validation (LIVE_DB_URL not set)."
    fi
fi

run_k6_smoke() {
    log "Running k6 smoke..."
    TARGET_URL="$TARGET_URL" k6 run "$PROJECT_ROOT/tests/performance/k6/smoke.js" \
        --out json="$REPORTS_DIR/k6-smoke.json" || true
}

run_k6_baseline() {
    log "Running k6 baseline..."
    TARGET_URL="$TARGET_URL" k6 run "$PROJECT_ROOT/tests/performance/k6/baseline.js" \
        --out json="$REPORTS_DIR/k6-baseline.json" || true
}

run_k6_soak() {
    log "Running k6 soak..."
    DURATION="${SOAK_DURATION:-300}" TARGET_URL="$TARGET_URL" \
        k6 run "$PROJECT_ROOT/tests/performance/k6/soak.js" \
        --out json="$REPORTS_DIR/k6-soak.json" || true
}

run_k6_stress() {
    log "Running k6 stress..."
    TARGET_URL="$TARGET_URL" k6 run "$PROJECT_ROOT/tests/performance/k6/stress.js" \
        --out json="$REPORTS_DIR/k6-stress.json" || true
}

run_k6_spike() {
    log "Running k6 spike..."
    TARGET_URL="$TARGET_URL" k6 run "$PROJECT_ROOT/tests/performance/k6/spike.js" \
        --out json="$REPORTS_DIR/k6-spike.json" || true
}

run_lighthouse() {
    log "Running Lighthouse..."
    LIGHTHOUSE_URL="$LIGHTHOUSE_URL" REPORTS_DIR="$REPORTS_DIR" \
        bash "$SCRIPT_DIR/run_lighthouse.sh" --url "$LIGHTHOUSE_URL" --output "$REPORTS_DIR" || true
}

run_playwright() {
    log "Running Playwright Web Vitals..."
    PLAYWRIGHT_BASE_URL="$PLAYWRIGHT_BASE_URL" LIGHTHOUSE_URL="$PLAYWRIGHT_BASE_URL" \
        npx playwright test "$PROJECT_ROOT/tests/performance/playwright/web-vitals.spec.ts" \
        --config="$PROJECT_ROOT/playwright.config.ts" \
        --reporter=json 2>"$REPORTS_DIR/playwright.stderr" || true
    if [ -f "$PROJECT_ROOT/reports/playwright-results.json" ]; then
        cp "$PROJECT_ROOT/reports/playwright-results.json" "$REPORTS_DIR/playwright-results.json"
    fi
}

run_benchmarks() {
    log "Running pytest-benchmark..."
    cd "$PROJECT_ROOT"
    DATABASE_URL="sqlite:///$PROJECT_ROOT/m3tacron_test.db" \
        python -m pytest backend/tests/performance/test_db_queries.py \
        --benchmark-only --benchmark-min-rounds=1 \
        --benchmark-json="$REPORTS_DIR/benchmark.json" -v 2>&1 || true
    cd "$PROJECT_ROOT"
}

run_docker_stats() {
    log "Capturing Docker stats..."
    bash "$SCRIPT_DIR/capture_docker_stats.sh" --duration 30 --output "$REPORTS_DIR" || true
}

case "$MODE" in
    smoke)
        run_k6_smoke
        run_lighthouse
        run_playwright
        if [ "$TARGET" = "local" ]; then
            run_benchmarks
            run_docker_stats
        fi
        ;;
    baseline)
        run_k6_smoke
        run_k6_baseline
        run_lighthouse
        if [ "$TARGET" = "local" ]; then
            run_benchmarks
            run_docker_stats
        fi
        ;;
    soak)
        run_k6_smoke
        run_k6_soak
        run_lighthouse
        if [ "$TARGET" = "local" ]; then
            run_benchmarks
            run_docker_stats
        fi
        ;;
    stress)
        run_k6_smoke
        run_k6_stress
        run_lighthouse
        if [ "$TARGET" = "local" ]; then
            run_benchmarks
            run_docker_stats
        fi
        ;;
    spike)
        run_k6_smoke
        run_k6_spike
        run_lighthouse
        if [ "$TARGET" = "local" ]; then
            run_benchmarks
            run_docker_stats
        fi
        ;;
    all)
        run_k6_smoke
        run_k6_baseline
        run_k6_soak
        run_k6_stress
        run_k6_spike
        run_lighthouse
        if [ "$TARGET" = "local" ]; then
            run_benchmarks
            run_docker_stats
        fi
        ;;
esac

log "Generating report..."
REPORTS_DIR="$REPORTS_DIR" \
    bash "$SCRIPT_DIR/generate_report.sh" \
        --reports-dir "$REPORTS_DIR" \
        --output "$REPORTS_DIR/report.json" \
        --run-id "$RUN_ID" \
        --env "$ENVIRONMENT_NAME" \
        --target "$TARGET_NAME" || true

log "Performance suite ($TARGET/$MODE) complete."
log "Report: $REPORTS_DIR/report.json"
