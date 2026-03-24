# prd-validator

Validates PRD.md files for structural completeness, specificity, and actionability.

## Usage

```
/prd-validator                      # Validates PRD.md in current directory
/prd-validator path/to/PRD.md       # Validates a specific file
/prd-validator PRD.md --draft       # Relaxed threshold for WIP PRDs
```

## When to Use

- Before handing a PRD off to engineering
- After `/prd-author` completes (runs automatically)
- Checking if a PRD is ready for roadmap translation
- Reviewing a PRD you received from a stakeholder

## What It Does

- Runs 17 structural checks: required sections, acceptance criteria, scope boundaries, vague language, requirement ID consistency, implementation leakage
- Produces a score (0-100) with PASS (>= 70) or NEEDS WORK verdict
- Supports `--draft` mode with relaxed threshold (>= 50) for incomplete PRDs
