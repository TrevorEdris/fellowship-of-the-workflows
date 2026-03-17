# Discovery Prompts

Reference templates for each phase of the QRSPI workflow. Use the section that matches your current phase.

---

## Phase 1: Questioning Templates

Use these before any code reading. Work from the user's description only.

**Approach framing:**
- "What approaches exist for [X]? Here are the main options: (1)... (2)... (3)..."
- "There are two ways to solve [Y]: [option A] trades [quality] for [quality]; [option B] does the reverse. Which fits the constraint?"
- "Before I start reading code, I need to know: is [assumption] correct, or should I treat it as a research question?"

**Scope framing:**
- "To confirm scope: [feature] means X but NOT Y. Is that right?"
- "Should [edge case] be handled in this change, or is it out of scope?"
- "What's the non-goal here — what should this explicitly NOT do?"

**Constraint surfacing:**
- "Are there any API contracts, DB schemas, or external integrations that cannot change?"
- "What org policies apply? (branch protection, TDD, deployment sequence)"
- "Has this been attempted before? What did you learn?"

---

## Phase 2: Research Templates

Work through these after phase 1 questions are answered. Each question should map to a specific file read.

### Problem Space

- What symptom or request triggered this work?
- What is the business impact if nothing changes?
- Who or what is affected? (users, services, data pipelines)

### Current State

- What code paths are involved? (entry points, controllers, services, data layer)
- What tests cover this area? What is untested?
- What is the data model? (tables, columns, relationships)
- What cross-repo or cross-service dependencies exist?

### Constraints

- What cannot change? (API contracts, DB schema, external integrations)
- What org policies apply? (no FKs, TDD, branch protection, deployment sequence)
- What has been tried before? (prior PRs, reverted changes, known dead ends)

### Target State

- What does "done" look like in concrete terms?
- What behavior should change? What must NOT change?
- What are the edge cases and failure modes?

---

## Phase 3: Structure Templates

Use these to decompose work into ordered phases before writing implementation steps.

**Phase identification:**
- "What is the smallest deliverable that unblocks everything else?" → This is P1.
- "What can run in parallel once P1 lands?" → These become P2a, P2b.
- "What requires both P2a and P2b before it can start?" → This is P3.

**Dependency graph format:**
```
P1: [capability] ──► P2: [capability] ──► P3: [capability]
                  └─► P2b: [capability]
```

**Risk register format:**
| Phase | Risk | Likelihood | Impact | Mitigation |
|-------|------|-----------|--------|-----------|
| P1 | [risk] | H/M/L | H/M/L | [action] |

---

## Phase 5: After-Action Review Prompts

Run at each phase boundary before continuing to the next phase.

1. **What succeeded as planned?** List steps that executed as written.
2. **What deviated and why?** List unexpected findings, scope creep, or failed assumptions.
3. **What carries forward?** List open items, adjusted assumptions, or risks to watch in the next phase.

Record answers in `SESSION.md` under a heading like `## After Phase 1 — [date]`.
