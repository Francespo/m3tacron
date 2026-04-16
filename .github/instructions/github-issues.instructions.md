---
name: github-issues
applyTo: "**/*"
description: "Use when creating or managing GitHub issues for this repository. Enforces the repo's issue creation workflow and required metadata."
---

## GitHub Issue Creation Guidelines

Follow the repository's issue workflow exactly when opening new GitHub issues.

- Check for existing relevant issues first using `gh issue list` to avoid duplicates.
- Clarify scope with the user before creating the issue.
- Use `gh issue create` to open the issue before starting implementation.

### Required issue body format

Each issue body must include:

- `Objective`: A short statement of what the issue is intended to accomplish.
- `Context & Symptoms`: A developer-focused description of the current problem or goal, including relevant files or behavior. Avoid prescribing a rigid technical solution.
- `Expected Outcome`: A concise description of the wanted end state and acceptance outcome, without technical implementation details unless explicitly discussed.

Do not store Priority and Size in the issue body. Manage them through GitHub Project fields.

### Markdown formatting and template

- Write issue bodies in GitHub Flavored Markdown.
- Keep section order fixed: `Objective`, `Context & Symptoms`, `Expected Outcome`.
- Use one blank line between sections and avoid trailing whitespace.
- Use concise bullet points when listing symptoms or acceptance outcomes.
- Keep tone human-written, specific, and repository-aware.

Use this template:

```markdown
## Objective

<1-3 lines describing the goal>

## Context & Symptoms

- <current behavior or problem>
- <where it appears: route/module/component>
- <impact on users/developers>

## Expected Outcome

- <observable end state>
- <acceptance-oriented result>
```

### Newlines and special formatting in CLI

- Prefer `gh issue create --body-file <file>` for multi-line content.
- If creating from shell inline, prefer a heredoc with a quoted delimiter to preserve formatting exactly:

```bash
cat > /tmp/issue-body.md <<'EOF'
## Objective

...
EOF

gh issue create --title "..." --body-file /tmp/issue-body.md
```

- Avoid packing multi-line Markdown into a single `--body` string when possible.
- When issue text includes special characters (for example `` ` ``, `$`, `*`, `_`, or `#`), use `--body-file` to avoid shell escaping errors.

### Project field updates (Priority and Size)

- After issue creation, set Priority and Size in the linked GitHub Project item.
- Allowed `Size` values: `S`, `M`, `L`.
- Assign `Size` using these measurable criteria:
  - `S`: small scoped change, usually one flow/module, up to about 3 files touched, with localized edits or small additions.
  - `M`: medium scoped change, usually up to 2 related flows/modules, about 4-8 files touched, with moderate additions/refactors.
  - `L`: largest allowed single-issue scope, usually up to 3 related flows/modules, about 9-15 files touched, with substantial but cohesive changes.
- If scope exceeds `L` (for example more than 15 files touched, more than 3 flows/modules, or would require more than one PR), split it into cohesive sub-issues before creation.
- Allowed `Priority` values:
  - `Urgent & Important`
  - `Not Urgent & Important`
  - `Urgent & Not Important`
  - `Not Urgent & Not Important`
- Use these exact option names when mapping to project single-select options.
- Use CLI commands in this sequence:
  - `gh project field-list <project-number> --owner <owner> --format json`
  - `gh project item-list <project-number> --owner <owner> --format json`
  - `gh project item-edit --id <item-id> --project-id <project-id> --field-id <field-id> --single-select-option-id <option-id>`
- Use one `gh project item-edit` invocation per field update.

### Multi-Issue Discussion and Creation

- When multiple problems or improvement ideas are discussed in one conversation, group them into cohesive issues first.
- Grouping and drafting are a single workflow pass: create grouped issues in the same phase once scope is clear.
- Keep issue scope balanced: avoid very small issues and avoid giant umbrella issues.
- Ask clarifying questions before creating issues, not after.
- Before creating, request explicit confirmation of both:
  - the proposed grouping
  - the proposed issue titles and bodies
  - the proposed Priority and Size for each issue (to be set in the project fields)

### Labels and milestone

- Assign type and domain labels on the Issue only.
- Use one type label: `bug`, `enhancement`, `refactor`, or `documentation`.
- Use one or more domain labels: `frontend`, `backend`, `performance`.
- Assign the appropriate milestone when creating the issue.

### Other workflow rules

- Keep issue text objective, professional, and developer-to-developer.
- Keep issue text concise and human-written; avoid generic AI-style phrasing.
- Issue title and issue body must always be written in English.
- Technical plan comments posted on GitHub must always be written in English.
- After creating issues, do not automatically transition to technical planning unless the user explicitly asks to start planning/implementation.
- Before coding begins for an issue, prepare a technical plan but post it as a comment only after explicit user approval.
- If the approved plan changes later, update the existing plan comment instead of adding a new one.
