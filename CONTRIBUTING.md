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
name: my-skill  # Must match directory name
description: "What this skill does and when to use it"
---
```

#### Agents (`.md` files)

```yaml
---
name: my-agent
description: "What this agent specializes in"
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

### 4. Validate Before Committing

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
