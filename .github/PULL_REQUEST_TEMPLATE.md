## Summary

<!-- What changed and why. 1-3 bullet points. -->

-

## Workflow Types Affected

<!-- Check all that apply -->

- [ ] Skills (`skills/`)
- [ ] Agents (`agents/`)
- [ ] Rules (`rules/`)
- [ ] Hooks (`hooks/`)
- [ ] Personas (`personas/`)
- [ ] CLI (`cli/`)
- [ ] Teams (`teams/`)
- [ ] Platforms / Vendors (`platforms/`, `vendors/`)

## Checklist

- [ ] `./bin/fotw validate` passes
- [ ] Skill SKILL.md is under 500 lines (deep content in `references/`)
- [ ] `allowed-tools` uses scoped Bash (no broad `Bash(git:*)` or `Bash(gh:*)`)
- [ ] No persona-specific language in workflow files (per Persona Independence rule)
- [ ] Version bumped in `.claude-plugin/plugin.json` (if modifying agents/hooks/skills)

## Test Plan

<!-- How did you verify this works? -->

-
