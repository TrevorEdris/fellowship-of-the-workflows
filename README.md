# Fellowship of the Workflows

A centralized repository for sharing AI agent workflows across your team. Works with Claude Code, Cursor, Copilot, Codex, Windsurf, Gemini, Roo, Goose, and more.

## Quick Start

```bash
# 1. Set up the CLI (creates a project-local Python venv)
./bin/bootstrap

# 2. Bootstrap a new project with a starter template
./bin/fotw install starters/standard ~/my-project --for claude-code  # → CLAUDE.md
./bin/fotw install starters/standard ~/my-project --for cursor       # → AGENTS.md
./bin/fotw install starters/standard ~/my-project --for copilot      # → AGENTS.md + .github/instructions/
./bin/fotw install starters/standard ~/my-project --for both         # → Both CLAUDE.md and AGENTS.md

# 3. List available workflows
./bin/fotw list

# 4. Install individual workflows
./bin/fotw install rules/ai-session ~/my-project --for cursor
./bin/fotw install skills/code-review ~/my-project --for claude-code

# Or install globally (available in all projects)
./bin/fotw install rules/ai-session --global --for cursor
```

## Commands

| Command | Description |
|---------|-------------|
| `./bin/bootstrap` | Set up the CLI environment (Python 3.10+ required) |
| `./bin/fotw list` | List available workflows |
| `./bin/fotw install` | Deploy workflow or starter to a project |
| `./bin/fotw new` | Create a new workflow from template |
| `./bin/fotw validate` | Validate workflow files |

Run any command with `--help` for full options. The `./bin/list`, `./bin/install`, `./bin/new`, and `./bin/validate` shortcuts also work.

### Install Options

The install command will prompt before overwriting existing files. Use `--force` to skip the prompt:

```bash
./bin/fotw install skills/code-review ~/my-project --for claude-code --force
```

Other useful flags:
- `--dry-run` / `-n` — Preview what would be installed without copying
- `--global` / `-g` — Install to `~/.<tool>/` (available in all projects)
- `--all` / `-a` — Install all workflows at once
- `--to-claude-dir` — Place CLAUDE.md inside `.claude/` directory

### Supported Tools

| Tool | `--for` value | Config directory | Rule extension |
|------|---------------|------------------|----------------|
| Claude Code | `claude-code` | `.claude/` | `.md` |
| Cursor | `cursor` | `.cursor/` | `.mdc` |
| GitHub Copilot | `copilot` | `.github/` | `.instructions.md` |
| OpenAI Codex | `codex` | `.codex/` | `.md` |
| Windsurf | `windsurf` | `.windsurf/` | `.md` |
| Gemini Code Assist | `gemini` | `.gemini/` | `.md` |
| Roo Code | `roo` | `.roo/` | `.md` |
| Goose | `goose` | `.goose/` | `.md` |
| Universal | `universal` | `.ai/` | `.md` |

Use `--for both` to install for both Claude Code and Cursor simultaneously.

## Starter Templates

New to AI coding assistants? Start with a pre-configured template:

```bash
# For Claude Code → creates CLAUDE.md
./bin/fotw install starters/standard ~/my-project --for claude-code

# For Cursor → creates AGENTS.md
./bin/fotw install starters/standard ~/my-project --for cursor

# For any supported tool
./bin/fotw install starters/standard ~/my-project --for copilot
```

| Tier | Description |
|------|-------------|
| `minimal` | Git safety, output style (~20 lines) |
| `standard` | + Discover → Plan → Implement workflow, session docs (~30 lines) |
| `full` | + Persona system (12 characters), multi-repo safety (~40 lines) |

See [starters/README.md](starters/README.md) for details and modular snippets.

## Workflow Types

| Type | Description | Storage format |
|------|-------------|----------------|
| **Rules** | Conditional context files | `workflows/rules/*.mdc` (Cursor format, translated on install) |
| **Skills** | Executable packages ([Agent Skills](https://agentskills.io) standard) | `workflows/skills/<name>/SKILL.md` |
| **Agents** | Subagent definitions | `workflows/agents/*.md` |

Rules are stored in Cursor format and automatically translated to each tool's native format on install (e.g., `globs` → `paths` for Claude, `globs` → `applyTo` for Copilot).

### Claude Code Enhancements

Skills and agents support additional Claude Code fields (`model`, `argument-hint`, `disable-model-invocation`, `user-invocable`) that are ignored by other tools. These are optional — workflows work without them. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full schema.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new workflows.

## License

MIT
