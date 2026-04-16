---
name: Plan Issue Implementation
description: "Use in planning phase for selected issue(s): draft/refine the technical plan in plan mode without implementation actions."
argument-hint: "Issue number(s), constraints, branch/worktree context, and implementation preferences"
agent: "Plan"
tools: [search, read]
---

For the selected issue(s), create a concise technical implementation plan in plan mode. Keep this phase planning-only.

## Requirements

1. Confirm the target issue number(s) if available.
2. Draft a technical plan with:
   - Scope and non-goals
   - Proposed approach
   - Test and validation strategy
   - Risks and rollback notes
3. Ask for explicit user approval of the plan text.
4. At the end of planning phase, post or update the approved plan as a GitHub issue comment when issue(s) are linked.
5. Follow all rules defined in [GitHub Issue Instructions](../instructions/github-issues.instructions.md) when posting/updating the comment.
6. If no issue is linked, keep the approved plan in chat context and clearly state that no GitHub comment was posted.
7. Return a final approved-plan block ready for implementation-phase handoff.

## Writing Rules

- Keep plan clear and execution-oriented.
- Align tasks explicitly to issue expected outcomes.
- If multiple issues are included, separate plan sections per issue.
- Any technical plan comment posted to GitHub must be written in English.
- Do not run implementation actions in this prompt.
