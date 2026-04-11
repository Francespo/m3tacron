---
name: workflow-implementation
description: "Use when implementing selected issue(s): proceed directly with coding/planning, avoid re-running discovery, and keep work aligned with approved scope."
---

## Implementation Phase Rules

- If issue(s) are selected, proceed directly with implementation-oriented work.
- Do not force discovery mode again unless the user explicitly requests discovery.
- Enter planning only when the user explicitly asks to start planning/implementation.
- If implementation is requested with no issue provided, search open issues for likely matches and ask the user to confirm the correct issue.
- If no matching issue is found, ask explicit confirmation before planning without an issue and state clearly that no issue is linked.
- Use an approved plan from the current chat if provided; do not require fetching it from GitHub.
- Post or update the plan comment on GitHub automatically after explicit user approval of the plan text.
- If the plan changes later, update the existing plan comment rather than adding a new one.
