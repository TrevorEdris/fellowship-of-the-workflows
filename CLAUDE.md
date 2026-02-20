# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fellowship of the Workflows is a centralized repository for sharing AI agent workflows. It provides starter templates, reusable workflows (skills, rules, agents), and a persona system for 9 AI tool targets.

## Commands

```bash
# Setup
./bin/bootstrap              # Set up CLI (Python 3.10+ required)
./bin/bootstrap --check      # CI-friendly check only

# List available workflows
./bin/fotw list              # All workflows
./bin/fotw list --type skill # Skills only
./bin/fotw list --json       # JSON output

# Create new workflows
./bin/fotw new skill/my-skill     # New skill package
./bin/fotw new rule/my-rule       # New rule file
./bin/fotw new agent/my-agent     # New agent definition

# Install to target project (prompts before overwriting)
./bin/fotw install starters/standard ~/project --for claude-code
./bin/fotw install skills/code-review ~/project --for copilot
./bin/fotw install rules/ai-session --global --for cursor
./bin/fotw install --all ~/project --for claude-code --force  # Install everything

# Validate before committing
./bin/fotw validate          # Check all workflows
./bin/fotw validate --verbose
```

## Architecture

### Workflow Types

| Type | Storage | Description |
|------|---------|-------------|
| **Skills** | `workflows/skills/<name>/SKILL.md` | Executable packages with references, scripts, assets |
| **Rules** | `workflows/rules/*.mdc` | Conditional context files (Cursor format, auto-translated for Claude Code) |
| **Agents** | `workflows/agents/*.md` | Subagent definitions with tool restrictions |

### Skill Package Structure

```
skills/<name>/
├── SKILL.md           # Required - main instructions with YAML frontmatter
├── references/        # Additional documentation
├── scripts/           # Executable helpers
└── assets/            # Templates, configs
```

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

### Starter Tiers

| Tier | Content |
|------|---------|
| `minimal` | Git safety, output style (~20 lines) |
| `standard` | + Discover → Plan → Implement workflow (~30 lines) |
| `full` | + Persona system, multi-repo safety (~40 lines) |

### Dynamic Context Injection

Skills can embed live command output using `` !`command` `` syntax:
```markdown
Current branch:
\```
!`git branch --show-current`
\```
```

The command executes at skill invocation, injecting results into the prompt.

### Installation Translation

Rules stored in Cursor format (`.mdc`) are automatically translated per target tool:
- **Claude Code:** `globs` → `paths` (as array), `alwaysApply: true` → `paths: ["**/*"]`
- **Copilot:** `globs` → `applyTo`, `alwaysApply: true` → `applyTo: "**"`
- **Generic** (codex, windsurf, gemini, roo, goose, universal): description only

Supported `--for` targets: claude-code, cursor, copilot, codex, windsurf, gemini, roo, goose, universal, both.

## Key Directories

- `bin/` — CLI wrapper scripts (delegate to Python CLI)
- `workflows/` — Skills, rules, agents
- `starters/` — CLAUDE.md/AGENTS.md templates
- `starters/personas/` — 12 themed persona definitions
- `starters/snippets/` — Modular template components
