---
name: make-no-mistakes
description: "Maximum-rigor development relay. Runs the Discover → Plan → Implement workflow through dedicated agents — researcher, planner, critic, implementer, and code reviewers — with explicit gates between each. Use when ultracode effort is active, or when the user asks for the most thorough, carefully-verified delivery of a non-trivial change. Claude Code only."
user-invocable: true
argument-hint: "[task description]"
allowed-tools: Glob, Grep, Read, Write, Edit, Task, AskUserQuestion, Bash(git diff:*), Bash(git log:*), Bash(git status), Bash(git branch:*)
tags: [meta]
---

# Make No Mistakes

A repeatable, high-rigor development relay: gather context, plan, critique the
plan, build, review, fix, and prepare to ship — each stage handled by a dedicated
agent, with a gate between stages so nothing advances on a weak foundation.

> **Claude Code only.** This skill orchestrates subagents through the `Task` tool.
> Tools without subagent support (Cursor, Copilot, etc.) cannot run it. Do not
> install it for other targets.

## Relationship to other workflows

- This skill is the **ultracode execution** of the `discover-plan-implement` rule.
  That rule defines the Question → Research → Structure → Plan → Implement phases
  and their gates; this skill runs them with one agent per phase instead of inline.
- It differs from the `orchestrate` skill: `orchestrate` decomposes an arbitrary
  task across whatever specialists fit. This skill runs one **opinionated, fixed
  development pipeline** with a built-in adversarial critique and a test-first
  build stage.

## When to use

- The configured effort is **ultracode**, or the user explicitly wants maximum
  rigor on a non-trivial change.
- The change is worth the cost of multiple agents and human gates: new features,
  cross-cutting refactors, anything where a wrong plan is expensive.

Do **not** use it for a one-line fix or a question — that is pure overhead. Run
the change directly.

## The relay

Each agent's behavior lives in its `agents/*.md` definition. The exact prompt to
dispatch each one — with this run's artifact paths and round numbers — lives in
[references/dispatch-prompts.md](references/dispatch-prompts.md). You are the
orchestrator: you spawn agents via `Task`, hold the gates, and never skip a phase
silently.

### Phase 0 — Session setup

Create the session directory per the `ai-session` convention:
`~/src/.ai/sessions/YYYY-MM-DD_<TICKET>_<TITLE_SLUG>/`. Create `SESSION.md` with
the schema-v1 frontmatter. Every artifact below lives in this directory.

### Phase 1 — Question (inline, gated)

Work only from the user's description — do not read code yet. Surface the design
decisions that will shape the solution and the scope boundaries.

- For decisions with a small set of discrete options, use `AskUserQuestion`.
- For genuinely open design questions, ask in prose — do not force an open
  question into fixed multiple-choice.
- Record confirmed answers and the resulting **research frame** (the numbered
  questions Research must answer) in `SESSION.md`.

**Gate:** do not proceed until the design questions are answered or scoped out.

### Phase 2 — Research

Dispatch the **researcher** (Researcher prompt). It writes `DISCOVERY.md`. When it
returns, read the Unknowns & Confidence section — if a load-bearing question came
back unanswered, decide whether to re-dispatch with a tighter frame or surface the
gap to the user before planning on sand.

### Phase 3 — Plan

Dispatch the **planner** in draft mode (Planner — draft prompt). It writes
`PLAN.md`.

Then validate structure mechanically: run `/plan-validator [SESSION_DIR]/PLAN.md`.
If it scores below PASS, re-dispatch the planner in revision mode with the
validator output until it passes. This cheap check runs **before** the expensive
critic.

### Phase 4 — Critique (capped loop)

This is the adversarial gate the validator cannot provide.

1. Append `critique_round: [N]` to `SESSION.md` (start at 1) and re-read it so the
   cap is auditable, not just remembered.
2. Dispatch the **critic** (Critic prompt). It writes `CRITIQUE.md` with an
   APPROVE/REVISE verdict.
3. If **APPROVE** → go to the approval gate.
4. If **REVISE** → dispatch the planner in revision mode against `CRITIQUE.md`,
   increment the round, and loop.
5. **Cap: 2 critique rounds.** If the critic still returns REVISE after round 2,
   stop looping. Surface the unresolved findings to the user verbatim and let them
   decide — do not spin a third round or quietly accept the plan.

### Phase 5 — Approval gate (human)

Present the plan and the final critique verdict. **Wait for explicit user
approval.** Do not write production code before it. This gate is the whole point —
the relay exists to make the plan trustworthy enough to approve.

### Phase 6 — Implement (per phase)

Confirm the branch is not `main`/`master`; if it is, stop and ask. Then, for each
phase in the approved plan, **spawn a fresh implementer** (Implementer prompt)
scoped to that phase only. A fresh instance per phase avoids context exhaustion
and drift across a long plan.

After each implementer returns, read its completion report from `SESSION.md`. If
it reports a three-fix-limit block, do not dispatch the next phase — resolve the
blocker (often a plan gap) or surface it to the user. Record a one-line
after-action per phase in `SESSION.md`.

### Phase 7 — Review and fix (capped loop)

After implementation:

1. Append `review_round: [N]` to `SESSION.md` (start at 1) and re-read it.
2. Dispatch **`pragmatic-code-review`** and **`security-review`** in parallel
   (Reviewers prompt), both pinned to `git diff --name-only [BASE]...HEAD`. Pinning
   keeps them on this change, not unrelated worktree code.
3. Merge their findings: collapse duplicates (same file + line + root cause → keep
   the highest severity), then sort by severity.
4. Dispatch an **implementer** to fix CRITICAL and HIGH findings (MEDIUM/LOW are
   reported, not auto-fixed). Re-review **only the files the fix touched**,
   increment the round, and loop.
5. **Cap: 2 review rounds.** If CRITICAL/HIGH findings remain after round 2,
   surface them to the user rather than looping further.

### Phase 8 — Ship

Run the full test/lint/build suite once more as a final confirmation, independent
of per-step checks. Then suggest committing and opening a PR via `/git-workflow`,
which handles conventional commits, the PR template, and branch safety. Do not
push to `main`/`master` without explicit user approval.

## Artifact contract

All artifacts live in the session directory. Producers and consumers:

| Artifact | Written by | Read by |
|----------|------------|---------|
| `SESSION.md` | orchestrator + implementer | all phases (round counters, after-actions) |
| `DISCOVERY.md` | researcher | planner, critic |
| `PLAN.md` | planner | critic, implementer, you (approval) |
| `CRITIQUE.md` | critic | planner (revision), you (approval) |

The exact read/write paths and scope each agent is given are defined once, in
[references/dispatch-prompts.md](references/dispatch-prompts.md). If you change an
artifact's name or an agent's contract, change it there — not in the agent bodies.

## Failure handling

- **Agent fails or returns nothing:** retry once with the failure reason added to
  its prompt. If it fails again, stop and surface to the user with full context.
  Never silently skip a phase.
- **Named agent unavailable** (skill installed without the relay agents): run that
  phase inline in the main conversation, following the same agent definition's
  rules, and tell the user you did so. Degrade, do not halt.
- **Loop caps** are enforced by the round counters in `SESSION.md`: read the
  counter before each round and stop at the cap. The caps are advisory but
  auditable — if you ever exceed one, say so explicitly.

## Hard rules

- Never write production code before the Phase 5 approval gate.
- Never skip a phase without telling the user.
- Every review dispatch is pinned to the diff.
- Honor the loop caps; surface unresolved findings rather than looping past them.
- The orchestrator (you) holds every human gate — subagents cannot ask the user,
  so they cannot be trusted to gate.
