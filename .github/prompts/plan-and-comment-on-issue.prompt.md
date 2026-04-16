---
name: Plan Issue Implementation
description: "Use when starting implementation for selected issue(s): draft the technical plan in plan mode and wait for explicit user approval before any GitHub comment publishing."
argument-hint: "Issue number(s), constraints, branch/worktree context, and implementation preferences"
agent: "Plan"
tools: [search, read]
---

For the selected issue(s), create a concise technical implementation plan in plan mode. Do not post anything to GitHub in this step.

## Requirements

1. Confirm the target issue number(s).
2. Draft a technical plan with:
   - Scope and non-goals
   - Proposed approach
   - Test and validation strategy
   - Risks and rollback notes
3. Ask for explicit user approval of the plan text.
4. Once approved, automatically sync the approved plan to GitHub comments when an issue is linked.
5. If no issue is linked, keep the approved plan in chat context and clearly note that no GitHub comment was synced.

## Writing Rules

- Keep plan clear and execution-oriented.
- Align tasks explicitly to issue expected outcomes.
- If multiple issues are included, separate plan sections per issue.
- Any technical plan comment posted to GitHub must be written in English.
- If an approved plan is later revised, update the existing comment rather than creating a new one.
