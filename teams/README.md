# Agent Teams

Coordinate multiple Claude Code sessions working together as a team. One session leads, the rest are specialist teammates that communicate directly with each other through shared tasks and messaging.

Agent Teams are Claude Code only. They require Claude Code v2.1.32+ and are experimental.

## Prerequisites

- Claude Code v2.1.32 or later (`claude --version`)
- FOTW plugin or install-mode already set up
- tmux or iTerm2 for split-pane mode (optional — in-process mode works in any terminal)

## Install

```bash
./bin/fotw install teams --global --for claude-code
```

This installs:
- `/team` skill and `team-lead` agent to `~/.claude/`
- `TeammateIdle` and `TaskCompleted` hooks to `~/.claude/hooks/`
- Team conventions rule to `~/.claude/rules/`
- Predefined rosters to `~/.claude/teams/rosters/`
- Enables `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` in `~/.claude/settings.json`

To remove:

```bash
./bin/fotw uninstall teams --global
```

## Quick Start

```
/team review PR#142
```

Claude reads the review-team roster, shows you the team composition (3 reviewers: security, code quality, adversarial), and asks for approval. Once approved, it spawns the team. Each reviewer works independently, challenges each other's findings, and the lead synthesizes a unified review.

## Available Team Presets

| Preset | Command | Teammates | Best For |
|--------|---------|-----------|----------|
| Review | `/team review <context>` | security-review, pragmatic-code-review, chaos-engineer | PR reviews, pre-merge audits |
| Implementation | `/team implementation <context>` | tdd-enforcer, refactoring-specialist, documentation-sync | Feature work, large refactors |
| Investigation | `/team investigation <context>` | 3x systematic-debugger | Bug hunting, root cause analysis |
| Design | `/team design <problem>` | system-design-reviewer, chaos-engineer, pragmatic-code-review | Architecture debates before planning |
| Plan Review | `/team plan-review <path>` | system-design-reviewer, chaos-engineer, scope-analyzer | Stress-test an existing PLAN.md |

### Examples

```
/team review PR#142
/team review "the auth module changes in src/auth/"
/team implementation "add OAuth2 support to the auth module"
/team investigation "app exits after one message instead of staying connected"
/team design "we need to add multi-tenancy to the auth module"
/team plan-review .ai/sessions/2026-03-19_Add-OAuth2/PLAN.md
```

For detailed scenarios including multi-team sequences, see [EXAMPLES.md](EXAMPLES.md).

## Working With Your Team

### Talking to the lead

Type naturally. The lead coordinates the team based on your instructions.

```
Wait for all reviewers to finish before synthesizing.
Tell the security reviewer to also check the session handling code.
```

### Talking to teammates directly

- **In-process mode**: press Shift+Down to cycle through teammates. Type to send a message.
- **Split-pane mode**: click into a teammate's pane.

### Monitoring progress

- Press Ctrl+T to view the shared task list
- The lead's terminal shows all teammates and their current status

### Steering

Redirect teammates that are going off-track:

```
The adversarial reviewer is spending too much time on theoretical issues. Tell them to focus on the auth changes only.
```

### When it's done

The lead synthesizes results automatically. To explicitly end:

```
Clean up the team.
```

## Display Modes

### In-process (default)

All teammates run inside your main terminal. Navigate with keyboard shortcuts:
- **Shift+Down** — cycle through teammates (wraps back to lead after the last one)
- **Enter** — view a teammate's session
- **Escape** — interrupt a teammate's current turn
- **Ctrl+T** — toggle the shared task list

Works in any terminal. No extra dependencies.

### Split panes

Each teammate gets its own pane. Claude Code automatically creates a pane per teammate when spawning — you don't manually assign panes.

```
┌─────────────────────┬─────────────────────┐
│ Lead                │ security-reviewer   │
│ (coordinating)      │ (working on T1)     │
│                     │                     │
├─────────────────────┼─────────────────────┤
│ code-quality-       │ adversarial-        │
│ reviewer            │ reviewer            │
│ (working on T2)     │ (idle)              │
└─────────────────────┴─────────────────────┘
```

Interact by clicking into a teammate's pane or using your multiplexer's navigation keybinds.

**Requirements:** tmux or iTerm2 only. Not supported in zellij, VS Code terminal, Windows Terminal, or Ghostty. Zellij support is tracked upstream ([anthropics/claude-code#24122](https://github.com/anthropics/claude-code/issues/24122)).

If you use zellij, stick with in-process mode — it works fine in any terminal.

To force a mode:

```bash
claude --teammate-mode in-process
claude --teammate-mode tmux
```

Or set permanently in `~/.claude/settings.json`:

```json
{
  "teammateMode": "in-process"
}
```

The default is `"auto"` — uses split panes if already inside a tmux session, in-process otherwise.

## How It Differs From /orchestrate

| | `/orchestrate` | `/team` |
|---|---|---|
| Architecture | Subagents report back to orchestrator | Teammates talk to each other directly |
| Communication | One-way (agent → orchestrator) | Peer-to-peer messaging |
| Coordination | Orchestrator manages everything | Shared task list, self-claiming |
| Best for | Independent tasks where only results matter | Tasks needing discussion and cross-examination |

Use `/orchestrate` when tasks are independent. Use `/team` when teammates need to share findings, challenge each other, or coordinate on shared concerns.

## Limitations

- Experimental — API may change between Claude Code versions
- One team per session (clean up before starting a new team)
- No nested teams (teammates cannot spawn their own teams)
- No session resumption for in-process teammates
- Split panes require tmux or iTerm2 (not supported in zellij, VS Code terminal, Ghostty, or Windows Terminal)
- Claude Code only — not available for Cursor, Copilot, or other tools
