---
name: team
description: "Create an Agent Team from a predefined roster. Spawns multiple Claude Code sessions that coordinate via shared tasks and direct messaging."
context: fork
agent: team-lead
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(git status), Bash(git branch:*), Glob, Grep, Read, Task, SendMessage
tags: [meta]
model: opus
---

# Agent Teams

Spawn a coordinated team of Claude Code sessions from a predefined roster. Each teammate is a full, independent session with its own context window. Teammates communicate directly with each other and coordinate through a shared task list.

## Context

AVAILABLE ROSTERS:
```
!`ls teams/rosters/*.yaml 2>/dev/null | xargs -I{} basename {} .yaml | sort || echo "No rosters found"`
```

AVAILABLE AGENTS (for reference):
```
!`ls agents/ 2>/dev/null | sed 's/\.md$//' | sort || echo "No agents found"`
```

GIT STATUS:
```
!`git status --short 2>/dev/null || echo "Not a git repo"`
```

CURRENT BRANCH:
```
!`git branch --show-current 2>/dev/null || echo "Unknown"`
```

## Usage

```
/team review PR#142
/team implementation "add OAuth2 support to the auth module"
/team investigation "app exits after one message instead of staying connected"
```

## Process

### Step 1: Select Roster

Parse the user's command to identify the requested preset and task context.

Available presets:
- `review` — security + code quality + chaos engineer (PR reviews, pre-merge audits)
- `implementation` — TDD + refactoring + docs sync (feature work, large refactors)
- `investigation` — 3x systematic debugger with competing hypotheses (bug hunting)

If the preset is ambiguous or not specified, ask the user to choose.

### Step 2: Load Roster

Read the roster file from `teams/rosters/<preset>-team.yaml`. Extract:
- Teammate definitions (name, agent, model, focus, plan_approval)
- Lead model and coordination strategy
- Team size

Present the team composition to the user:
- Who each teammate is and what they focus on
- The coordination strategy
- Expected token cost (each teammate ≈ 200k tokens; total ≈ team_size × 200k + lead)

**Wait for explicit user approval before spawning.**

### Step 3: Create Team

Use Agent Teams primitives to:
1. Create the team
2. Create tasks based on the user's request, decomposed per the coordination strategy
3. Spawn each teammate with their focus area and the agent definition from `agents/<agent>.md`

Each teammate receives:
- Their `focus` field as primary directive
- The task context from the user's request
- Access to the shared task list

### Step 4: Coordinate

The team lead (this session) coordinates by:
- Monitoring teammate progress via task list
- **Proactively pushing cross-teammate findings** — when one teammate discovers something relevant to another, message them immediately
- Requiring plan approval from teammates where the roster specifies `plan_approval: true`
- Reassigning work if a teammate gets stuck

### Step 5: Synthesize

When all teammates finish:
1. Collect results from each teammate
2. Identify areas of agreement and disagreement
3. Produce a unified report with per-teammate contributions
4. Clean up the team

## References

- [references/team-roster-schema.md](references/team-roster-schema.md) — Roster YAML format
- [references/agent-teams-primer.md](references/agent-teams-primer.md) — Agent Teams primitives reference
