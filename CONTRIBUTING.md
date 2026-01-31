# Contributing to Fellowship of the Workflows

Thank you for contributing! This guide explains how to add new workflows.

## Quick Start

```bash
# Create a new skill
./bin/new skill/my-skill

# Create a new rule
./bin/new rule/my-rule

# Create a new agent
./bin/new agent/my-agent

# Validate your changes
./bin/validate
```

## Adding Workflows

### 1. Use the `new` command

The easiest way to add a workflow is using the `new` script:

```bash
./bin/new rule/code-style
./bin/new skill/pr-review
./bin/new agent/researcher
```

This will:
- Create the appropriate directory structure
- Generate a template with required frontmatter
- Open the file in your `$EDITOR`

### 2. Frontmatter Requirements

#### Rules (`.mdc` files)

Rules are stored in Cursor format and automatically translated when installing for Claude Code.

```yaml
---
description: "Brief description of what this rule does"
globs: "**/*.ts"  # Optional: file patterns to match
alwaysApply: false  # true = always applied, false = agent decides
---
```

**Translation for Claude Code:**
- `globs` → `paths` (as array)
- `alwaysApply: true` → `paths: ["**/*"]`

#### Skills (`SKILL.md`)

```yaml
---
name: my-skill                    # Required: must match directory name
description: "What this does"     # Required: when to use it
# Cross-platform fields (work in both Cursor and Claude Code):
context: fork                     # Optional: isolated subagent execution
agent: my-agent                   # Optional: link to agent definition
allowed-tools: Read, Grep         # Optional: restrict available tools

# Claude Code-specific (ignored by Cursor):
model: sonnet                     # Optional: opus, sonnet, or haiku
argument-hint: "[PR#]"            # Optional: CLI autocomplete hint
disable-model-invocation: false   # Optional: set true to require /command
user-invocable: true              # Optional: set false to hide from / menu
---
```

#### Agents (`.md` files)

```yaml
---
name: my-agent
description: "What this agent specializes in"
tools: Bash, Glob, Grep, Read, Write    # Tools available to agent
model: sonnet                            # opus, sonnet, or haiku
---
```

### 3. Skill Directory Structure

Skills can include additional resources:

```
my-skill/
├── SKILL.md           # Required - main instructions
├── references/        # Optional - additional documentation
│   └── checklist.md
├── scripts/           # Optional - executable helpers
│   └── analyze.sh
└── assets/            # Optional - templates, config
    └── template.json
```

### 4. Dynamic Context Injection

Skills can embed live command output using the `` !`command` `` syntax:

```markdown
## Context

Current branch:
```
!`git branch --show-current`
```

Modified files:
```
!`git diff --name-only`
```
```

The command executes at skill invocation time, injecting results into the prompt context. This works in both Cursor and Claude Code.

### 5. Validate Before Committing

```bash
./bin/validate
```

This checks:
- Required frontmatter fields are present
- Skill directories contain SKILL.md

## Best Practices

### Writing Good Descriptions

- Be specific about when to use the workflow
- Mention key features or capabilities
- Keep it concise (one sentence is ideal)

### Skill Content Guidelines

- Start with "When to Use" section
- Provide clear, numbered instructions
- Include examples where helpful
- Reference external docs in `references/` directory

### Rule Content Guidelines

- Keep rules focused on one topic
- Use concrete examples, not abstract guidance
- Avoid duplicating what AI already knows (common patterns, popular frameworks)
- Use Cursor frontmatter format (`globs`, `alwaysApply`) - translation is automatic
