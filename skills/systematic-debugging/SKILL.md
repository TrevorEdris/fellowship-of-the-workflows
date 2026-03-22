---
name: systematic-debugging
description: "Structured root-cause analysis for bugs, test failures, and unexpected behavior. Four-phase methodology: investigate, analyze patterns, hypothesize, implement fix. Use when encountering any technical issue before proposing fixes. Prevents brute-force retry loops."
context: fork
agent: systematic-debugger
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(git status), Bash(npm:*), Bash(npx:*), Bash(pnpm:*), Bash(yarn:*), Bash(cargo:*), Bash(go:*), Bash(python:*), Bash(pytest:*), Bash(make:*), Bash(task:*), Grep, Glob, Read, Write, Edit
tags: [testing]
tier: core
---

# Systematic Debugging

Investigate and resolve technical issues through structured root-cause analysis, not guess-and-check.

---

## Quick Start

State the issue concisely:

```
debug: tests fail with "connection refused" after upgrading the database driver
```

```
debug: API returns 500 only when user has no profile photo set
```

```
debug: build succeeds locally but fails in CI with exit code 137
```

**What to include:**
- The exact error message or unexpected behavior
- When it started (after a deploy, after a change, always been broken)
- Where it occurs (local only, CI only, production, specific inputs)
- What you have already tried (so we do not repeat it)

---

## Triggers

| Trigger | Example |
|---------|---------|
| `debug` | "debug: auth token validation fails intermittently" |
| `investigate` | "investigate why this test is flaky" |
| `why is` | "why is this endpoint returning 403 for admin users?" |
| `figure out` | "figure out why the build is failing" |
| `root cause` | "root cause analysis for the memory leak" |
| `what's wrong` | "what's wrong with this query?" |
| Multiple failed fixes | After 2+ attempted fixes that did not resolve the issue |

---

## Key Terms

| Term | Definition |
|------|------------|
| **Root cause** | The original condition that makes the bug structurally possible |
| **Symptom** | The observable effect (error message, wrong output, crash) |
| **Immediate cause** | The proximate failure point — often not the root cause |
| **Hypothesis** | A single, specific, testable explanation for the bug |
| **Reproduction** | Consistently triggering the bug with exact steps |
| **Evidence** | Observed facts that support or refute a hypothesis |
| **Defense in depth** | Validation at multiple layers so bugs cannot hide |

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| Error message | Read it completely, including stack trace |
| Can't reproduce | Find the distinguishing condition before doing anything else |
| "Obvious" fix | Still run Phase 1 — obvious fixes that skip investigation often miss the real cause |
| 3+ failed fixes | STOP. Escalate to human. Architectural problem likely. |
| Unclear error | Add instrumentation at component boundaries before hypothesizing |
| Multiple plausible causes | Pick ONE. Test it. Then the next. |
| Time pressure | Systematic debugging is faster than brute-force past 2 attempts |

---

## Context

Current repo state:

```
!`git status`
```

Recent changes that may be relevant:

```
!`git diff --stat HEAD~3`
```

Recent commits for context:

```
!`git log --oneline -10`
```

---

## The Iron Law

**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

Proposing a fix before understanding the root cause is not faster — it is guessing. Guessing creates compound failures: the original bug plus the side effects of the wrong fix. Every additional wrong fix makes the next investigation harder.

---

## Process Overview

```
Bug / Test Failure / Unexpected Behavior
    |
    v
+-----------------------------------------------------+
| Phase 1: ROOT CAUSE INVESTIGATION                   |
| * Read the full error message and stack trace       |
| * Reproduce consistently with exact steps           |
| * Check recent changes (git diff, deps, config)     |
| * Gather evidence at component boundaries           |
| * Trace data flow upstream until source found       |
+-----------------------------------------------------+
    |
    v
+-----------------------------------------------------+
| Phase 2: PATTERN ANALYSIS                           |
| * Find working implementations of similar code      |
| * Compare working vs broken completely              |
| * Identify every difference                         |
| * Map the dependency chain                          |
+-----------------------------------------------------+
    |
    v
+-----------------------------------------------------+
| Phase 3: HYPOTHESIS AND TESTING                     |
| * Form ONE specific hypothesis: X causes Y because Z|
| * Test with SMALLEST possible change (one variable) |
| * Verify result before continuing                   |
| * Hypothesis fails? Form NEW one, do not stack fixes|
| * Stuck? State what you do not know. Do not guess.  |
+-----------------------------------------------------+
    |
    v
+-----------------------------------------------------+
| Phase 4: IMPLEMENTATION                             |
| * Create failing test case first                    |
| * Implement single fix addressing root cause        |
| * Verify: test passes, no regressions               |
| * Fix count >= 3 without resolution? STOP. Escalate.|
+-----------------------------------------------------+
    |
    v
Verified Fix + Confirmation Evidence
```

---

## Commands

| Command | When to Use | Action |
|---------|-------------|--------|
| `debug: <description>` | Starting investigation | Launch full four-phase process |
| `reproduce: <steps>` | Before hypothesizing | Establish consistent reproduction |
| `trace: <value>` | Unclear data source | Trace value upstream to origin |
| `compare: <working> vs <broken>` | After Phase 1 | Pattern analysis against reference |
| `hypothesize: <specific claim>` | After pattern analysis | Form and test single hypothesis |
| `escalate` | After 3 failed fixes | Request human review |

---

## Core Principles

