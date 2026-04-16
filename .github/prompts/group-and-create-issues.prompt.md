---
name: Group And Create Issues
description: "Use when discussing multiple bugs or improvements and you want cohesive grouping plus GitHub issue creation in a single pass."
argument-hint: "Discussion notes, findings, constraints, labels, and milestone preference"
agent: "agent"
tools: [search, execute]
---

Turn the current discussion into cohesive GitHub issues and create them in one workflow pass.

## Workflow

1. Extract candidate problems/improvements from the discussion.
2. Ask only essential clarification questions needed to lock scope, expected outcome, and priority.
3. Group items into cohesive issues (not tiny, not giant), based on user-visible outcome and delivery boundary.
4. Draft issue titles and bodies for all groups.
5. Ask for explicit user confirmation of the grouping and issue drafts before creating anything.
6. Check for duplicates with `gh issue list` before creating new issues.
7. Create each issue with `gh issue create`.
8. Set Priority and Size through GitHub Project fields using `gh project field-list`, `gh project item-list`, and `gh project item-edit`.
9. Use only the allowed project options:
   - Size: `S`, `M`, `L`
   - Priority: `Urgent & Important`, `Not Urgent & Important`, `Urgent & Not Important`, `Not Urgent & Not Important`
10. Assign Size using measurable criteria:

- `S`: one flow/module, up to about 3 files touched, localized edits or small additions.
- `M`: up to 2 related flows/modules, about 4-8 files touched, moderate additions/refactors.
- `L`: up to 3 related flows/modules, about 9-15 files touched, substantial but cohesive changes.

11. If scope exceeds `L` (for example more than 15 files touched, more than 3 flows/modules, or it would require more than one PR), split it into cohesive issues before creation.

## Required Issue Structure

Each issue body must include these sections:

- `Objective`
- `Context & Symptoms`
- `Expected Outcome`

Do not include Priority and Size in the issue body.

## Markdown Formatting and Template

- Write issue bodies in GitHub Flavored Markdown.
- Keep section order fixed: `Objective`, `Context & Symptoms`, `Expected Outcome`.
- Use one blank line between sections and avoid trailing whitespace.
- Use concise bullet points when listing symptoms or acceptance outcomes.
- Keep tone human-written, specific, and repository-aware.

Use this template for each issue body draft:

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

## Newlines and Special Formatting in CLI

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

## Writing Rules

- Keep tone objective and developer-to-developer.
- Write in clear, human, project-specific language. Avoid generic AI-style wording.
- Write issue titles and issue bodies only in English.
- Avoid technical implementation detail unless the user explicitly asked to include it.
- Assign exactly one type label: `bug`, `enhancement`, `refactor`, or `documentation`.
- Assign one or more domain labels: `frontend`, `backend`, `performance`.
- Set the milestone if provided by the user.
- Resolve clarifications before creation; do not defer follow-up clarification to after issue creation.

## Output

Return:

1. A short grouping rationale.
2. A pre-create confirmation block showing grouped drafts.
3. After approval, a table of created issues with number, title, labels, and milestone.
4. A summary of Priority/Size project field updates per issue.
