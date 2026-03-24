# prd-to-roadmap

Translates an approved PRD into a phased ROADMAP.md with implementation checklists.

## Usage

```
/prd-to-roadmap                     # Uses PRD.md in current directory
/prd-to-roadmap path/to/PRD.md      # Specific PRD file
```

## When to Use

- You have a finalized PRD and need to break it into development phases
- Planning sprint work from approved requirements
- Creating a phased delivery plan with dependency ordering

## What It Does

- Gates on PRD validation — refuses to proceed if score < 70
- Decomposes requirements into sequenced phases with dependency ordering
- Produces ROADMAP.md with per-phase feature descriptions and implementation checklists

## References

- `references/roadmap-template.md` — Canonical roadmap format