| Principle | Why | Implementation |
|-----------|-----|----------------|
| Root cause first | Symptoms mislead | Complete Phase 1 before any hypothesis |
| One hypothesis at a time | Ambiguous results | Cannot isolate cause with multiple changes |
| One variable at a time | Reproducible conclusions | Change one thing, observe, conclude |
| Evidence over intuition | Intuition has blind spots | State only what evidence confirms |
| Reproducibility before investigation | Intermittent bugs cannot be traced | Find the distinguishing condition first |
| Fix at source, not at symptom | Symptoms recur | Address the originating condition |

---

## Three-Fix Escalation Rule

If you have attempted 3 fixes and the issue persists, stop attempting fixes.

This is the signal that the problem is architectural, not a simple code bug. Continuing adds complexity, masks the real issue, and consumes time without resolution.

**When to escalate:**
- 3 fixes attempted without resolution
- Each fix reveals new unexpected coupling
- The required change scope keeps expanding
- New symptoms appear in different components after each fix

**How to escalate:**
Tell the user what you know, what you tried, what each attempt revealed, and why you believe this requires architectural discussion. This is not failure — it is accurate diagnosis.

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Proposing a fix before stating root cause | Guessing, not engineering | Complete Phase 1 first |
| Multiple fixes at once | Can't isolate what worked | One change, verify, then next |
| Retrying same approach with minor variations | Definition of brute-force | Form a new hypothesis |
| "This should fix it" without evidence | Conveying hope, not knowledge | State evidence or admit uncertainty |
| Skimming reference implementations | Partial understanding misses differences | Read completely |
| "Quick fix for now" | Quick fixes become permanent | No such thing as temporary wrong code |
| 4th fix attempt without escalating | Compounding guesses | Stop at 3, escalate |

---

## Red Flags

These thoughts mean "STOP, return to Phase 1":

- "Quick fix for now"
- "Just try changing X"
- "I don't fully understand but this might work"
- "One more fix attempt"
- "The fix is obvious"
- Proposing solutions before tracing data flow
- Using "probably" or "should" without evidence

---

## Verification Checklist

After identifying the root cause and implementing a fix:

- [ ] Root cause stated in one specific sentence
- [ ] Evidence gathered confirming root cause (not just consistent with it)
- [ ] Failing test case created before fix
- [ ] Single minimal fix applied addressing root cause only
- [ ] Fix verified by running the failing test/command
- [ ] No regressions introduced (existing tests still pass)
- [ ] Reproduction steps documented

---

<details>
<summary><strong>Deep Dive: Root Cause Tracing</strong></summary>

See `references/root-cause-tracing.md` for the complete five-step tracing process, instrumentation patterns, and a worked example through a multi-layer system.

### The Core Process

1. Observe the symptom (the error or wrong output)
2. Find the immediate cause (the code that produced it)
3. Ask "what called this function / set this value?"
4. Trace upstream through the call stack or data flow
5. Find the original trigger — the condition that made the bug structurally possible

**Key insight:** The immediate cause is usually not the root cause. Fixing the immediate cause (the symptom layer) means the bug returns through a different code path.

### Quick Tracing Pattern

```
Symptom: NullPointerException in PaymentProcessor.charge()
    |
    → charge() receives null amount
    → amount comes from Order.getTotal()
    → getTotal() returns null when no items in cart
    → Cart allows checkout with empty cart (root cause)

Fix at: Cart.checkout() — validate non-empty before proceeding
Not at: PaymentProcessor — null check here would hide the real bug
```

</details>

<details>
<summary><strong>Deep Dive: Defense in Depth</strong></summary>

See `references/defense-in-depth.md` for the complete four-layer validation pattern and application process.

### Why Single-Layer Validation Fails

A bug fixed at one layer can resurface through:
- Different code paths (refactoring, new features)
- Test mocks that bypass the fixed layer
- Direct database access that skips business logic
- Edge cases not covered by the original fix

### Four Validation Layers

| Layer | Purpose | Example |
|-------|---------|---------|
| Entry point | Block invalid inputs before processing | API request validation |
| Business logic | Enforce domain rules | Service-layer invariant checks |
| Environment guards | Detect unexpected state | Assertion on assumed pre-conditions |
| Debug instrumentation | Structured logging at boundaries | Log input + output at each layer |

**Goal:** Make the bug structurally impossible, not just fixed for the known path.

</details>

<details>
<summary><strong>Deep Dive: Common Rationalizations</strong></summary>

See `references/anti-patterns.md` for the full rationalization table with rebuttals and the partner-facing signals that investigation is off track.

### Why Systematic Debugging is Faster

The common objection: "I don't have time for a structured process."

The math:
- Brute-force attempt 1: 15 min (doesn't work, new symptom appears)
- Brute-force attempt 2: 20 min (partially works, breaks something else)
- Brute-force attempt 3: 25 min (still broken, now harder to understand)
- Total: 60+ min, system in worse state

Versus:
- Phase 1 investigation: 10 min (root cause identified)
- Phase 3 hypothesis: 5 min (single targeted fix)
- Phase 4 verification: 5 min (confirmed working)
- Total: 20 min, system in better state

Systematic debugging is the fast path past the second failed attempt.

</details>

<details>
<summary><strong>Deep Dive: Debugging Log</strong></summary>

See `references/debugging-log-template.md` for the structured investigation template.

Use the debugging log for any investigation lasting more than 30 minutes or involving more than one hypothesis. It prevents:
- Retrying approaches you already ruled out
- Losing track of what evidence you have gathered
- Forgetting which hypothesis you are currently testing

The log is the single source of truth for the investigation state.

</details>

---

## References

- `references/root-cause-tracing.md` — Five-step tracing process and instrumentation patterns
- `references/defense-in-depth.md` — Multi-layer validation strategy
- `references/anti-patterns.md` — Rationalization table and red flags
- `references/debugging-log-template.md` — Structured investigation notes template
