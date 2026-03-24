# plan-validator

Validates PLAN.md files for completeness, specificity, and actionability before the approval gate.

## Usage

```
/plan-validator                     # Validates PLAN.md in current session dir
/plan-validator path/to/PLAN.md     # Validates a specific file
```

## When to Use

- After drafting a PLAN.md during the Plan phase
- Before presenting a plan to the user for approval
- Reviewing an existing plan's quality before implementation

## What It Does

- Runs 16 checks: target repos, file paths, ordered steps, risks, verification, vague language, git strategy, traceability
- Produces a score (0-100) with PASS (>= 70) or NEEDS WORK verdict
- Flags vague language, oversized code blocks, and missing per-step verification
