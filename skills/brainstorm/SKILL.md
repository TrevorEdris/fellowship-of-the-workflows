---
name: brainstorm
description: "Structured design thinking for technical decisions. Captures constraints, surfaces assumptions, generates alternatives, analyzes trade-offs, and records decisions. Triggered by: brainstorm, design, explore options, what approach, how should we, which way."
user-invocable: true
argument-hint: "[design problem or question]"
allowed-tools: Read, Grep, Glob, LS, WebSearch, WebFetch
model: sonnet
tags: [meta, architecture]
---

# Brainstorm

Structured design exploration for technical decisions. Use before committing to an approach.

---

## When to Use

- "How should we design X?"
- "What's the best approach for Y?"
- "Brainstorm options for Z"
- "Help me think through this architecture decision"
- Before starting the Research phase in QRSPI — to clarify the question space

---

## Process

### Step 1: Capture the Problem

Restate the problem in one sentence. Confirm with the user before continuing.

> "We need to [accomplish X] given [constraint Y], without [Z]."

If the problem statement is unclear, ask:
- What does success look like in concrete, observable terms?
- What is the primary constraint? (time, cost, compatibility, reversibility)
- What is explicitly NOT in scope?

### Step 2: Surface Assumptions

List the assumptions embedded in the problem as stated. For each:
- State the assumption
- Assess its risk: HIGH (wrong assumption = wrong solution), MEDIUM, LOW
- Note how to verify it

Use `references/design-prompts.md` → "Assumption Surfacing" templates.

### Step 3: Generate Alternatives

Produce at least 3 meaningfully different approaches. Aim for divergence, not convergence:
- The obvious approach
- The simplest approach (fewest moving parts)
- The most flexible approach (easiest to change later)
- Any unconventional approaches worth considering

For each alternative, briefly describe:
- What it is
- What it's optimized for
- Its main weakness

Do NOT evaluate yet — generate first, evaluate second.

### Step 4: Trade-off Analysis

Compare alternatives on the dimensions that matter most for this problem. Typical dimensions:

| Dimension | Why It Matters |
|-----------|---------------|
| Complexity | How hard is it to build and operate? |
| Reversibility | How easy is it to change the decision later? |
| Performance | Does it meet throughput/latency needs? |
| Consistency | Is behavior predictable under failure? |
| Time to ship | How long until users benefit? |
| Test surface | Is it easy to verify correctness? |

Use the trade-off matrix in `references/design-prompts.md` to structure the comparison.

### Step 5: Record the Decision

Produce a lightweight Architecture Decision Record (ADR):

```markdown
## Decision: [short title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded

### Context
[What problem are we solving and why does it matter now?]

### Options Considered
1. [Option A] — [one-line summary]
2. [Option B] — [one-line summary]
3. [Option C] — [one-line summary]

### Decision
[Which option and why — reference the trade-off analysis]

### Consequences
**Good:** [what gets better]
**Bad:** [what gets harder or more expensive]
**Neutral:** [what changes but doesn't clearly improve or worsen]
```

Save the ADR to the session directory: `.ai/sessions/<session>/decisions/<TITLE>.md`

---

## Output

After completing the process, produce:

1. **Problem statement** — confirmed with user
2. **Assumption register** — HIGH-risk assumptions called out
3. **Alternatives table** — at least 3 options with trade-offs
4. **Recommendation** — which option and why, stated directly
5. **ADR** — saved to session directory

---

## References

- `references/design-prompts.md` — facilitation templates for each step
