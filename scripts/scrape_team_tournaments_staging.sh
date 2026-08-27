#!/usr/bin/env bash
set -euo pipefail
# Re-scrape only Longshanks team tournaments on staging (targeted backfill,
# not a full 32×3-month sweep). The team-board bug only affects these
# 60 is_team_event=true source=longshanks rows (~17 with 0 matches, ~5 with
# 1-10 matches); no need to re-scrape the whole DB.
#
# Usage: ./scripts/scrape_team_tournaments_staging.sh [--dry-run] [--ref REF]
#   --dry-run   list URLs without dispatching
#   --ref REF   workflow ref (default: current branch or main)
#
# Under the hood it dispatches `scrape_tournaments.yml` in tournament_urls
# mode with `environment=staging overwrite=true` in small batches so the
# Playwright Longshanks jobs don't overlap on staging's single DB.

REF=""
DRY_RUN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --ref) REF="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) echo "Usage: $0 [--dry-run] [--ref REF]"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$REF" ]; then
  REF="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
  # If we're on a detached HEAD or non-pushable branch, fall back to main
  if ! git ls-remote --heads origin "$REF" 2>/dev/null | grep -q .; then
    REF="main"
  fi
fi

# 1. Collect team Longshanks URLs from staging (direct DB via SSH tunnel).
# Prefer the same query the workflow uses: is_team_event=true + longshanks
# Filter to longshanks sources only (team events only exist there).
HOST="audit-bot@84.8.253.2"
KEY="${SSH_KEY:-$HOME/.ssh/m3tacron_audit_bot}"

echo "[team-staging] ref=$REF  dry-run=$DRY_RUN"
echo "[team-staging] fetching team tournament URLs from staging (m3tacron_staging)..."
URLS_FILE="$(mktemp)"
trap 'rm -f "$URLS_FILE"' EXIT

ssh -i "$KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=12 "$HOST" \
  "docker exec rdvq2p6xwxho16pbcyd40w0d psql -U postgres -d m3tacron_staging -t -A -c \"SELECT url FROM tournament WHERE is_team_event = true AND source = 'longshanks' ORDER BY date;\"" \
  2>&1 | tr -d ' \r' | grep -E '^https://' > "$URLS_FILE" || true

COUNT="$(grep -c https "$URLS_FILE" 2>/dev/null | tr -d ' ' || echo 0)"
echo "[team-staging] found $COUNT team Longshanks URLs on staging"
if [ "$COUNT" -eq 0 ]; then
  echo "[team-staging] No URLs found — is the staging DB populated? Try without --ref override or check is_team_event population."
  exit 1
fi

# 2. Dry-run mode: just list
if [ "$DRY_RUN" = 1 ]; then
  echo "[team-staging] --dry-run: listing URLs (first 20):"
  head -n 20 "$URLS_FILE"
  echo "... ($COUNT total, not dispatching)"
  exit 0
fi

# 3. Batch and dispatch sequentially (one batch at a time, wait for completion)
BATCH_SIZE="${BATCH_SIZE:-20}"
TOTAL_BATCHES=$(( (COUNT + BATCH_SIZE - 1) / BATCH_SIZE ))
echo "[team-staging] dispatching $COUNT URLs in $TOTAL_BATCHES batch(es) of $BATCH_SIZE, staging, overwrite=true"
echo "[team-staging] workflow: scrape_tournaments.yml  ref=$REF  tournament_urls mode"
echo ""

BATCH_NUM=0
LINES=()
while IFS= read -r U; do
  LINES+=("$U")
done < "$URLS_FILE"

for ((i=0; i<COUNT; i+=BATCH_SIZE)); do
  BATCH_NUM=$((BATCH_NUM + 1))
  BATCH_URLS=$(printf "%s\n" "${LINES[@]:$i:$BATCH_SIZE}")
  BATCH_COUNT=$(echo "$BATCH_URLS" | grep -c https || echo 0)
  echo "======================================================================"
  echo "[team-staging $BATCH_NUM/$TOTAL_BATCHES] dispatching $BATCH_COUNT URL(s) at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "  URLs: $(echo "$BATCH_URLS" | tr '\n' ' ' | cut -c1-200) ..."
  echo "======================================================================"

  set +e
  gh workflow run scrape_tournaments.yml \
    --ref "$REF" \
    -f tournament_urls="$(echo "$BATCH_URLS")" \
    -f environment=staging \
    -f overwrite=true \
    -f upload_sqlite_artifact=false 2>&1
  EC=$?
  set -e
  if [ $EC -ne 0 ]; then
    echo "[team-staging $BATCH_NUM/$TOTAL_BATCHES] dispatch failed ($EC) — retry in 30s"
    sleep 30
    gh workflow run scrape_tournaments.yml \
      --ref "$REF" \
      -f tournament_urls="$(echo "$BATCH_URLS")" \
      -f environment=staging \
      -f overwrite=true \
      -f upload_sqlite_artifact=false || {
        echo "[team-staging $BATCH_NUM/$TOTAL_BATCHES] second attempt failed — continue (manual retry: batch $BATCH_NUM/$TOTAL_BATCHES)"
        continue
      }
  fi

  echo "[team-staging $BATCH_NUM/$TOTAL_BATCHES] dispatched — waiting for completion (no next batch until done)..."
  sleep 12
  RUN_ID=""
  for _ in $(seq 1 30); do
    RUN_ID=$(gh run list --workflow scrape_tournaments.yml --limit 5 --json databaseId,status,createdAt --jq 'sort_by(.createdAt) | reverse | .[0].databaseId' 2>/dev/null || echo "")
    [ -n "$RUN_ID" ] && [ "$RUN_ID" != "null" ] && break
    sleep 5
  done
  if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
    echo "[team-staging $BATCH_NUM/$TOTAL_BATCHES] warning: could not resolve RUN_ID — sleep 60s"
    sleep 60
    continue
  fi
  echo "[team-staging $BATCH_NUM/$TOTAL_BATCHES] tracking run $RUN_ID ..."
  while true; do
    sleep 45
    INFO=$(gh run view "$RUN_ID" --json status,conclusion 2>/dev/null || echo '{"status":"unknown","conclusion":null}')
    STATUS=$(echo "$INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "?")
    CONCL=$(echo "$INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); v=d.get('conclusion'); print(v if v else '-')" 2>/dev/null || echo "?")
    echo "[team-staging $BATCH_NUM/$TOTAL_BATCHES] run $RUN_ID status=$STATUS conclusion=$CONCL at $(date -u +%H:%M:%SZ)"
    if [ "$STATUS" = "completed" ]; then
      echo "[team-staging $BATCH_NUM/$TOTAL_BATCHES] completed $CONCL"
      sleep 15
      break
    fi
  done
done

echo ""
echo "[team-staging] all $TOTAL_BATCHES team batch(es) done at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[team-staging] promote when ready: gh workflow run promote_staging.yml -f confirm=YES -f backup=true"
