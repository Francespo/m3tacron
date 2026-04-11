---
name: workflow-phases
description: "Use when routing a request to discovery or implementation phase in the issue-first workflow."
---

## Phase Routing

- First classify the user request as either discovery phase or implementation phase.
- If the user is in discovery phase, follow the discovery instruction set and do not start coding.
- If the user is in implementation phase with selected issue(s), proceed with implementation work and do not force a new discovery loop.
- If implementation is requested but issue scope is missing, search open issues for likely matches and confirm with the user before proceeding.
- If no matching issue exists, ask explicit confirmation before planning/implementing without an issue and state that no issue is currently linked.
- Do not move from discovery/issue-creation into technical planning unless the user explicitly asks to start planning or implementation.
- For discovery requests that involve UX/UI/responsiveness, feature ideation, or performance/refactor scouting, proactively use or suggest `Discovery Web Auditor`.
