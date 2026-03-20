# Agent Teams

Coordinate multiple Claude Code sessions working together as a team. One session leads, the rest are specialist teammates that communicate directly with each other through shared tasks and messaging.

Agent Teams are Claude Code only. They require Claude Code v2.1.32+ and are experimental.

## Prerequisites

- Claude Code v2.1.32 or later (`claude --version`)
- FOTW plugin or install-mode already set up
- tmux recommended for split-pane mode (not required — in-process mode works in any terminal)

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

### Examples

```
/team review PR#142
/team review "the auth module changes in src/auth/"
/team implementation "add OAuth2 support to the auth module"
/team investigation "app exits after one message instead of staying connected"
```

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

| Mode | Terminal | Navigation |
|------|----------|------------|
| In-process (default) | Single terminal | Shift+Down to cycle teammates, Ctrl+T for task list |
| Split panes | One pane per teammate | Click pane to interact; requires tmux or iTerm2 |

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

## Cost Guidance

Each teammate is a full Claude Code session with its own context window. Token usage scales linearly.

| Preset | Teammates | Approximate Tokens | Notes |
|--------|-----------|-------------------|-------|
| Review | 3 | ~800k | Cheapest — read-only analysis, shorter sessions |
| Implementation | 3 | ~1M+ | Most expensive — full code generation per teammate |
| Investigation | 3 | ~800k | Medium — read-heavy with some experimentation |

**Tips:**
- Review preset uses Opus for all teammates (high-judgment work). Consider Sonnet for lower-stakes reviews.
- Implementation preset uses Sonnet teammates by default. This is intentional — standard tasks don't need Opus.
- The lead always runs on Opus regardless of preset.

## How It Differs From /orchestrate

| | `/orchestrate` | `/team` |
|---|---|---|
| Architecture | Subagents report back to orchestrator | Teammates talk to each other directly |
| Communication | One-way (agent → orchestrator) | Peer-to-peer messaging |
| Coordination | Orchestrator manages everything | Shared task list, self-claiming |
| Token cost | Lower (~440k for 3 agents) | Higher (~800k for 3 teammates) |
| Best for | Independent tasks where only results matter | Tasks needing discussion and cross-examination |

Use `/orchestrate` when tasks are independent. Use `/team` when teammates need to share findings, challenge each other, or coordinate on shared concerns.

## Limitations

- Experimental — API may change between Claude Code versions
- One team per session (clean up before starting a new team)
- No nested teams (teammates cannot spawn their own teams)
- No session resumption for in-process teammates
- Split panes require tmux or iTerm2 (not supported in VS Code terminal or Ghostty)
- Claude Code only — not available for Cursor, Copilot, or other tools
