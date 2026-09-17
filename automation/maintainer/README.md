# Software Maintainer Controller

A reusable, narrow control plane between a conversational Hermes profile and Paseo/Pi.

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

## Hermes profile

Configure the reusable profile without changing the default Hermes profile:

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

## Operational security

- The controller executes commands as argument arrays, never through a shell.
- SSH uses a dedicated key and `StrictHostKeyChecking=accept-new`; never disable host-key checking.
- Coolify credentials remain in the machine-level CLI context with mode `0600`. The controller exposes only PR preview deployment for the configured application UUID; it cannot deploy production.
- Database credentials and connection strings must never be committed or printed. Database access is read-only unless a human explicitly authorizes a write.
- GitHub workflow permissions are read-only. Branch protection should be enabled only after the required check names have been observed on the infrastructure PR.

## Auto-merge

The controller implements shadow classification only. It has no merge operation. A result of `would_merge: true` is advisory.
