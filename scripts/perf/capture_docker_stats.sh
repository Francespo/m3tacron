#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

COMPOSE_FILE="$PROJECT_ROOT/docker-compose.perf.yml"
OUTPUT_DIR="${1:-$PROJECT_ROOT/reports}"
DURATION="${DURATION:-60}"
INTERVAL="${INTERVAL:-2}"

mkdir -p "$OUTPUT_DIR"

CSV_FILE="$OUTPUT_DIR/stats.csv"
JSONL_FILE="$OUTPUT_DIR/stats.jsonl"
SUMMARY_FILE="$OUTPUT_DIR/stats_summary.json"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "Starting Docker stats capture for ${DURATION}s"

containers=$(docker compose -f "$COMPOSE_FILE" ps --format '{{.Names}}' 2>/dev/null)
if [ -z "$containers" ]; then
    echo "ERROR: No running containers found from $COMPOSE_FILE"
    exit 1
fi

log "Monitoring containers: $containers"

echo "timestamp,container,cpu_percent,mem_usage,mem_limit,mem_percent,net_in,net_out,block_in,block_out" > "$JSONL_FILE"

end_time=$(($(date +%s) + DURATION))
while [ "$(date +%s)" -lt "$end_time" ]; do
    timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}}' $containers 2>/dev/null | while IFS=',' read -r name cpu mem_usage mem_pct net_io block_io; do
        echo "{\"timestamp\":\"$timestamp\",\"container\":\"$name\",\"cpu\":\"$cpu\",\"mem_usage\":\"$mem_usage\",\"mem_pct\":\"$mem_pct\",\"net_io\":\"$net_io\",\"block_io\":\"$block_io\"}" >> "$JSONL_FILE"
    done
    sleep "$INTERVAL"
done

log "Capture complete. Generating summary..."

python3 - "$JSONL_FILE" "$SUMMARY_FILE" <<'PYEOF'
import json
import sys
from collections import defaultdict

jsonl_file = sys.argv[1]
summary_file = sys.argv[2]

stats = defaultdict(lambda: {"cpu_values": [], "mem_values": [], "snapshots": 0})

with open(jsonl_file) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("timestamp"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = row.get("container", "unknown")
        cpu_str = row.get("cpu", "0%").replace("%", "")
        try:
            cpu = float(cpu_str)
        except ValueError:
            cpu = 0.0
        mem_str = row.get("mem_usage", "0B / 0B").split("/")[0].strip()
        mem_mb = 0.0
        if "GiB" in mem_str:
            mem_mb = float(mem_str.replace("GiB", "").strip()) * 1024
        elif "MiB" in mem_str:
            mem_mb = float(mem_str.replace("MiB", "").strip())
        elif "KiB" in mem_str:
            mem_mb = float(mem_str.replace("KiB", "").strip()) / 1024

        stats[name]["cpu_values"].append(cpu)
        stats[name]["mem_values"].append(mem_mb)
        stats[name]["snapshots"] += 1

containers_summary = []
for name, data in sorted(stats.items()):
    containers_summary.append({
        "container": name,
        "cpu_percent": round(sum(data["cpu_values"]) / len(data["cpu_values"]), 2) if data["cpu_values"] else 0,
        "memory_mb": round(max(data["mem_values"]), 2) if data["mem_values"] else 0,
        "snapshots": data["snapshots"],
    })

summary = {
    "total_containers": len(containers_summary),
    "total_snapshots": sum(c["snapshots"] for c in containers_summary),
    "peak_memory_mb": round(max((c["memory_mb"] for c in containers_summary), default=0), 2),
    "avg_cpu_percent": round(sum(c["cpu_percent"] for c in containers_summary) / len(containers_summary), 2) if containers_summary else 0,
    "containers": containers_summary,
}

with open(summary_file, "w") as f:
    json.dump(summary, f, indent=2)

print(f"Summary written to {summary_file}")
PYEOF

log "Docker stats saved to: $JSONL_FILE"
log "Summary saved to: $SUMMARY_FILE"
