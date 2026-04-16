---
name: issue-first-workflow
description: "Run a phase-based issue-first workflow across separate chats: discovery, grouped issue creation, clean planning, and separate implementation execution."
argument-hint: "Choose phase entry: discovery, group-and-create issues, planning, or implementation"
user-invocable: true
---

# Issue-First Workflow

Use this skill as a phase entrypoint. You can run any phase independently, including in separate chats.

## When To Use

- You are exploring potential improvements.
- You have multiple bugs or enhancement ideas to triage.
- You want grouped issue creation in one pass.
- You are drafting/refining an implementation plan in plan mode.
- You are ready to execute implementation from approved scope.

## Phase Entry Options

1. Discovery phase
   - Use [Discovery Phase Audit](../../prompts/discovery-phase.prompt.md) as the default discovery entrypoint.
   - Use [Discovery Web Auditor](../../agents/discovery-web-auditor.agent.md) for UX/UI/responsiveness, performance/refactor, and feature discovery.
   - Discovery Web Auditor should be proactively selected or suggested when the request clearly matches this scope.
   - Clarify current vs expected state.
   - Keep issue content implementation-agnostic by default.

2. Group and create issues (single phase)
   - Use [Group And Create Issues](../../prompts/group-and-create-issues.prompt.md).
   - Group related items into cohesive issues.
   - Ask clarifications and obtain explicit confirmation before creating.
   - Check duplicates, create issues, then set Priority/Size through project fields.

3. Plan drafting (plan mode)
   - Use [Plan Issue Implementation](../../prompts/plan-and-comment-on-issue.prompt.md).
   - Draft/refine technical implementation plan per selected issue.
   - Keep this phase planning-only: no coding and no implementation actions.
   - Wait for explicit user approval, then post/update the approved plan comment on linked issue(s) following GitHub issue rules.
   - Keep final planning output ready for handoff to implementation phase.

4. Implementation phase
   - Use [Execute Implementation](../../prompts/implementation-phase.prompt.md).
   - Follow [workflow-implementation instructions](../../instructions/workflow-implementation.instructions.md).
   - Execute code changes from approved scope.
   - Use plan source priority: current chat/context first, then linked issue comments.
   - If browser access is available, visually verify changes at `https://<pr-id>.dev.m3tacron.com`.
   - Preview usually appears about 45-60 seconds after PR creation.
   - Treat preview as ready when PR bot comment reports preview deployment ready; then verify URL accessibility.
   - Open a pull request at end of implementation targeting base branch `dev`, with `Closes #<issue-id>` in PR body for linked issue(s).
   - Handle no-issue edge cases as defined in implementation instructions.

## Notes

- This skill is intentionally modular: use only the phase you need at that moment.
- If the implementation agent already has the approved plan in chat context, it can proceed directly without fetching the comment from GitHub.
- Recommended user entrypoint: use this skill for phase routing, then use the phase-specific prompt only when you want direct control.

## Default Behavior Without Prior Context

- If this skill is invoked without meaningful prior chat context, default to discovery phase.
- Ask the user which focus areas to prioritize: UX/UI/responsiveness, performance/refactor, feature opportunities.
- Ask for target routes/modules and any project constraints.

## Deliverables

- Created issue set with cohesive scope and expected outcomes.
- Planning output ready for implementation handoff.
- Approved plan comments posted or updated without duplication when issue-linked and approved.
- Pull request opened for implementation output, including `Closes #<issue-id>` when issue-linked.
- Clear handoff target for local, CLI, or cloud agents across branches/worktrees.
