# Fellowship of the Workflows

A centralized repository for sharing AI agent workflows across your team. Works with both Cursor and Claude Code.

## Quick Start

```bash
# 1. Install dependencies (macOS with Homebrew)
./bin/bootstrap

# 2. Bootstrap a new project with a starter template
./bin/install starters/standard ~/my-project --for claude-code  # → CLAUDE.md
./bin/install starters/standard ~/my-project --for cursor       # → AGENTS.md
./bin/install starters/standard ~/my-project --for both         # → Both files

# 3. List available workflows
./bin/list

# 4. Install workflows
./bin/install rules/ai-session ~/my-project --for cursor
./bin/install skills/code-review ~/my-project --for claude-code

# Or install globally (available in all projects)
./bin/install rules/ai-session --global --for cursor
```

## Commands

| Command | Description |
|---------|-------------|
| `./bin/bootstrap` | Install dependencies (jq, fzf, yq) |
| `./bin/list` | List available workflows |
| `./bin/install` | Deploy workflow or starter to a project |
| `./bin/new` | Create a new workflow from template |
| `./bin/validate` | Validate workflow files |

Run any command with `--help` for full options.

## Starter Templates

New to AI coding assistants? Start with a pre-configured template:

```bash
# For Claude Code → creates CLAUDE.md
./bin/install starters/standard ~/my-project --for claude-code

# For Cursor (and Copilot, Codex, etc.) → creates AGENTS.md
./bin/install starters/standard ~/my-project --for cursor

# For mixed teams → creates both files
./bin/install starters/standard ~/my-project --for both
```

| Tier | Description |
|------|-------------|
| `minimal` | Git safety, output style, project placeholders (~25 lines) |
| `standard` | Adds Discover → Plan → Implement workflow, session docs (~55 lines) |
| `full` | Adds persona system (12 characters), multi-repo safety (~115 lines) |

See [starters/README.md](starters/README.md) for details and modular snippets.

## Workflow Types

| Type | Description | Cursor | Claude Code |
|------|-------------|--------|-------------|
| **Rules** | Conditional context files | `.cursor/rules/*.mdc` | `.claude/rules/*.md` |
| **Skills** | Executable packages ([Agent Skills](https://agentskills.io) standard) | `.cursor/skills/<name>/` | `.claude/skills/<name>/` |
| **Agents** | Subagent definitions | `.cursor/agents/*.md` | `.claude/agents/*.md` |

Rules are stored in Cursor format and automatically translated for Claude Code on install.

### Claude Code Enhancements

Skills and agents support additional Claude Code fields (`model`, `argument-hint`, `disable-model-invocation`, `user-invocable`) that are ignored by Cursor. These are optional—workflows work without them. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full schema.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new workflows.

## License

MIT
