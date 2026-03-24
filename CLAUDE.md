# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fellowship of the Workflows is a centralized repository for sharing AI agent workflows. It provides starter templates, reusable workflows (skills, rules, agents), and a persona system for 9 AI tool targets.

## Commands

```bash
# Setup
./bin/bootstrap              # Set up CLI (Python 3.10+ required, creates cli/.venv/)
./bin/bootstrap --check      # CI-friendly check only (exit 0/1)
./bin/bootstrap --force       # Full reinstall

# List available workflows
./bin/fotw list              # All workflows
./bin/fotw list --type skill # Skills only
./bin/fotw list --json       # JSON output

# Create new workflows
./bin/fotw new skill/my-skill     # New skill package
./bin/fotw new rule/my-rule       # New rule file
./bin/fotw new agent/my-agent     # New agent definition

# Install to target project (prompts before overwriting)
./bin/fotw install skills/code-review ~/project --for copilot
./bin/fotw install rules/ai-session --global --for cursor
./bin/fotw install --all ~/project --for claude-code --force  # Install everything

# Install hooks (Claude Code only, global only)
./bin/fotw install hooks --global --for claude-code           # All hooks
./bin/fotw install hooks/branch-guard --global --for claude-code  # Single hook
./bin/fotw install hooks --global --for claude-code --include-tests  # With test files

# Setup — install all rules with lock file tracking
./bin/fotw setup ~/my-project --for claude-code               # Install all rules
./bin/fotw setup ~/my-project --for cursor --force            # Overwrite existing
./bin/fotw setup ~/my-project --for claude-code --dry-run     # Preview only

# Update — re-sync installed rules after git pull
./bin/fotw update ~/my-project                                # Update changed rules
./bin/fotw update ~/my-project --force                        # Re-install all
./bin/fotw update ~/my-project --dry-run                      # Preview only

# Validate before committing
./bin/fotw validate          # Check all workflows
./bin/fotw validate --verbose
```

### Testing

```bash
# Run all tests
cd cli && python -m pytest

# Run a single test file
cd cli && python -m pytest tests/test_catalog.py

# Run a single test
cd cli && python -m pytest tests/test_install.py::test_translate_frontmatter_claude -v

# Install dev dependencies (if not already)
cd cli && pip install -e ".[dev]"
```

Tests use `FOTW_REPO_ROOT` env var to override repo root detection, allowing tests to run against fixture directories.

## Architecture

### Core Design: Single Source, Multi-Target Translation

Rules are authored **once** in Cursor `.mdc` format and translated to each tool's native format at install time. This is the central architectural pattern — avoids maintaining 9 copies of every rule.

Translation is handled by `cli/fotw/services/frontmatter_translator.py`:
- **Claude Code:** `globs` → `paths` (array), `alwaysApply: true` → `paths: ["**/*"]`, body `.mdc` refs → `.md`
- **Copilot:** `globs` → `applyTo` (string), `alwaysApply: true` → `applyTo: "**"`, body `.mdc` refs → `.instructions.md`
- **Generic** (codex, windsurf, gemini, roo, goose, universal): frontmatter stripped to description only

Supported `--for` targets: claude-code, cursor, copilot, codex, windsurf, gemini, roo, goose, universal, both.

### Workflow Types

| Type | Storage | Description |
|------|---------|-------------|
| **Skills** | `skills/<name>/SKILL.md` | Executable packages with references, scripts, assets |
| **Rules** | `rules/*.mdc` | Conditional context files (Cursor format, auto-translated) |
| **Agents** | `agents/*.md` | Subagent definitions with tool restrictions |
| **Hooks** | `hooks/*.js` | Claude Code hook scripts (global, claude-code only) |

### CLI Architecture

Python package at `cli/fotw/` built with **Typer** (CLI) + **Rich** (terminal UI) + **python-frontmatter** (YAML parsing).

| Layer | Path | Purpose |
|-------|------|---------|
| Entry | `bin/fotw` → `cli/fotw/__main__.py` | Shell wrapper delegates to `python -m fotw` |
| Commands | `cli/fotw/commands/` | `list`, `install`, `new`, `setup`, `update`, `validate` |
| Services | `cli/fotw/services/` | `catalog` (scan/parse), `installer` (deploy + conflict resolution), `frontmatter_translator`, `agents` (tool configs), `settings_merger` (hooks JSON merge) |
| Models | `cli/fotw/models/` | `Workflow`, `Starter`, `Persona`, `Hook`, `ValidationResult`, `WorkflowType`, `LockEntry` |
| UI | `cli/fotw/ui/` | `console` (Rich), `tables`, `diff` (paged syntax-highlighted diffs) |

