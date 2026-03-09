---
name: plan-validator
description: "Validate implementation plans for completeness, specificity, and actionability. Catches vague language, missing sections, and untestable outcomes."
user-invocable: true
argument-hint: "[path-to-plan.md]"
allowed-tools: Bash, Read, Glob
model: sonnet
---

# Plan Validator

Validates PLAN.md files for structural completeness, specificity, and actionability before the approval gate.

---

## When to Use

- After drafting a PLAN.md during the Plan phase
- Before presenting a plan for user approval
- To review an existing plan's quality

---

## Usage

```
/plan-validator                    # Validates PLAN.md in current session dir
/plan-validator path/to/PLAN.md    # Validates a specific file
```

---

## Process

### Step 1: Locate the Plan

If no path argument is provided:
1. Check the current session directory for `PLAN.md`
2. If not found, ask the user for the path

### Step 2: Run Validation

Run from the skill directory (`workflows/skills/plan-validator/`):

```bash
python scripts/validate_plan.py <path> --verbose
```

### Step 3: Report Results

Present the validation output to the user:
- Score (0-100) and verdict (PASS >= 70, NEEDS WORK < 70)
- Errors (blocking issues)
- Warnings (quality concerns)

### Step 4: Fix and Re-validate

If the plan scores NEEDS WORK:
- Address each error finding
- Re-run validation to confirm the fix
- Present the updated score

---

## Checks Performed

| # | Check | What It Validates |
|---|-------|-------------------|
| 1 | Target repos | At least one repo or directory listed |
| 2 | Files to modify | Explicit file paths, not vague areas |
| 3 | Ordered steps | Numbered or sequenced implementation steps |
| 4 | Steps reference files | Each step mentions at least one file path |
| 5 | Risks section | Non-empty risks or assumptions section |
| 6 | Verification section | How to confirm correctness is described |
| 7 | Vague language | Flags: "should work", "might need", "probably", "as needed", "etc." |
| 8 | Oversized code blocks | Code blocks >15 lines (plans describe, not implement) |
| 9 | Scope boundary | Explicit exclusions or out-of-scope stated |
| 10 | Traceability table | Discovery findings mapped to plan steps |
| 11 | Testable outcomes | At least one step references tests, builds, or verification |

---

## Resources

### scripts/

| Script | Purpose |
|--------|---------|
| `validate_plan.py <file> [--verbose] [--json]` | Run all validation checks on a PLAN.md |
