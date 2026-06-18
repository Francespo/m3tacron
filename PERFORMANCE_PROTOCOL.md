# M3tacron Performance Suite Protocol

## Overview

This document describes how to run, interpret, and maintain the M3tacron performance suite. The suite measures backend API latency, frontend Core Web Vitals, database query performance, and container resource usage using a local Docker topology with a raw copy of the dev PostgreSQL database.

**Important**: Scheduled CI results are regression signals, not production-grade load claims. The local Docker environment does not replicate production hardware or network conditions.

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Node.js 20+
- k6 (`https://k6.io/docs/get-started/installation/`)
- Lighthouse CI (`npm install -g @lhci/cli`)
- Playwright (`npx playwright install --with-deps chromium`)
- pytest-benchmark (`pip install pytest-benchmark`)

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Start the performance stack
docker compose -f docker-compose.perf.yml up -d --build --wait

# 3. Validate the database
bash scripts/perf/validate_dev_db.sh

# 4. Run a smoke test
bash scripts/perf/run_local.sh --mode smoke
```

## Database Setup

### Refreshing the Dev Database

The raw dev database copy script connects to the real M3tacron server via SSH, dumps the dev PostgreSQL database using `pg_dump -Fc`, and restores it locally.

```bash
# Configure SSH access in .env
# PERF_SSH_HOST=your-server-ip
# PERF_SSH_USER=your-ssh-user
# PERF_SSH_KEY_PATH=~/.ssh/id_ed25519

# Dry run (prints commands without executing)
bash scripts/perf/refresh_dev_db.sh --dry-run

# Actual refresh
bash scripts/perf/refresh_dev_db.sh
```

**Security Warning**: The raw database contains real player data. Never commit dump files, share them, or upload them to CI artifacts. The `.gitignore` excludes `*.dump`, `*.sql`, and the `dumps/` directory.

### Validating the Database

Before running any performance tests, validate the restored database:

```bash
bash scripts/perf/validate_dev_db.sh
```

This checks:
- Required tables exist (tournament, playerresult, match, supporter, contribution, playerstanding, teammatch, teamstanding)
- Row counts meet minimum thresholds
- Critical columns are present
- A smoke query succeeds

If validation fails, performance tests will not run.

## Run Modes

### Local Orchestration

```bash
# Smoke: quick validation run
bash scripts/perf/run_local.sh --mode smoke

# Baseline: moderate load for establishing metrics
bash scripts/perf/run_local.sh --mode baseline

# Soak: extended duration for stability
bash scripts/perf/run_local.sh --mode soak

# Stress: high load for failure behavior
bash scripts/perf/run_local.sh --mode stress

# All: runs all suites sequentially
bash scripts/perf/run_local.sh --mode all
```

### Individual Suites

```bash
# k6 API load tests
k6 run tests/performance/k6/smoke.js
k6 run tests/performance/k6/baseline.js

# Lighthouse CI frontend checks
npx lhci autorun --config=lighthouserc.json

# Playwright Web Vitals
npx playwright test tests/performance/playwright/web-vitals.spec.ts

# pytest-benchmark DB queries
python -m pytest backend/tests/performance/test_db_queries.py --benchmark-only

# Docker resource metrics
bash scripts/perf/capture_docker_stats.sh --duration 60 --output reports/stats
```

## Report Generation

```bash
# Generate aggregated report
bash scripts/perf/generate_report.sh --reports-dir reports --output reports/report.json

# Validate report against schema
bash scripts/perf/validate_report.sh reports/report.json

# Redact sensitive values from logs
cat reports/report.json | bash scripts/perf/redact_logs.sh > reports/report-redacted.json
```

## CI Usage

The GitHub Actions workflow runs on:
- **Schedule**: Weekly on Monday at 06:00 UTC
- **Manual dispatch**: Via the Actions tab with selectable mode (smoke/baseline/all)

CI runs smoke checks by default. Full stress/soak remains manual-only to avoid excessive CI cost.

### Setting Up CI Secrets

In your repository settings, add:
- `LOCAL_DB_PASSWORD`: PostgreSQL password for the local perf stack

### Interpreting CI Results

- Performance artifacts are retained for 30 days
- Results are regression signals, not production benchmarks
- Threshold failures indicate potential regressions that warrant investigation
- Compare runs over time for trend analysis

## Security Notes

- **Never commit**: `.env`, SSH keys, DB URLs, raw dumps, SQL dumps, credentials, or generated reports
- **Never run load tests against production**
- **Raw dev DB contains real player data**: treat as sensitive/local-only
- **Log redaction**: `scripts/perf/redact_logs.sh` masks DB URLs, passwords, SSH keys, and API tokens in output
- **CI secrets**: Use GitHub Actions repository secrets, never workflow text

## Troubleshooting

### Database connection refused
- Ensure the PostgreSQL container is running: `docker compose -f docker-compose.perf.yml ps`
- Check logs: `docker compose -f docker-compose.perf.yml logs postgres`

### k6 thresholds fail
- Check if the backend is healthy: `curl http://localhost:8888/`
- Review the k6 output for specific failed thresholds
- Adjust thresholds in the k6 script or via environment variables

### Lighthouse fails
- Ensure the frontend is running: `curl http://localhost:3333/`
- Check if Chromium is installed: `npx playwright install --with-deps chromium`

### Report validation fails
- Run `bash scripts/perf/validate_report.sh <report.json>` for detailed errors
- Ensure all required artifacts exist in the reports directory
