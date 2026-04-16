---
name: Execute Implementation
description: "Use in implementation phase to execute approved work with clear plan-source priority and no-issue fallback handling."
argument-hint: "Issue number(s), approved plan (if present in chat), constraints, and validation targets"
agent: "agent"
---

Execute implementation changes from approved scope.

## Plan Source Priority

1. Use the approved plan already present in current chat/context as the primary source.
2. If no approved plan is present in current chat/context and issue(s) are selected, read approved plan comments from linked GitHub issue(s).
3. If no approved plan exists, ask whether to return to planning phase or continue only with an explicitly approved quick-fix scope.

## Requirements

1. Confirm issue number(s) when available.
2. Confirm implementation scope before editing.
3. Implement changes according to approved plan source.
4. Run relevant validation/tests for changed behavior.
5. Summarize implemented changes, validations, and any follow-up risks.
