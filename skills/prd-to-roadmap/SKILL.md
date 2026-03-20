---
name: prd-to-roadmap
description: >
  Translates an approved PRD into a unified ROADMAP.md with phased feature
  descriptions and implementation checklists. Engineer-facing skill that bridges
  Product requirements to engineering execution. Gates on PRD validation — refuses
  to proceed if the PRD hasn't passed /prd-validator.
user-invocable: true
argument-hint: "[path/to/PRD.md]"
allowed-tools: Read, Grep, Glob, Write
model: sonnet
tags: [documentation, architecture]
---

# PRD to Roadmap

Translate an approved PRD into a phased ROADMAP.md.

---

## When to Use

- After receiving an approved PRD from Product
- When starting a new project and need to decompose requirements into phases
- When transitioning from "what to build" to "how to build it"

---

## Usage

```
/prd-to-roadmap PRD.md              # Translate specific PRD
/prd-to-roadmap                     # Translate PRD.md in current directory
```

---

## Process

### Step 1: Validate the PRD

Before translation, verify the PRD has passed validation:

```bash
python skills/prd-validator/scripts/validate_prd.py <path> --verbose
```

If the PRD scores NEEDS WORK, stop and inform the user. The PRD must pass validation (score >= 70) before translation. This gate ensures the roadmap is built from a complete, well-structured PRD.

### Step 2: Read and Analyze the PRD

Extract:
- All functional requirements (FR-NNN) with priorities and acceptance criteria
- All non-functional requirements (NFR-NNN)
- Milestone/phase structure if the PRD defines one
- Dependencies between requirements
- Cross-cutting constraints

### Step 3: Decompose into Phases

Group requirements into phases following these principles:

1. **Priority first:** Must-have requirements land in earlier phases
2. **Dependencies respected:** If FR-003 depends on FR-001, FR-001's phase is earlier
3. **User-visible milestones:** Each phase delivers something a user can try
4. **Vertical slices:** Avoid phases that are purely "backend" or "infrastructure" with nothing visible

Assign feature IDs: P0-A, P0-B, P1-A, etc.

### Step 4: Generate Feature Details

For each feature, produce:
- **What:** Translate the PRD requirement description into plain language
- **Depends on:** Map requirement dependencies to feature IDs
- **Risk:** Surface risks from the PRD or identify new ones from decomposition
- **Note:** Add implementation context (optional)
- **Checklist:** Break down into 5-10 implementation sub-tasks with verification actions

### Step 5: Write the ROADMAP.md

Following `references/roadmap-template.md`, produce:
- Current Status section
- Philosophy statement (ask the engineer or infer from project context)
- Per-phase sections with entry/exit criteria, features, and deliverable statements
- Cross-cutting concerns (from PRD NFRs)
- Dependency summary table
- Empty spec index (to be filled as specs are written)

Write to `ROADMAP.md` (or `docs/planning/ROADMAP.md` if a `docs/` directory exists).

### Step 6: Confirm with the Engineer

Present the roadmap for review:
- Phase count and feature distribution
- Critical path (the longest dependency chain)
- Any PRD requirements that didn't map cleanly (ambiguous, too large, conflicting)

---

## References

- `references/roadmap-template.md` — Unified ROADMAP.md format with feature descriptions + implementation checklists
