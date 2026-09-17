# Autonomous Software Maintainer — Implementation Plan

## 1. Purpose

Build a reusable, low-friction software maintainer that lets a user discuss a change naturally, delegate implementation, and review the result through concise evidence, screenshots, and a preview environment.

The first registered project is M3tacron, but the maintainer core and the Hermes `coding` profile must not contain M3tacron-specific behavior.

## 2. Non-negotiable product requirements

1. The user may communicate with the conversational agent in any language. The agent follows the language currently used by the user.
2. All persistent engineering artifacts are written in English: configuration, code, comments, tests, documentation, stored prompts, task specifications, branches, commits, issues, pull requests, and review evidence.
3. The user is not required to fill in a work-order template. Structured task records are generated internally and adapt to task complexity.
4. The maintainer asks only questions that materially affect the expected product outcome.
5. Implementation happens in isolated Paseo worktrees and uses Pi through the Manifest `auto-coding` model.
6. GitHub and the local state database provide traceability. Conversational memory is not the source of truth for task state.
7. Product changes remain subject to human review. Low-risk auto-merge starts in shadow mode and cannot merge anything.
8. Project-specific conventions remain in each repository or project registration, not in the global Hermes profile.

## 3. Architecture

```text
User (Telegram, Hermes dashboard, or CLI)
                    |
                    v
       Hermes profile: coding
       - adaptive conversation language
       - general software-product behavior
       - model: auto-coding
                    |
                    v
       software-maintainer CLI
       - project registry
       - SQLite task state
       - deterministic policy
       - audit trail and idempotency
                    |
                    v
              Paseo daemon
       - isolated git worktree
       - Pi / manifest / auto-coding
                    |
                    v
          GitHub branch and PR
       - CI checks
       - preview deployment
       - screenshots/evidence
                    |
                    v
       Hermes review and feedback loop
```

## 4. Component responsibilities

### 4.1 Hermes `coding` profile

- Acts as a general product and engineering colleague.
- Accepts informal text, voice transcripts, screenshots, and links.
- Distinguishes exploration, proposal, implementation authorization, and review.
- Calls only the narrow maintainer CLI actions.
- Does not choose arbitrary shell commands, merge changes, or bypass safeguards.
- Uses `auto-coding` for the main conversation and material product decisions.

### 4.2 Maintainer controller

- Registers and selects projects.
- Creates durable task IDs and stores task state in SQLite.
- Starts one Paseo worktree per task.
- Builds an English implementation prompt from multilingual user intent.
- Resumes the same Paseo agent when feedback arrives.
- Reconciles local state with Paseo and GitHub after restarts.
- Generates concise review data.
- Computes a deterministic shadow auto-merge decision.
- Records every state-changing operation in an append-only audit table.

### 4.3 Paseo and Pi

- Paseo owns process and worktree orchestration.
- Pi inspects the repository, derives the technical approach, implements, tests, pushes, and opens a pull request.
- Pi follows repository instructions and never relies on the conversational agent for project-specific commands.

### 4.4 GitHub and CI

- GitHub stores pull requests and optional tracking issues.
- CI is the technical verification authority.
- Preview deployment is the preferred product-review environment for UI work.
- Branch protection and required checks must be enabled only after the workflow exists on the target branch and has demonstrated stable check names.

## 5. Task lifecycle

```text
DRAFT -> RUNNING -> REVIEW -> CHANGES_REQUESTED -> RUNNING
                    |                         |
                    +-------> APPROVED <-----+
                    |
                    +-------> BLOCKED
                    +-------> STOPPED
                    +-------> FAILED
```

- `DRAFT`: captured but not authorized.
- `RUNNING`: a Paseo agent owns the implementation or revision.
- `REVIEW`: a pull request or runnable result is ready.
- `CHANGES_REQUESTED`: user feedback has been recorded and is being delegated.
- `APPROVED`: product approval was recorded for the current head commit.
- `BLOCKED`: external input is needed.
- `STOPPED`: explicitly stopped by the user.
- `FAILED`: unrecoverable controller or agent failure.

Transitions are validated by normal code. The model cannot invent states.

## 6. Low-friction interaction contract

### Propose

The user describes an idea naturally. Hermes responds with a short understanding, a recommendation, and only material questions. No repository artifact is required.

### Start

When the user authorizes implementation, Hermes calls `start` with:

- project ID;
- expected outcome;
- confirmed product decisions;
- optional attachment paths or URLs.

The controller immediately returns a task ID and Paseo agent ID.

### Review

The controller and Hermes present:

- project and pull request;
- what changed;
- what the user should evaluate;
- preview URL;
- screenshots or evidence;
- automated verification status;
- risk and shadow auto-merge decision.

### Feedback

Natural-language feedback and attachments are sent to the existing Paseo agent. A new task or worktree is not created.

### Approval

Approval is bound to the current pull-request head SHA. A later code change invalidates that approval.

## 7. Project registration

Each project registration defines only integration facts:

- stable project ID and display name;
- absolute source checkout path;
- GitHub repository;
- base branch;
- Paseo provider/model;
- repository instruction files;
- preview URL template;
- required checks;
- sensitive paths;
- low-risk allowlist and diff limits.

