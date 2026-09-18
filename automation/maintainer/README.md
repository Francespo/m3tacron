# Software Maintainer Controller

A reusable, narrow control plane between a conversational Hermes profile and direct Pi workers. Paseo remains available as a separate, manually supervised development interface.

See [`docs/AUTONOMOUS_MAINTAINER_PLAN.md`](../../docs/AUTONOMOUS_MAINTAINER_PLAN.md) for the architecture and rollout plan.

## Commands

```bash
scripts/maintainer project-list
scripts/maintainer task-list
scripts/maintainer start --project m3tacron --intent "Expected outcome" --request-id <stable-id>
scripts/maintainer status --task <task-id>
scripts/maintainer review --task <task-id>
scripts/maintainer preview-deploy --task <task-id>
scripts/maintainer feedback --task <task-id> --message "Requested revision"
scripts/maintainer approve --task <task-id>
scripts/maintainer stop --task <task-id>
scripts/maintainer audit --task <task-id>
```

State defaults to `~/.local/state/software-maintainer/state.db`. Override it with `MAINTAINER_STATE` or `--state`.

## Add a project

Add an entry to `projects.json`. Keep product knowledge and repository conventions in that project's version-controlled instruction files. The registry should contain only integration details such as checkout path, GitHub repository, branch, provider, preview template, checks, and deterministic risk policy.

## Direct Pi runtime

Each authorized task gets a dedicated `agent/<task-id>` branch, Git worktree, Pi session, event log, and detached worker process. The controller stores lifecycle state in SQLite and can resume the saved Pi session for feedback. Paseo is not used by this autonomous path.

Task runtime artifacts default to:

```text
~/.local/state/software-maintainer/
├── state.db
├── tasks/<task-id>/events.jsonl
├── tasks/<task-id>/worker.log
├── tasks/<task-id>/sessions/
└── worktrees/<project-id>/<task-id>/
```

## Hermes profile

Configure the reusable profile and install the structured Hermes plugin without changing the default profile:

```bash
python3 scripts/setup_coding_profile.py
```

After creating a private Telegram group and obtaining its chat ID:

```bash
python3 scripts/setup_coding_profile.py \
  --chat-id=-1001234567890 \
  --restart-gateway
```

Verify `/profile` reports `coding` in the dedicated group and `default` in the normal chat.

## Language policy

Conversation follows the user's language. Every persistent engineering artifact must be English. The controller prompt enforces this policy while retaining the original user message as source context.

## Structured Hermes tools

The coding profile receives `maintainer_start`, `maintainer_status`, `maintainer_review`, `maintainer_feedback`, `maintainer_approve`, and `maintainer_stop`. Hermes must use these instead of terminal commands. The tools expose no arbitrary shell, merge, repository-governance mutation, or production deployment.

## Operational security

- The controller executes commands as argument arrays, never through a shell.
- SSH uses a dedicated key and `StrictHostKeyChecking=accept-new`; never disable host-key checking.
- Coolify credentials remain in the machine-level CLI context with mode `0600`. The controller exposes only PR preview deployment for the configured application UUID; it cannot deploy production.
- Database credentials and connection strings must never be committed or printed. Database access is read-only unless a human explicitly authorizes a write.
- GitHub workflow permissions are read-only. Branch protection should be enabled only after the required check names have been observed on the infrastructure PR.

## Auto-merge

The controller implements shadow classification only. It has no merge operation. A result of `would_merge: true` is advisory.