Tool target configs are defined as `AgentConfig` dataclasses in `cli/fotw/services/agents.py` — each maps a tool name to its config directory, starter filename, rule extension, and frontmatter format.

### Frontmatter Schemas

**Skills:**
```yaml
---
name: my-skill                    # Required
description: "What this does"     # Required
context: fork                     # Optional: isolated execution
agent: agent-name                 # Optional: link subagent
allowed-tools: Read, Grep         # Optional: restrict tools
model: sonnet                     # Claude-only: opus, sonnet, haiku
tags: [infrastructure, aws]       # Optional: controlled vocabulary for categorization
---
```

**Rules:**
```yaml
---
description: "Brief description"
globs: "**/*.ts"                  # File patterns to match
alwaysApply: false                # true = always, false = agent decides
---
```

**Agents:**
```yaml
---
name: my-agent
description: "Specialization"
tools: Bash, Glob, Grep, Read, Write
model: sonnet
---
```

**Hooks** (inline JSDoc metadata, not YAML):
```javascript
/**
 * @fotw-hook {"event":"PreToolUse","matcher":"Bash","description":"What this hook does"}
 */
```
- `event` — Claude Code hook event: `PreToolUse`, `PostToolUse`, `PreCompact`, `UserPromptSubmit`, etc.
- `matcher` — Tool name filter (e.g., `"Bash"`, `"Edit|Write|Bash"`). Empty string = all tools.
- `description` — Short description for `fotw list`.

### Dynamic Context Injection

Skills can embed live command output using `` !`command` `` syntax:
```markdown
Current branch:
\```
!`git branch --show-current`
\```
```

The command executes at skill invocation, injecting results into the prompt.

### Install Conflict Resolution

When installing over existing files, the installer prompts: `[o]verwrite / [s]kip / [d]iff / [b]ackup / [O]verwrite-all / [S]kip-all / [q]uit`. The `InstallContext` carries a `sticky_action` field that propagates `OVERWRITE_ALL` or `SKIP_ALL` across multi-file sessions. Identical files are silently skipped.

## Maintenance Rules

### Agent Catalog

The orchestration skill maintains an agent catalog at `skills/orchestrate/references/agent-catalog.md`. This catalog maps each agent to its domain, capabilities, model, and tools — enabling the orchestrator to route subtasks to the best-fit agent.

**When adding or modifying any agent** (`agents/*.md`):
1. Add/update a row in the Routing Guide table
2. Add/update the Agent Capability Details section
3. Run `./bin/fotw validate` to confirm the new agent is indexed

**When removing an agent:** Remove its row and capability section from the catalog.

### Persona Independence

Workflow files (skills, agents, rules) must be **persona-agnostic**. No character names (Gandalf, Treebeard, etc.) or character role-play in workflow definitions. The persona system (`persona.yaml` + `persona-integration.mdc`) handles voice/style at runtime.

Standard severity levels used across all workflow files: **CRITICAL**, **HIGH**, **MEDIUM**, **LOW**.

Phase names in workflow files use plain labels: **Discover**, **Plan**, **Implement**. Persona-flavored phase names (The Palantír, The Council of Elrond, The Journey) belong only in persona definitions under `personas/`.

### Tool Scoping (Least Privilege)

`allowed-tools` in SKILL.md must use the **minimum Bash commands** needed. Never use broad wildcards.

**Prohibited patterns:**
- `Bash(git:*)` — grants `git push --force`, `git reset --hard`, etc.
- `Bash(gh:*)` — grants `gh pr merge`, `gh pr close`, `gh repo delete`, etc.

**Use explicit subcommands instead:**

| Need | Pattern |
|------|---------|
| Read-only git | `Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(git status), Bash(git branch:*)` |
| Read-only GitHub | `Bash(gh pr view:*), Bash(gh pr diff:*), Bash(gh pr list:*)` |
| Analytics | `Bash(git shortlog:*), Bash(git rev-list:*), Bash(gh api:*), Bash(gh repo view:*)` |
| Write (explicit) | `Bash(git add:*), Bash(git commit:*), Bash(git stash:*)` |

**Decision tree:**
1. Skill only reads code/PRs? → Read-only scoping
2. Skill modifies files? → Use `Write`/`Edit` tools, keep git read-only
3. Skill needs to commit? → Add `Bash(git add:*), Bash(git commit:*)` explicitly
4. Skill needs to push? → Don't scope it in allowed-tools. Let the user's permission system handle it.

`fotw validate` warns on `Bash(git:*)` and `Bash(gh:*)`.
