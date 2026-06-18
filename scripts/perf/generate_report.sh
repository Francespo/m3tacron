#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/reports"
OUTPUT_FILE=""
RUN_ID=""
ENVIRONMENT="local-docker"
COMMIT_SHA=""

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Generate aggregated performance report from suite artifacts.

Options:
  --reports-dir DIR    Directory containing artifacts (default: reports/)
  --output FILE        Output report path (default: reports/report.json)
  --run-id ID          Run identifier (auto-generated if omitted)
  --env ENV            Environment name (default: local-docker)
  --commit SHA         Git commit SHA
  -h, --help           Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reports-dir) REPORTS_DIR="$2"; shift 2 ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        --run-id) RUN_ID="$2"; shift 2 ;;
        --env) ENVIRONMENT="$2"; shift 2 ;;
        --commit) COMMIT_SHA="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

if [ -z "$OUTPUT_FILE" ]; then
    OUTPUT_FILE="$REPORTS_DIR/report.json"
fi
if [ -z "$RUN_ID" ]; then
    RUN_ID="perf_run_$(date '+%Y%m%d_%H%M%S')"
fi
if [ -z "$COMMIT_SHA" ]; then
    COMMIT_SHA=$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

find_passed_validation_manifest() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        echo ""
        return
    fi
    local newest_passed=""
    for f in $(ls -1t "$dir"/validation_manifest_*.json 2>/dev/null); do
        if jq -e '.status == "passed"' "$f" >/dev/null 2>&1; then
            newest_passed="$f"
            break
        fi
    done
    echo "$newest_passed"
}

