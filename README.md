# Fellowship of the Workflows

A centralized repository for sharing AI agent workflows across your team. Works with both Cursor and Claude Code.

## Quick Start

```bash
# 1. Install dependencies (macOS with Homebrew)
./bin/bootstrap

# 2. List available workflows
./bin/list

# 3. Install a workflow
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
| `./bin/install` | Deploy workflow to a project or globally |
| `./bin/new` | Create a new workflow from template |
| `./bin/validate` | Validate workflow files |

Run any command with `--help` for full options.

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
