---
name: work-order
description: "Turn brief problem notes into complete, verifiable GitHub issues (work orders). Use when the user describes bugs or improvement ideas and wants them drafted into agent-ready, verification-grade issues — the user decides the desired solution, you propose options when ambiguous, then draft and create the issues."
---

# Work-Order Issue Creation

The user spots problems and describes them briefly. You turn those notes into **work-order-grade GitHub issues** — executable by a context-less agent later (paseo spawn, Hub trigger, parallel worktrees).

## Decision Model

- **The user decides WHAT** — the desired end result, including any technical preference they have.
- When several credible ways to reach the goal exist, **you propose options with strengths and weaknesses** and the user picks. Offer options only when genuinely ambiguous — not for obvious fixes.
- **You own HOW** — figuring out the path to the chosen goal is your job, not a question you ask the user.
- Issues record the user's **solution intent** (the decision), never an implementation plan. The implementing agent derives HOW.

## Flow

1. Collect the user's brief problem notes (they may dump several at once).
2. Interrogate — ask for what is missing, never guess.
3. Propose solutions — for each problem with multiple viable approaches, present options + trade-offs; user picks the WHAT.
4. Draft every issue using the template below.
5. Run the Verifiability Test on every draft.
6. Confirm with the user, explicitly: target repo, grouping, titles + bodies, and Priority/Size.
7. Check duplicates (`gh issue list`), create (`gh issue create --body-file`), set project fields if a project exists.
8. Report created issues: numbers, titles, labels, milestone, field updates.

## Interrogation Checklist

Ask for anything missing from the brief. Batch related questions; keep the count minimal. **Never invent** file paths, modules, behavior, or technical details. If you don't know where the problem lives, offer to investigate the codebase (see `codemap.md`).

Per issue, you need:

- **Problem** — what happens, or what is missing (one line).
- **Location** — route/module/component/files. Unknown? Offer to search the code rather than guess paths.
- **Impact** — who suffers and how (users, developers, performance, reliability).
- **Solution intent (WHAT)** — the desired end result; the user's technical preference if they have one. Ask this as a decision, not as "how should this be implemented".
- **Expected** — the exact behavior when fixed.
- **Verification** (non-negotiable) — how to prove it works: specific test command, manual steps, or measurable threshold. At least one concrete check per issue.
- **Visual verification** (UI-affecting changes) — which pages/routes to inspect, which states (loading, empty, error, hover), which viewports (desktop/mobile). Default: desktop + mobile for every touched route.
- **Scope** — what is in, what is explicitly out.
- **Reproduction** — steps and environment, for bugs only.
- **Metadata** — type label, domain label(s), milestone (if any).
- **Priority and Size** — via repo project fields, never in the body.

Rules:
- If verification cannot be stated after asking, keep asking until it can. **An issue without verification is not creatable.**
- Never ask "how should it be implemented" — that is yours to figure out. Ask what result the user wants, propose options when there are real choices.

## Adaptive Depth

- Small (S) issues: confirm only problem, solution intent, and verification. Infer scope; confirm in one line.
- Medium/Large (M/L): run the full checklist.

## Drafting

- Title: imperative, specific, ≤ ~60 chars — "Fix <thing> in <place>".
- Body: sections in fixed order (template below), GitHub Flavored Markdown, human tone, English.
- Record the **solution intent** — the user's decision, with brief rationale if alternatives were compared. Do not write an implementation plan; the implementing agent derives HOW.
- Never put Priority or Size in the body — they live in project fields.
- Scope must bound the work: a fresh agent needs to know where to look and where to stop.

## Issue Body Template

