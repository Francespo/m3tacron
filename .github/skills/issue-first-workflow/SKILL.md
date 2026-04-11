---
name: issue-first-workflow
description: "Run a phase-based issue-first workflow across separate chats: discovery, grouped issue creation, and explicit-start planning with approval-gated GitHub plan sync."
argument-hint: "Choose phase entry: discovery, group-and-create issues, or plan drafting"
user-invocable: true
---

# Issue-First Workflow

Use this skill as a phase entrypoint. You can run any phase independently, including in separate chats.

## When To Use

- You are exploring potential improvements.
- You have multiple bugs or enhancement ideas to triage.
- You want grouped issue creation in one pass.
- You are drafting an implementation plan in plan mode.

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
   - Draft technical implementation plan per selected issue.
   - Wait for explicit user approval, then sync to GitHub comment automatically when an issue is linked.

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
- Approved plan comments posted or updated without duplication when issue-linked and approved.
- Clear handoff target for local, CLI, or cloud agents across branches/worktrees.
