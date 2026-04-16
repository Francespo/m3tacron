---
name: workflow-phases
description: "Use when routing a request to discovery, planning, or implementation phase in the issue-first workflow."
---

## Phase Routing

- First classify the user request as discovery phase, planning phase, or implementation phase.
- If the user is in discovery phase, follow the discovery instruction set and do not start coding.
- If the user asks to define or refine a technical plan, follow the planning instruction set and keep the phase implementation-free.
- If the user asks to execute changes, follow the implementation instruction set and do not force a new discovery/planning loop unless requested.
- If the request is ambiguous between planning and implementation, ask explicitly whether the user wants plan-only or code execution.
- Do not move from discovery/issue-creation into technical planning unless the user explicitly asks to start planning or implementation.
- For discovery requests that involve UX/UI/responsiveness, feature ideation, or performance/refactor scouting, proactively use or suggest `Discovery Web Auditor`.