```markdown
## Objective

<1-3 lines describing the goal>

## Context & Symptoms

- <current behavior or problem>
- <where it appears: route/module/component>
- <impact on users/developers>

## Expected Outcome

- <observable end state>
- <what "done" looks like>

## Solution Intent

- <the desired end result / chosen approach — decided by the user>
- <if alternatives existed: which was chosen and why, briefly>
- <or: "no preset approach — implementer decides the path to the expected outcome">

## Scope

- In: <files/modules touched, bounded>
- Out: <explicit non-goals>

## Acceptance Criteria & Verification

- [ ] <criterion — observable and measurable>
- [ ] <how to verify: exact command / test / manual step / performance threshold>

## Visual & Browser Verification

<!-- required for any UI-affecting change -->

- **Routes/pages:** <which pages to open, with what data/setup>
- **Viewports:** <desktop + mobile; add tablet/narrow widths if responsive behavior is at risk>
- **States to inspect:** <loading, empty, error, hover/focus, dark mode if applicable>
- **What to look for:** <layout/overflow, alignment, spacing, contrast, regressions vs. intended design>
- **Evidence:** capture screenshots (full page + mobile) and attach them to the PR/issue comment

## Reproduction

<!-- only for bugs -->

1. <step one>
2. <step two>

**Environment:** <branch, env, device>
```

## Grouping

- One cohesive problem per issue — not tiny, not umbrella.
- Group only tightly coupled items (same module, single delivery boundary).
- Split anything exceeding Size `L` (see repo conventions below).
- Ask for clarification before creating, not after.

## Verifiability Test (self-check before creating)

Answer for every draft:

1. Can a fresh agent with only this issue locate the code?
2. Is "done" observable from the Expected Outcome and criteria?
3. Is there at least one concrete verification step?
4. Is the solution intent recorded (what the user decided)?
5. Do the scope boundaries prevent wandering?

Any "no" → go back to interrogation before showing drafts. For UI changes, additionally: **is there at least one concrete visual check** (route + viewport + state)?

## Repo Conventions

Read `codemap.md` when locating code or judging scope. Read `AGENTS.md` for repo-level guidance.

### Labels

- Type (exactly one): `bug`, `enhancement`, `refactor`, `documentation`.
- Domain (one or more): `frontend`, `backend`, `performance`.
- Create any missing labels with `gh label create` before the first issue uses them.

### Size and Priority (project fields, not body)

- `Size`: `S` (≤ ~3 files, one flow/module, localized) · `M` (4-8 files, up to 2 related flows) · `L` (9-15 files, up to 3 related flows). Exceeds `L` → split into cohesive sub-issues.
- `Priority`: `Urgent & Important` · `Not Urgent & Important` · `Urgent & Not Important` · `Not Urgent & Not Important`.

### Verification commands (for acceptance criteria)

- Backend: `pytest -m 'not performance'` (tests in `backend/tests`).
- Frontend: `npm run check` (svelte-check) and `npm run build` (vite) in `frontend/`.
- Performance-sensitive changes: reference `PERFORMANCE_PROTOCOL.md` — k6 (`k6 run tests/performance/k6/smoke.js`), Lighthouse CI, Playwright, `pytest-benchmark`.
- **Visual/browser (UI changes):** use Playwright (repo has `playwright.config.ts` + `playwright/` tests) for browser inspection and screenshots; inspect the PR preview at `https://<pr-id>.dev.m3tacron.com` once the deployment bot reports it ready. Verify the route set in the issue's Visual & Browser Verification section at desktop + mobile widths, capture screenshots as evidence.

### Feature work (once an issue is picked up)

- PR targets base branch `dev`, body includes `Closes #<issue-id>`.
- Preview at `https://<pr-id>.dev.m3tacron.com` once the deployment bot reports it ready.

## Target Repository

Issues and labels live on the **upstream** repo (the project tracker), never on the fork. Default target: the upstream remote — `Francespo/m3tacron` — confirmed with the user before creating. The work-order labels (types + `frontend`/`backend`/`performance`) already exist upstream, and Priority/Size live in the M3tacron Project fields. Create with `gh issue create -R <owner/repo> --body-file`.