Repository-specific knowledge remains in version-controlled files such as `AGENTS.md`, `codemap.md`, and `paseo.json`.

## 8. Security and reliability

1. The controller uses argument arrays, never shell interpolation.
2. Inputs are validated and task IDs are generated by the controller.
3. SQLite uses WAL mode and transactions.
4. A per-task lease prevents duplicate starts.
5. Repeated `start`, `sync`, and `feedback` operations are idempotent where possible.
6. Agent, branch, PR, preview, and commit identifiers are persisted.
7. Sensitive paths always veto low-risk classification.
8. Shadow mode never executes a merge.
9. The Hermes tool surface does not expose arbitrary Paseo or GitHub commands.
10. Secrets remain outside the repository.
11. Logs and persisted artifacts are English; raw user messages may retain their original language as quoted source input.
12. Timeouts become visible failures or blockers rather than unbounded loops.

## 9. Shadow auto-merge policy

A pull request is only classified as a low-risk candidate when all conditions hold:

- every required check succeeded;
- no sensitive path changed;
- changed files and line count are below configured limits;
- every changed path matches the low-risk allowlist;
- the pull request is not a draft;
- no unresolved product approval is required;
- the current head commit has not changed since verification.

In this implementation the result is advisory only:

```json
{
  "mode": "shadow",
  "eligible": true,
  "would_merge": true,
  "reasons": []
}
```

The controller contains no merge operation.

## 10. Implementation phases

### Phase A — Repository foundation

- Add this plan.
- Add the generic controller package and CLI.
- Add project registration for M3tacron.
- Add unit tests for state, command construction, transitions, language policy, and risk policy.
- Add a pull-request CI workflow.

### Phase B — Hermes profile

- Back up the current Hermes installation state.
- Create the isolated `coding` profile without changing the default profile.
- Set the profile model to `custom:manifest / auto-coding`.
- Install the generic software-maintainer skill.
- Keep the conversation language adaptive and artifacts English.
- Verify profile, model, skill isolation, and a direct model response.

### Phase C — Paseo integration

- Start a no-code smoke task in a disposable worktree.
- Verify worktree creation, Pi provider selection, structured tracking, and cleanup.
- Verify restart reconciliation with `sync`.

### Phase D — Dedicated channel

- The user creates a private Telegram group and adds the existing Hermes bot.
- A setup command records the chat ID and adds a profile route to `coding`.
- Enable multiplexed profile routing.
- Restart the gateway.
- Verify `/profile` returns `coding` in the group and `default` elsewhere.
- Verify the sender allowlist.

This phase cannot be completed until the Telegram group exists and its chat ID is supplied.

### Phase E — End-to-end pilot

- Submit a small reversible improvement in the dedicated channel.
- Verify conversation in the user's language.
- Verify all generated engineering artifacts are English.
- Verify Paseo/Pi implementation, CI, preview, screenshots, feedback iteration, and approval binding.
- Observe shadow auto-merge output without merging.

### Phase F — Hardening and activation

- Run at least 10–20 supervised pull requests.
- Measure duplicate-task rate, clarification rounds, CI flake rate, recovery after restart, and incorrect low-risk classifications.
- Stabilize required check names.
- Enable a GitHub ruleset and required checks.
- Consider docs-only auto-merge only after shadow-mode evidence is satisfactory.

## 11. Verification matrix

| Capability | Verification |
|---|---|
| Controller unit behavior | `python3 -m unittest discover -s automation/maintainer/tests -v` |
| Python project regression | `pytest -m 'not performance'` |
| Frontend correctness | `npm --prefix frontend run check && npm --prefix frontend run build` |
| CLI registration | `scripts/maintainer project-list` |
| Dry-run task creation | `scripts/maintainer start --project m3tacron --intent ... --dry-run` |
| Manifest model | `/v1/models` contains `auto-coding`; direct request succeeds |
| Hermes isolation | `hermes profile show coding`; default profile remains unchanged |
| Paseo handoff | dry-run command inspection, then disposable live task |
| Restart recovery | restart controller invocation and run `sync` on the same task |
| PR discovery | `sync` records the PR matching the persisted branch |
| Risk policy | unit tests plus `review --task <id>` against a real PR |
| Telegram routing | `/profile` in dedicated group and normal chat |
| Artifact language | inspect task prompt, branch, commit, PR, code, tests, and report |
| Shadow merge safety | review result may say `would_merge`; no merge command exists |

## 12. Definition of done

The maintainer is complete for supervised production use when:

1. A user can authorize work from the Hermes `coding` profile without writing an issue or template.
2. The controller starts Pi in an isolated Paseo worktree and survives process restarts.
3. Feedback resumes the same task.
4. Pull-request and preview information is reconciled and presented concisely.
5. UI work includes visual evidence and a preview review path.
6. All persistent engineering artifacts are English.
7. The default Hermes profile and its economical routing remain unchanged.
8. Shadow policy is deterministic, tested, and incapable of merging.
9. CI passes for the controller and existing project checks.
10. The only remaining manual integration step is the user-created dedicated channel, when its external identifier has not yet been supplied.
