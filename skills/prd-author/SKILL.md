---
name: prd-author
description: >
  Interactive PRD creation and iteration for non-technical users. Use this skill
  whenever the user wants to define product requirements, write a PRD, spec out a
  feature, describe what to build, or says "what should we build", "write requirements",
  "create a PRD", "define the product". Also use when updating an existing PRD based
  on stakeholder or engineering feedback. Guides through structured requirement
  definition using plain-language facilitation prompts with discovery questions upfront.
  Auto-validates with /prd-validator after completion.
user-invocable: true
argument-hint: "[create | iterate [path/to/PRD.md]]"
allowed-tools: Read, Grep, Glob, Write
model: sonnet
tags: [documentation, meta]
---

# PRD Author

Create or iterate on a Product Requirements Document.

---

## When to Use

- Starting a new product initiative from scratch
- Translating stakeholder conversations into structured requirements
- Updating an existing PRD after feedback from engineering, design, or stakeholders
- Before handing off requirements to an engineering team

---

## Usage

```
/prd-author create                  # New PRD from scratch
/prd-author iterate PRD.md          # Update existing PRD
/prd-author iterate                 # Update PRD.md in current directory
```

---

## Mode: Create

### Phase 1: Discovery Questions

Before writing any PRD sections, run through the discovery questions from `references/discovery-questions.md`. These surface assumptions, constraints, and scope boundaries upfront.

Ask the 8 core questions:
1. **The Problem** — What problem, without mentioning a solution?
2. **The Stakes** — What happens if we don't solve this?
3. **Prior Art** — What's been tried before?
4. **Stakeholders** — Who has input? Who has veto power?
5. **Constraints** — Timeline, budget, team, technology, compliance?
6. **Success Definition** — What changes if this works perfectly?
7. **Non-Goals** — What are we explicitly not trying to achieve?
8. **Existing Context** — Is there existing code to reverse-engineer first?

This phase is essential — skipping it produces PRDs that answer the wrong question. The answers feed directly into PRD sections (see the mapping table in the reference file). If the user has already documented answers elsewhere, reference those rather than re-asking.

If question 8 reveals existing code, suggest running `/reverse-engineer discover` before proceeding.

### Phase 2: Structured Authoring

Walk the user through each section of the PRD template using the facilitation prompts. Work through sections in order, using discovery answers as input:

1. **Problem Statement** — From discovery Q1 + Q2
2. **User Personas** — From discovery Q4 + new prompts for goals/pain points
3. **Functional Requirements** — Each requirement with ID, description, priority, acceptance criteria
4. **Non-Functional Requirements** — From discovery Q5 (constraints)
5. **Scope Boundary** — From discovery Q7 (non-goals)
6. **Milestones / Phases** — Phased delivery with deliverable statements
7. **Success Metrics** — From discovery Q6
8. **Dependencies** — From discovery Q4 + Q5
9. **Open Questions** — From discovery Q3 (prior art gaps) + anything unresolved

For each section:
- Present the facilitation prompt from `references/facilitation-prompts.md`
- Pre-fill with relevant discovery answers where applicable
- Capture additional input from the user
- Structure it into the template format from `references/prd-template.md`
- Confirm with the user before moving to the next section

### Phase 3: Validation

After all sections are complete:
- Write the PRD to `PRD.md` (or user-specified path)
- Auto-run `/prd-validator` on the result
- If NEEDS WORK, address the findings and re-validate

## Mode: Iterate

Update an existing PRD based on user-described changes. Follow `references/iteration-guide.md`:

1. Read the existing PRD
2. Ask the user what changed (new requirements, scope changes, priority shifts, engineering feedback)
3. Apply changes following the iteration guide's conventions (change markers, ID management)
4. Write the updated PRD
5. Auto-run `/prd-validator` on the result
6. If NEEDS WORK, address the findings and re-validate

---

## References

- `references/prd-template.md` — Canonical PRD format with all required sections
- `references/facilitation-prompts.md` — Plain-language prompts for each PRD section
- `references/iteration-guide.md` — Guide for updating existing PRDs (add, revise, split, merge)
- `references/discovery-questions.md` — Pre-authoring questions to surface assumptions and constraints
