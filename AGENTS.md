# AGENTS

## Repository Map

A full codemap is available at `codemap.md` in the project root.

Before working on any task, read `codemap.md` to understand:
- Project architecture and entry points
- Directory responsibilities and design patterns
- Data flow and integration points between modules

For deep work on a specific folder, also read that folder's `codemap.md`.

## Commits And Pushes

- Commit in verified logical increments as work progresses, not as one large commit at the end.
- Push the branch immediately after each commit. No work may exist only in the local worktree.
- A partial but pushed artifact is strictly better than a complete but lost one, because agent runtimes can be interrupted and uncommitted work is unrecoverable.
- Keep the branch buildable at every commit.

## Issue Creation

Turning brief problem notes into work-order-grade GitHub issues (interrogation, drafting, verification criteria, creation): load the `work-order` skill at `.agents/skills/work-order/SKILL.md`.