collect_k6_metrics() {
    local k6_dir="$REPORTS_DIR"
    local k6_file=""
    for candidate in "$k6_dir"/k6-smoke.json "$k6_dir"/smoke.json "$PROJECT_ROOT"/.omo/evidence/k6/smoke.json; do
        if [ -f "$candidate" ]; then
            k6_file="$candidate"
            break
        fi
    done

    if [ -z "$k6_file" ] || [ ! -f "$k6_file" ]; then
        echo '{"http_metrics":[],"summary":{"total_endpoints":0,"overall_p95":0,"overall_error_rate":0,"total_requests":0}}'
        return
    fi

    python3 - "$k6_file" <<'PYEOF'
import json
import sys
from collections import defaultdict

k6_file = sys.argv[1]
endpoints = defaultdict(lambda: {"latencies": [], "errors": 0, "total": 0})

try:
    with open(k6_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "Point":
                continue
            metric = obj.get("metric", "")
            tags = obj.get("data", {}).get("tags", {})
            url = tags.get("url", tags.get("name", "unknown"))
            value = obj.get("data", {}).get("value", 0)
            endpoint = url
            if metric == "http_req_duration":
                endpoints[endpoint]["latencies"].append(value)
                endpoints[endpoint]["total"] += 1
            elif metric == "http_req_failed" and value > 0:
                endpoints[endpoint]["errors"] += 1
except FileNotFoundError:
    pass

http_metrics = []
all_lats = []
for ep, data in endpoints.items():
    lats = sorted(data["latencies"])
    if not lats:
        continue
    n = len(lats)
    p50 = lats[int(n * 0.5)]
    p95 = lats[int(n * 0.95)]
    p99 = lats[int(n * 0.99)]
    error_rate = data["errors"] / data["total"] if data["total"] > 0 else 0
    http_metrics.append({
        "endpoint": ep,
        "method": "GET",
        "p50": round(p50, 2),
        "p95": round(p95, 2),
        "p99": round(p99, 2),
        "error_rate": round(error_rate, 4),
        "total_requests": data["total"],
    })
    all_lats.extend(lats)

all_lats.sort()
n = len(all_lats)
summary = {
    "total_endpoints": len(http_metrics),
    "overall_p95": round(all_lats[int(n * 0.95)], 2) if all_lats else 0,
    "overall_error_rate": round(sum(m["error_rate"] for m in http_metrics) / len(http_metrics), 4) if http_metrics else 0,
    "total_requests": sum(m["total_requests"] for m in http_metrics),
}

print(json.dumps({"http_metrics": http_metrics, "summary": summary}))
PYEOF
}

collect_lighthouse_metrics() {
    local lh_dir=""
    for candidate in "$REPORTS_DIR"/lighthouse "$PROJECT_ROOT"/.omo/evidence/lighthouse; do
        if [ -d "$candidate" ]; then
            lh_dir="$candidate"
            break
        fi
    done

    if [ -z "$lh_dir" ] || [ ! -d "$lh_dir" ]; then
        echo '{"lighthouse":{"routes":[],"performance_score":0},"summary":{"avg_performance_score":0,"routes_tested":0}}'
        return
    fi

    python3 - "$lh_dir" <<'PYEOF'
import json
import sys
import os

lh_dir = sys.argv[1]
routes = []

for fname in sorted(os.listdir(lh_dir)):
    if not fname.endswith(".json"):
        continue
    fpath = os.path.join(lh_dir, fname)
    try:
        with open(fpath) as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        continue
    if "runWarnings" in data and data["runWarnings"]:
        continue
    categories = data.get("categories", {})
    perf = categories.get("performance", {})
    score = perf.get("score", 0)
    if score is None:
        continue
    audits = data.get("audits", {})
    lcp = audits.get("largest-contentful-paint", {}).get("numericValue", 0)
    cls = audits.get("cumulative-layout-shift", {}).get("numericValue", 0)
    requested_url = data.get("requestedUrl", data.get("finalDisplayedUrl", fname))
    routes.append({
        "route": requested_url,
        "url": requested_url,
        "performance_score": round(score, 4),
        "lcp": round(lcp, 0),
        "cls": round(cls, 4),
        "report_path": fpath,
    })

avg_score = round(sum(r["performance_score"] for r in routes) / len(routes), 4) if routes else 0
print(json.dumps({
    "lighthouse": {"routes": routes, "performance_score": avg_score},
    "summary": {"avg_performance_score": avg_score, "routes_tested": len(routes)},
}))
PYEOF
}

collect_benchmark_metrics() {
    local bench_file=""
    for candidate in "$REPORTS_DIR"/benchmark.json "$PROJECT_ROOT"/.omo/evidence/pytest-benchmark/benchmark.json; do
        if [ -f "$candidate" ]; then
            bench_file="$candidate"
            break
        fi
    done

    if [ -z "$bench_file" ] || [ ! -f "$bench_file" ]; then
        echo '{"benchmarks":[],"summary":{"total_benchmarks":0,"avg_query_time_ms":0,"max_query_time_ms":0}}'
        return
    fi

    python3 - "$bench_file" <<'PYEOF'
import json
import sys

bench_file = sys.argv[1]
try:
    with open(bench_file) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    print(json.dumps({"benchmarks":[],"summary":{"total_benchmarks":0,"avg_query_time_ms":0,"max_query_time_ms":0}}))
    sys.exit(0)

benchmarks = []
for b in data.get("benchmarks", []):
    stats = b.get("stats", {})
    benchmarks.append({
        "name": b.get("name", "unknown"),
        "mean": round(stats.get("mean", 0) * 1000, 4),
        "min": round(stats.get("min", 0) * 1000, 4),
        "max": round(stats.get("max", 0) * 1000, 4),
        "stddev": round(stats.get("stddev", 0) * 1000, 4),
        "rounds": stats.get("rounds", 0),
        "median": round(stats.get("median", 0) * 1000, 4),
    })

means = [b["mean"] for b in benchmarks]
summary = {
    "total_benchmarks": len(benchmarks),
    "avg_query_time_ms": round(sum(means) / len(means), 4) if means else 0,
    "max_query_time_ms": round(max(means), 4) if means else 0,
}

print(json.dumps({"benchmarks": benchmarks, "summary": summary}))
PYEOF
}

collect_docker_stats() {
    local stats_file=""
    for candidate in "$REPORTS_DIR"/stats_summary.json "$PROJECT_ROOT"/.omo/evidence/docker-stats/stats_summary.json; do
        if [ -f "$candidate" ]; then
            stats_file="$candidate"
            break
        fi
    done

    if [ -z "$stats_file" ] || [ ! -f "$stats_file" ]; then
        echo '{"docker_stats":[],"summary":{"total_containers":0,"total_snapshots":0,"peak_memory_mb":0,"avg_cpu_percent":0}}'
        return
    fi

    python3 - "$stats_file" <<'PYEOF'
import json
import sys

stats_file = sys.argv[1]
try:
    with open(stats_file) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    print(json.dumps({"docker_stats":[],"summary":{"total_containers":0,"total_snapshots":0,"peak_memory_mb":0,"avg_cpu_percent":0}}))
    sys.exit(0)

containers = data.get("containers", [])
docker_stats = []
for c in containers:
    docker_stats.append({
        "container": c.get("container", "unknown"),
        "cpu_percent": c.get("cpu_percent", 0),
        "memory_mb": c.get("memory_mb", 0),
    })

print(json.dumps({
    "docker_stats": docker_stats,
    "summary": {
        "total_containers": data.get("total_containers", len(docker_stats)),
        "total_snapshots": data.get("total_snapshots", 0),
        "peak_memory_mb": data.get("peak_memory_mb", 0),
        "avg_cpu_percent": data.get("avg_cpu_percent", 0),
    },
}))
PYEOF
}

collect_db_metrics() {
    local manifest_dir="$PROJECT_ROOT/.omo/evidence"
    local validation_manifest
    validation_manifest=$(find_passed_validation_manifest "$manifest_dir")

    if [ -z "$validation_manifest" ] || [ ! -f "$validation_manifest" ]; then
        echo '{"validation_status":"skipped","row_counts":{}}'
        return
    fi

    python3 - "$validation_manifest" <<'PYEOF'
import json
import sys

manifest_file = sys.argv[1]
try:
    with open(manifest_file) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    print(json.dumps({"validation_status":"skipped","row_counts":{}}))
    sys.exit(0)

row_counts = {}
checks = data.get("checks", [])
for check in checks:
    name = check.get("name", "")
    if name.startswith("rows_") and check.get("status") == "passed":
        table = name[5:]
        row_counts[table] = check.get("actual", 0)

print(json.dumps({
    "validation_status": data.get("status", "skipped"),
    "row_counts": row_counts,
    "manifest_path": manifest_file,
}))
PYEOF
}

build_db_snapshot() {
    local db_metrics="$1"
    python3 - "$db_metrics" <<'PYEOF'
import json
import sys
from datetime import datetime, timezone

db_json = sys.argv[1]
try:
    db = json.loads(db_json)
except json.JSONDecodeError:
    db = {"validation_status": "skipped", "row_counts": {}}

print(json.dumps({
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "source": "local-perf-db",
    "row_counts": db.get("row_counts", {}),
    "validation_status": db.get("validation_status", "skipped"),
}))
PYEOF
}

build_slo_checks() {
    local k6_json="$1"
    local frontend_json="$2"
    local bench_json="$3"

    python3 - "$k6_json" "$frontend_json" "$bench_json" <<'PYEOF'
import json
import sys
import os

k6 = json.loads(sys.argv[1])
frontend = json.loads(sys.argv[2])
bench = json.loads(sys.argv[3])

p95_threshold = float(os.environ.get("K6_P95_THRESHOLD", "1000"))
error_threshold = float(os.environ.get("K6_ERROR_RATE_THRESHOLD", "0.01"))
perf_threshold = float(os.environ.get("LIGHTHOUSE_PERF_THRESHOLD", "0.8"))
db_threshold = float(os.environ.get("DB_AVG_QUERY_THRESHOLD", "200"))

k6_p95 = k6.get("summary", {}).get("overall_p95", 0)
k6_error = k6.get("summary", {}).get("overall_error_rate", 0)
perf_score = frontend.get("lighthouse", {}).get("performance_score", 0)
db_avg = bench.get("summary", {}).get("avg_query_time_ms", 0)

def check(name, threshold, actual, unit):
    status = "pass" if actual <= threshold else "fail"
    return {"name": name, "status": status, "threshold": threshold, "actual": round(actual, 4), "unit": unit}

checks = [
    check("backend_p95", p95_threshold, k6_p95, "ms"),
    check("backend_error_rate", error_threshold, k6_error, "ratio"),
    check("frontend_performance", perf_threshold, 1.0 - perf_score, "score_inverted"),
    check("db_avg_query", db_threshold, db_avg, "ms"),
]

overall = "pass" if all(c["status"] == "pass" for c in checks) else "fail"

print(json.dumps({"overall": overall, "checks": checks}))
PYEOF
}

build_missing_artifacts() {
    local details="[]"
    local status="pass"

    if [ ! -f "$REPORTS_DIR/k6-smoke.json" ] && [ ! -f "$REPORTS_DIR/smoke.json" ] && [ ! -f "$PROJECT_ROOT/.omo/evidence/k6/smoke.json" ]; then
        details=$(echo "$details" | jq '. + [{"artifact":"k6_smoke","expected_path":"reports/k6-smoke.json","reason":"k6 smoke output not found"}]')
        status="degraded"
    fi

    local lh_found=false
    for d in "$REPORTS_DIR/lighthouse" "$PROJECT_ROOT/.omo/evidence/lighthouse"; do
        if [ -d "$d" ] && [ "$(ls -A "$d"/*.json 2>/dev/null)" ]; then
            lh_found=true
            break
        fi
    done
    if [ "$lh_found" = false ]; then
        details=$(echo "$details" | jq '. + [{"artifact":"lighthouse","expected_path":"reports/lighthouse/","reason":"Lighthouse reports not found"}]')
        status="degraded"
    fi

    if [ ! -f "$REPORTS_DIR/benchmark.json" ] && [ ! -f "$PROJECT_ROOT/.omo/evidence/pytest-benchmark/benchmark.json" ]; then
        details=$(echo "$details" | jq '. + [{"artifact":"pytest_benchmark","expected_path":"reports/benchmark.json","reason":"Benchmark output not found"}]')
        status="degraded"
    fi

    if [ ! -f "$REPORTS_DIR/stats_summary.json" ] && [ ! -f "$PROJECT_ROOT/.omo/evidence/docker-stats/stats_summary.json" ]; then
        details=$(echo "$details" | jq '. + [{"artifact":"docker_stats","expected_path":"reports/stats_summary.json","reason":"Docker stats summary not found"}]')
        status="degraded"
    fi

    local val_dir="$PROJECT_ROOT/.omo/evidence"
    local val_manifest
    val_manifest=$(find_passed_validation_manifest "$val_dir")
    if [ -z "$val_manifest" ]; then
        details=$(echo "$details" | jq '. + [{"artifact":"db_validation","expected_path":".omo/evidence/validation_manifest_*.json","reason":"Passed validation manifest not found"}]')
        status="degraded"
    fi

    echo "{\"status\":\"$status\",\"details\":$details}"
}

log "Collecting metrics from artifacts..."

k6_metrics=$(collect_k6_metrics)
lighthouse_metrics=$(collect_lighthouse_metrics)
bench_metrics=$(collect_benchmark_metrics)
docker_metrics=$(collect_docker_stats)
db_metrics=$(collect_db_metrics)
db_snapshot=$(build_db_snapshot "$db_metrics")
slo_checks=$(build_slo_checks "$k6_metrics" "$lighthouse_metrics" "$bench_metrics")
missing_info=$(build_missing_artifacts)

overall_status=$(echo "$missing_info" | jq -r '.status')
slo_overall=$(echo "$slo_checks" | jq -r '.overall')
if [ "$slo_overall" = "fail" ]; then
    overall_status="fail"
fi

validation_manifest_path=""
val_dir="$PROJECT_ROOT/.omo/evidence"
val_manifest=$(find_passed_validation_manifest "$val_dir")
if [ -n "$val_manifest" ]; then
    validation_manifest_path="$val_manifest"
fi

lighthouse_artifact_path=""
for d in "$REPORTS_DIR/lighthouse" "$PROJECT_ROOT/.omo/evidence/lighthouse"; do
    if [ -d "$d" ] && [ "$(ls -A "$d"/*.json 2>/dev/null)" ]; then
        lighthouse_artifact_path="$d"
        break
    fi
done

benchmark_artifact_path=""
for f in "$REPORTS_DIR/benchmark.json" "$PROJECT_ROOT/.omo/evidence/pytest-benchmark/benchmark.json"; do
    if [ -f "$f" ]; then
        benchmark_artifact_path="$f"
        break
    fi
done

docker_stats_path=""
for f in "$REPORTS_DIR/stats_summary.json" "$PROJECT_ROOT/.omo/evidence/docker-stats/stats_summary.json"; do
    if [ -f "$f" ]; then
        docker_stats_path="$f"
        break
    fi
done

python3 - "$OUTPUT_FILE" "$RUN_ID" "$ENVIRONMENT" "$COMMIT_SHA" "$db_snapshot" "$k6_metrics" "$lighthouse_metrics" "$bench_metrics" "$docker_metrics" "$slo_checks" "$overall_status" "$missing_info" "$validation_manifest_path" "$lighthouse_artifact_path" "$benchmark_artifact_path" "$docker_stats_path" <<'PYEOF'
import json
import sys
from datetime import datetime, timezone

output = sys.argv[1]
run_id = sys.argv[2]
environment = sys.argv[3]
commit_sha = sys.argv[4]
db_snapshot = json.loads(sys.argv[5])
k6 = json.loads(sys.argv[6])
lh = json.loads(sys.argv[7])
bench = json.loads(sys.argv[8])
docker = json.loads(sys.argv[9])
slo = json.loads(sys.argv[10])
overall_status = sys.argv[11]
missing = json.loads(sys.argv[12])
val_manifest_path = sys.argv[13] if len(sys.argv) > 13 else ""
lh_artifact = sys.argv[14] if len(sys.argv) > 14 else ""
bench_artifact = sys.argv[15] if len(sys.argv) > 15 else ""
docker_artifact = sys.argv[16] if len(sys.argv) > 16 else ""

report = {
    "schema_version": "1.0.0",
    "metadata": {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": environment,
        "commit_sha": commit_sha,
        "db_snapshot": db_snapshot,
    },
    "database": bench,
    "backend": k6,
    "frontend": lh,
    "infrastructure": docker,
    "slo": slo,
    "artifacts": {
        "k6_smoke": "reports/k6-smoke.json",
        "lighthouse": lh_artifact or "reports/lighthouse/",
        "pytest_benchmark": bench_artifact or "reports/benchmark.json",
        "docker_stats": docker_artifact or "reports/stats_summary.json",
        "db_validation": val_manifest_path or ".omo/evidence/validation_manifest.json",
        "validation_manifest": val_manifest_path or "",
    },
    "status": overall_status,
    "details": missing.get("details", []),
}

with open(output, "w") as f:
    json.dump(report, f, indent=2)

print(f"Report written to {output}")
PYEOF

echo "$k6_metrics" | jq -r '.' 2>/dev/null > /dev/null || true
echo "$lighthouse_metrics" | jq -r '.' 2>/dev/null > /dev/null || true
echo "$bench_metrics" | jq -r '.' 2>/dev/null > /dev/null || true

log "Redacting sensitive values..."
if [ -f "$SCRIPT_DIR/redact_logs.sh" ]; then
    temp_file=$(mktemp)
    cp "$OUTPUT_FILE" "$temp_file"
    bash "$SCRIPT_DIR/redact_logs.sh" < "$temp_file" > "$OUTPUT_FILE"
    rm -f "$temp_file"
fi

log "Report generated: $OUTPUT_FILE"
log "Run ID: $RUN_ID"
log "Status: $overall_status"
