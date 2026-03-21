---
name: prd-validator
description: >
  Validates PRD.md files for structural completeness, specificity, and actionability
  before handoff to engineering. Use this skill whenever a PRD exists and needs quality
  review, before handing requirements to engineers, when the user asks "is this PRD
  ready" or "validate my requirements", or automatically after /prd-author completes.
  Checks for required sections, acceptance criteria, scope boundaries, vague language,
  and requirement ID consistency. Supports --draft mode for work-in-progress PRDs.
user-invocable: true
argument-hint: "[path/to/PRD.md] [--draft]"
allowed-tools: Read, Grep, Glob
model: sonnet
tags: [documentation, meta]
---

# PRD Validator

Validates PRD files for structural completeness, specificity, and actionability before the handoff gate.

---

## When to Use

- After drafting a PRD during the authoring phase
- Before handing off a PRD to engineering
- To review an existing PRD's quality
- Automatically invoked by `/prd-author` after creation or iteration

---

## Usage

```
/prd-validator                       # Validates PRD.md in current directory
/prd-validator path/to/PRD.md        # Validates a specific file
/prd-validator path/to/PRD.md --draft  # Relaxed threshold for work-in-progress
```

---

## Process

### Step 1: Locate the PRD

If no path argument is provided:
1. Check the current directory for `PRD.md`
2. If not found, ask the user for the path

### Step 2: Run Validation

Run from the skill directory (`skills/prd-validator/`):

```bash
python scripts/validate_prd.py <path> --verbose
```

For draft/work-in-progress PRDs:

```bash
python scripts/validate_prd.py <path> --verbose --draft
```

### Step 3: Report Results

Present the validation output to the user:
- Score (0-100) and verdict (PASS >= 70, or >= 50 in draft mode)
- Errors (blocking issues)
- Warnings (quality concerns)

### Step 4: Fix and Re-validate

If the PRD scores NEEDS WORK:
- Address each error finding
- Re-run validation to confirm the fix
- Present the updated score

---

## Checks Performed

| # | Check | What It Validates |
|---|-------|-------------------|
| 1 | Problem statement | Section exists and is substantive (not just a heading) |
| 2 | User personas | Section exists with at least one persona defined |
| 3 | Persona detail | Each persona mentions goals and pain points |
| 4 | Functional requirements | Section exists with requirement descriptions |
| 5 | Requirement IDs | Requirements use consistent IDs (FR-001 format) |
| 6 | Acceptance criteria | Requirements describe what "done" looks like |
| 7 | Non-functional requirements | NFRs documented (performance, security, scalability) |
| 8 | Scope boundary | Both in-scope and out-of-scope explicitly stated |
| 9 | Dependencies | External dependencies documented |
| 10 | Milestones | Phased delivery plan exists |
| 11 | Milestone deliverables | Each milestone states what users can do when it ships |
| 12 | Vague language | Flags: "TBD" without owner, "should work", "probably", "as needed", "etc." |
| 13 | Oversized code blocks | Code blocks >15 lines (PRDs describe, not implement) |
| 14 | Success metrics | Measurable outcomes defined |
| 15 | Open questions | Unresolved items documented (or explicitly empty) |
| 16 | ID consistency | Requirement IDs follow a single consistent format |

---

## Resources

### scripts/

| Script | Purpose |
|--------|---------|
| `validate_prd.py <file> [--verbose] [--json] [--draft]` | Run all validation checks on a PRD |
