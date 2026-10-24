# Points & game-data pipeline

How a points release travels from the upstream data repos to production, and
what to do when a step fails.

## Chain

```
SogeMoge/xwing-data2-legacy   (Legacy points + changelog reports)
Francespo/xwing-data2         (XWA data; YASB feed is still manual)
        │  git submodules
        ▼
Francespo/xwing-unified-data  ── 05:00 UTC daily
  scripts/sync_data.py --sync-submodules --detect-points
  • updates the nested submodules
  • Legacy: reads changelog/*.md (any name) and records date/version/counts
  • XWA: only 50P version commits; ignores versions already recorded
  • writes points_history/*.json and pushes main
        │  external_data submodule
        ▼
Francespo/m3tacron            ── 06:00 UTC daily
  scripts/sync_game_data.py --sync-submodules --rebuild-manifests
  • advances external_data to unified main (nested pins stay upstream-owned)
  • regenerates data-xwa/data-legacy manifests + points-history.json
  • scripts/validate_points_pipeline.py
  • opens/updates the chore/game-data-sync PR
  • with SYNC_BOT_TOKEN: approves the PR and enables auto-merge
        │  merge → Coolify auto-deploy
        ▼
production                    api.m3tacron.com / m3tacron.com
        │
        ▼
Pipeline Health (4×/day) + external uptime monitor
```

## Required settings

### GitHub Actions PR creation

Repo → **Settings → Actions → General → Workflow permissions** → enable
**Allow GitHub Actions to create and approve pull requests** → Save.

Without it `GITHUB_TOKEN` cannot call `createPullRequest`. The workflow then
falls back to `SYNC_BOT_TOKEN`, but that makes the bot the PR author, so the
bot cannot approve it and a human must merge. With the setting enabled the PR
author is `github-actions[bot]`, the bot supplies the review, and auto-merge is
fully hands-off.

### `SYNC_BOT_TOKEN`

A classic PAT for a write-capable bot account (for example `Franc3s-bot`),
stored as a repository secret in `Francespo/m3tacron`.

- The bot must have `repo` scope and write access to the repository.
- The PR is authored by `github-actions[bot]`; the bot supplies the required
  review, then auto-merge waits for CI.
- Without the secret the workflow still opens the PR and prints a warning; the
  health check flags a PR left open for more than 24 hours.
- Do not use the repository `GITHUB_TOKEN` for the approval: a workflow cannot
  approve its own PR.

## Validation

Run locally:

```bash
python3 scripts/validate_points_pipeline.py
pytest backend/tests/test_points_history.py -q
```

The validator checks ISO dates, newest-first ordering, `latest_date` matching
the first update, no duplicates/future dates, frontend vs `external_data`
agreement, and non-empty generated manifests. It runs in PR CI and in the sync
workflow before the PR is opened.

## Failure modes

| Symptom | Check | Fix |
|---|---|---|
| Unified workflow red | Actions → `Sync Game Data & Auto-detect Points` | Rerun; inspect the submodule/changelog error |
| Points released but not detected (Legacy) | `SogeMoge/xwing-data2-legacy/changelog/` contains a report with `**Date**` and `**Total Cards Updated**` | Ask upstream for the report, or add the entry manually |
| Points released but not detected (XWA) | `Francespo/xwing-data2` master has a `50P x.y` commit | Update the fork (YASB feed is manual today) |
| Sync PR open > 24h | `chore/game-data-sync` PR | Approve/merge; verify `SYNC_BOT_TOKEN` |
| Deploy drift | `Pipeline health` issue / `Deploy Drift Check` | Redeploy the `main` app in Coolify |
| API unreachable | `Pipeline health` issue | `docker ps`, backend logs, Coolify deployment |
| Deployed points stale | API `date_range` vs repo `points-history.json` | Merge the sync PR, wait for deploy |
| Wrong date/version recorded | `points_history/*.json` | Revert the unified data commit; fix the source report |

`Pipeline Health` runs at 01:15, 07:15, 13:15 and 19:15 UTC. It maintains a
single issue `Pipeline health: points/data drift` and closes it automatically
when the checks pass. It complements, but does not replace, the external uptime
monitor (the monitor detects “the site is down”; the health workflow detects
“the site is up but the data is stale”).

## Manual release

1. Add or fix the changelog report in the source repo.
2. Run `xwing-unified-data` → `Sync Game Data & Auto-detect Points`.
3. Run `m3tacron` → `Sync Game Data` (or wait for 06:00 UTC).
4. Merge/approve the `chore/game-data-sync` PR (auto-merge if the bot token is
   configured).
5. Confirm `/api/meta-snapshot?...&time_range=points_update` shows the new date.

## Known gap: XWA / YASB

The scheduled unified workflow updates submodules and detects versions, but it
does **not** run `--sync-yasb`. Even if it did, the YASB patch would modify the
nested `xwing-data2` working tree, and the parent can only commit the submodule
gitlink.

Phase 2 (not implemented yet) is a workflow inside `Francespo/xwing-data2` that:

1. downloads YASB `cards-common.coffee`;
2. patches pilot (and upgrade) costs/loadouts;
3. reads the latest YASB commit with a `50P x.y[.z]` version and its date;
4. commits with `data: apply YASB 50P x.y points (YYYY-MM-DD)`;
5. pushes master (or opens a PR with auto-merge).

The unified detector then needs to parse the `(YYYY-MM-DD)` from that commit
subject instead of using the workflow run date. Until then, an XWA release that
is not committed to `Francespo/xwing-data2` will not be detected.
