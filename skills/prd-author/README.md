# prd-author

Interactive PRD creation and iteration with structured discovery questions upfront.

## Usage

```
/prd-author create                  # New PRD from scratch
/prd-author iterate PRD.md          # Update existing PRD
```

## When to Use

- Starting a new product initiative and need structured requirements
- Translating stakeholder conversations into a formal PRD
- Updating an existing PRD after engineering or design feedback
- A non-technical user needs to define what to build

## What It Does

- Runs 8 discovery questions (problem, stakes, prior art, stakeholders, constraints, success, non-goals, existing context) before writing any sections
- Walks through each PRD section using plain-language facilitation prompts
- Auto-validates the result with `/prd-validator` (score >= 70 required)

## References

- `references/prd-template.md` — Canonical PRD format
- `references/discovery-questions.md` — Pre-authoring questions
- `references/facilitation-prompts.md` — Plain-language section prompts
- `references/iteration-guide.md` — Guide for updating existing PRDs
