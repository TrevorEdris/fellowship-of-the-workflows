# Starter Templates

Quickstart templates for configuring AI coding assistants in your projects.

## Tool Support

| Tool | Output File | Standard |
|------|-------------|----------|
| Claude Code | `CLAUDE.md` | Claude-specific |
| Cursor | `AGENTS.md` | [Universal standard](https://agents.md/) |
| GitHub Copilot | `AGENTS.md` | Universal standard |
| Other tools | `AGENTS.md` | Universal standard |

Both files use identical content — only the filename differs.

## Choose Your Tier

| Tier | Lines | Best For |
|------|-------|----------|
| `minimal` | ~25 | Quick setup, small projects |
| `standard` | ~55 | Most projects (recommended) |
| `full` | ~115 | Power users, multi-repo workspaces, Gandalf persona |

## Installation

```bash
# For Claude Code users
./bin/install starters/standard ~/my-project --for claude-code

# For Cursor users (creates AGENTS.md)
./bin/install starters/standard ~/my-project --for cursor

# For teams with mixed tooling (creates both files)
./bin/install starters/standard ~/my-project --for both

# Install CLAUDE.md to .claude/ directory instead of project root
./bin/install starters/standard ~/my-project --for claude-code --to-claude-dir
```

Then edit the template to fill in your project-specific details.

## Tier Comparison

### Minimal
- Project overview placeholder
- Tech stack placeholder
- Build commands placeholder
- Git safety rules
- Output style guidelines

### Standard (Recommended)
Everything in Minimal, plus:
- Discover → Plan → Implement workflow
- Session documentation pattern
- Enhanced git safety

### Full
Everything in Standard, plus:
- Gandalf persona (LotR-themed phase names and quips)
- Multi-repo safety rules
- Repository map for workspaces
- Required session documentation

## Modular Snippets

Prefer to build your own? Mix and match from `snippets/`:

| Snippet | Purpose |
|---------|---------|
| `workflow-discover-plan-implement.md` | Structured workflow phases |
| `session-documentation.md` | Session tracking for complex tasks |
| `git-safety.md` | Safe git practices |
| `output-style.md` | Concise, professional output |
| `gandalf-persona.md` | Optional Middle-earth flavor |

## What Each Section Does

### Project Overview / Tech Stack / Build Commands
Helps the AI understand your project context. Fill in your specific details.

### Workflow: Discover → Plan → Implement
Prevents the AI from jumping straight to code. Enforces:
1. **Discover** — Understand before changing
2. **Plan** — Get approval before implementing
3. **Implement** — Execute with minimal diffs

### Session Documentation
Creates an audit trail in `.ai/sessions/` for complex tasks. Useful for:
- Handoffs between sessions
- Reviewing decisions later
- Multi-step implementations

### Git Safety
Prevents common accidents:
- No direct commits to main/master
- No accidental credential commits
- Branch awareness before changes

### Output Style
Reduces verbose AI patterns:
- Skip filler phrases
- Use bullets over paragraphs
- State facts directly

### Gandalf Persona (Full only)
Adds thematic elements without overwhelming:
- LotR-themed workflow phase names
- Witty safety reminders
- Opening and closing quotes
