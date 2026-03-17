# Fellowship Roster

Roles are curated skill + rule bundles for specific engineering disciplines.

## Usage

```bash
# List available roles
./bin/fotw list --type role

# Install a role (installs all its skills + rules)
./bin/fotw install rosters/backend ~/my-project --for claude-code

# Dry-run to see what would be installed
./bin/fotw install rosters/frontend ~/my-project --for claude-code --dry-run
```

## Role Format

```yaml
---
name: my-role
description: "What this role optimizes for"
tags: [engineering, backend]
allowed-skills:
  - code-review
  - api-design
denied-skills:
  - design-review
rules:
  - git-safety
  - output-style
preferred-model: sonnet
persona: gandalf
---
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Must match filename stem |
| `description` | Yes | Shown in `fotw list --type role` |
| `tags` | No | Open vocabulary for categorization |
| `allowed-skills` | Yes | Skills installed with this role |
| `denied-skills` | No | Skills explicitly excluded (advisory) |
| `rules` | No | Rules installed alongside skills |
| `preferred-model` | No | Suggested model tier (opus/sonnet/haiku) |
| `persona` | No | Default persona pairing |

## Design Principles

- **Roles are singular** — a project has one active role at a time
- **Composing** — to combine roles, install individual skills instead
- **Advisory enforcement** — the `roster-enforcement` rule guides behavior but doesn't hard-block
- **Open tags** — no controlled vocabulary; use whatever tags make sense
