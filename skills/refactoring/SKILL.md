---
name: refactoring
description: "Systematic code refactoring with smell detection, safe transformation patterns, and test-verified execution. Triggered by: refactor this, clean up this code, code smells, extract method, dead code, reduce complexity, this code is messy, too much coupling, simplify this. Analyzes code structure, produces a prioritized refactoring plan, and executes changes with test verification at every step."
context: fork
agent: refactoring-specialist
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(git status), Bash(git branch:*), Bash(npm:*), Bash(npx:*), Bash(pnpm:*), Bash(yarn:*), Bash(cargo:*), Bash(go:*), Bash(python:*), Bash(pytest:*), Bash(make:*), Bash(task:*), Grep, Glob, LS, Read, Write, Edit
tags: [review]
tier: core
---

# Refactoring

Systematically detect code smells, produce a prioritized refactoring plan, and execute changes with test verification at every step.

---

## Context

GIT STATUS:

```
!`git status 2>/dev/null || echo "(not a git repository — no local changes to show)"`
```

TEST SUITE BASELINE:

```
!`npm test 2>&1 | tail -5 || pnpm test 2>&1 | tail -5 || yarn test 2>&1 | tail -5 || pytest --tb=no -q 2>&1 | tail -5 || go test ./... 2>&1 | tail -5 || cargo test 2>&1 | tail -5 || echo "No test runner detected"`
```

RECENT CHANGES:

```
!`git diff --stat HEAD~5 2>/dev/null || echo "Not enough history"`
```

---

## Process

### Phase 1: Reconnaissance

- Identify the scope — use user-specified files/dirs, or derive from changed files in git
- Run language-appropriate detection tools (see `references/DETECTION_TOOLS.md`)
- Catalog all detected smells with `file:line` references
- Classify each finding by triage level: [Design Discussion], [Active Smell], [Quick Fix]
- Output: triaged findings list

### Phase 2: Refactoring Plan

- Map each smell to a primary refactoring technique (see `references/REFACTORING_TECHNIQUES.md`)
- Order by dependency — some refactorings enable others (e.g., extract method before move method)
- Estimate effort per item (S = under 30 min, M = under 2 hrs, L = multi-session)
- Identify risks: missing tests, shared interfaces, callers outside the current scope
- **Present plan to user. Wait for explicit approval before executing any changes.**

### Phase 3: Execution

For each approved refactoring item:

1. Confirm tests are green (baseline)
2. Apply the refactoring — minimal, atomic diff
3. Run tests again
4. If green: commit with a descriptive message (`refactor: extract validatePayload from processRequest`)
5. If red: revert immediately (`git checkout -- .` or `git stash`), report the failure, skip or re-approach

**One smell per commit.** Do not bundle multiple refactorings into one commit.

### Phase 4: Verification

- Run the full test suite end-to-end
- Compare before/after metrics where tooling is available: cyclomatic complexity, file/line counts
- Confirm git log shows atomic, clearly-labeled commits
- Generate summary report of what was changed and what was deferred
- Suggest running `/code-review` for post-refactoring validation

---

## Quick Reference

| Phase | Action | Gate |
|-------|--------|------|
| 1. Reconnaissance | Detect smells, classify by triage | — |
| 2. Plan | Map techniques, order, estimate effort | **Wait for explicit user approval** |
| 3. Execute | Apply + test + commit loop | One smell per commit |
| 4. Verify | Full test suite + metrics + summary | — |

---

## References

- `references/CODE_SMELLS.md` — Full code smell catalog with descriptions and indicators
- `references/REFACTORING_TECHNIQUES.md` — Technique catalog with before/after examples
- `references/DETECTION_TOOLS.md` — Language-specific detection tooling
