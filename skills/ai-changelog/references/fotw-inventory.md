# FOTW Inventory

Current capabilities of the Fellowship of the Workflows project. Used by the ai-changelog skill to assess impact of new AI tooling features.

## Supported Tools

Claude Code, Cursor, Copilot, Codex, Windsurf, Gemini, Roo, Goose, Universal

## Workflow Types

- **Skills** — Executable packages with references, scripts, assets
- **Rules** — Conditional context files (Cursor format, auto-translated)
- **Agents** — Subagent definitions with tool restrictions
- **Hooks** — Claude Code hook scripts (global, claude-code only)

## Core Skills

| Skill | Domain | Key Capability |
|-------|--------|----------------|
| code-review | Review | PR review with Pragmatic Quality framework |
| security-review | Security | Vulnerability detection with >80% confidence |
| systematic-debugging | Debugging | 4-phase root cause analysis |
| refactoring | Code quality | Smell detection + safe transformation |
| test-driven-development | Testing | RED-GREEN-REFACTOR enforcement |
| orchestrate | Coordination | Multi-agent task decomposition |
| session-handoff | Context | Session state preservation |
| git-workflow | Git | Conventional commits, PR generation |
| cicd-pipeline | CI/CD | GHA/GitLab pipeline generation |
| update-docs | Documentation | Doc-code sync detection |
| desloppify | Quality | AI slop detection and removal |
| code-pattern-advisor | Architecture | Design pattern guidance |
| eval | Meta | Golden test evaluation and generation |
| ai-changelog | Meta | AI tooling change tracking |

## Key Architectural Patterns

- Single-source multi-target translation (Cursor → all tools)
- Progressive disclosure (SKILL.md → references/)
- Agent delegation (skill → subagent with restricted tools)
- Dynamic context injection (`!command` syntax)
- Golden test evaluation (deterministic + LLM-rubric)
