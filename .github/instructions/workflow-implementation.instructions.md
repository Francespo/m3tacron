---
name: workflow-implementation
description: "Use when executing approved work: implement changes, handle issue-linking edge cases, and keep GitHub plan-comment sync aligned with approved scope."
---

## Implementation Phase Rules

- Enter implementation phase only when the user explicitly asks to execute changes.
- If issue(s) are selected, proceed directly with implementation-oriented work.
- Do not force discovery or planning again unless the user explicitly requests it.
- If implementation is requested with no issue provided, search open issues for likely matches and ask the user to confirm the correct issue.
- If no matching issue is found, ask explicit confirmation before proceeding without an issue and state clearly that no issue is linked.
- Primary plan source is the approved plan in current chat/context.
- If no approved plan is available in current chat/context and issue(s) are selected, use approved plan comments from the linked GitHub issue(s).
- If no approved plan exists, ask whether to return to planning phase or continue with an explicitly approved quick-fix scope.
- At the end of implementation phase, open a pull request for the implemented changes.
- Pull request must target branch `dev` as base branch.
- Pull request body must include `Closes #<issue-id>` for each linked issue.
- If browser access is available, visually verify changes on the PR preview URL `https://<pr-id>.dev.m3tacron.com`.
- PR preview usually becomes available about 45-60 seconds after PR creation.
- Treat the preview as ready when a PR bot comment states that preview deployment is ready; from that moment, preview URL should be accessible.
- If preview is not yet ready, re-check PR comments and retry access before final handoff.
- Technical plan comments posted to GitHub must always be written in English.
- If the plan changes later, update the existing plan comment rather than adding a new one.
