# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fellowship of the Workflows is a centralized repository for sharing AI agent workflows. It provides starter templates, reusable workflows (skills, rules, agents), and a persona system for both Cursor and Claude Code.

## Commands

```bash
# Setup
./bin/bootstrap              # Install deps (jq, fzf, yq)
./bin/bootstrap --check      # CI-friendly check only

# List available workflows
./bin/list                   # All workflows
./bin/list --skills          # Skills only
./bin/list --rules           # Rules only
./bin/list --agents          # Agents only

# Create new workflows
./bin/new skill/my-skill     # New skill package
./bin/new rule/my-rule       # New rule file
./bin/new agent/my-agent     # New agent definition

# Install to target project (prompts before overwriting)
./bin/install starters/standard ~/project --for claude-code
./bin/install skills/code-review ~/project --for claude-code
./bin/install rules/ai-session --global --for cursor
./bin/install skills/code-review ~/project --for claude-code --force  # Skip prompt

# Validate before committing
./bin/validate               # Check all workflows
./bin/validate --verbose     # Show each file
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
| `minimal` | Git safety, output style (~25 lines) |
| `standard` | + Discover → Plan → Implement workflow (~55 lines) |
| `full` | + Persona system, multi-repo safety (~115 lines) |

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

Rules stored in Cursor format (`.mdc`) are automatically translated when installing for Claude Code:
- `globs` → `paths` (as array)
- `alwaysApply: true` → `paths: ["**/*"]`

## Key Directories

- `bin/` — CLI tools (bash scripts)
- `workflows/` — Skills, rules, agents
- `starters/` — CLAUDE.md/AGENTS.md templates
- `starters/personas/` — 12 themed persona definitions
- `starters/snippets/` — Modular template components
