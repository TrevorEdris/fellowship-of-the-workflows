# Dispatch Prompts

Single source of truth for what each relay agent is told when spawned via the
`Task` tool. The agent definitions (`agents/researcher.md`, etc.) hold *behavior*;
these templates hold the *contract* — the concrete artifact paths, scope, and
round number for this run. Keep contracts here, not in the agent bodies, so the
two never drift.

Before dispatching, substitute the bracketed placeholders:

- `[SESSION_DIR]` — the session directory created in Phase 0
  (e.g. `~/src/.ai/sessions/2026-06-23_TICKET_Slug/`).
- `[TASK]` — the user's task as framed after the Question phase.
- `[FRAME]` — the numbered research-frame questions from the Question phase.
- `[BASE]` — the branch/ref the diff is measured against (e.g. `main`).
- `[PHASE]` — the plan phase identifier the implementer is assigned.
- `[N]` — the current loop round (critique or review), 1-indexed.

---

## Researcher

```
You are the researcher agent. Investigate this task and write a discovery document.

Task: [TASK]

Research frame — answer each, with path:line evidence:
[FRAME]

Scope: <files/dirs in or out of bounds, or "the whole repo at [SESSION_DIR]'s project">

Write your discovery document to: [SESSION_DIR]/DISCOVERY.md
Follow the discovery-document structure in your agent definition. The Unknowns &
Confidence section is mandatory. Do not modify any other file. Do not propose a
plan — report what is.
```

---

## Planner — draft

```
You are the planner agent. Mode: draft.

Read the discovery document at: [SESSION_DIR]/DISCOVERY.md
Task: [TASK]

Write the implementation plan to: [SESSION_DIR]/PLAN.md
Follow the plan-document structure in your agent definition. Every behavioral
step is test-first (RED-GREEN). Include the Considered & Rejected, Traceability,
and Git Strategy sections. Verify every file claim by reading the actual file.
Write only the plan document.
```

## Planner — revision

```
You are the planner agent. Mode: revision. This is revision round [N].

Read, in order:
- The critique: [SESSION_DIR]/CRITIQUE.md
- Your prior plan: [SESSION_DIR]/PLAN.md

Respond to every critique finding — accepted (with the change) or rejected (with a
code-grounded reason). Silence on a finding is not allowed. Rewrite the plan in
place at [SESSION_DIR]/PLAN.md, keep Considered & Rejected current, and end with a
short changelog of what moved this round. Write only the plan document.
```

---

## Critic

```
You are the critic agent. This is critique round [N].

Read:
- The plan under review: [SESSION_DIR]/PLAN.md
- The discovery base it rests on: [SESSION_DIR]/DISCOVERY.md

Attack the plan's substance per the axes in your agent definition. Verify the
three riskiest steps against the actual code. Write your critique to:
[SESSION_DIR]/CRITIQUE.md

Return APPROVE or REVISE in the Verdict. Findings only — do not edit the plan or
any code. Do not manufacture findings; if the plan is sound, say so and APPROVE.
```

---

## Implementer

```
You are the implementer agent. Execute exactly phase [PHASE] of the approved plan.

Read the plan at: [SESSION_DIR]/PLAN.md
Execute only the steps in phase [PHASE]. Touch only the files those steps name.

Follow the iron law (test-first), the false-green check, and the three-fix limit
from your agent definition. Append your completion report to:
[SESSION_DIR]/SESSION.md

Confirm the branch is not main/master before your first edit. Report actual test
output, not "tests pass". Surface any out-of-scope change as a deviation rather
than making it.
```

---

## Reviewers (pragmatic-code-review and security-review)

Dispatched in parallel after each implementation phase. Pin both to the diff so
they do not drift into unrelated code.

```
Review ONLY the changes in this diff against [BASE]. Do not review unrelated code.

Changed files:
<output of: git diff --name-only [BASE]...HEAD>

Diff:
<output of: git diff [BASE]...HEAD>   (or instruct the agent to run it itself, pinned to these files)

Report findings with severity (CRITICAL/HIGH/MEDIUM/LOW), file:line, and a
concrete fix. Findings only — do not modify code.
```

On re-review after fixes (round [N]), narrow the diff to only the files the
implementer changed in the fix pass, so reviewers re-check the fix, not the world.
