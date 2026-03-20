# Agent Teams Primer

Quick reference on Claude Code Agent Teams primitives for the team lead.

## Primitives

| Primitive | Purpose |
|-----------|---------|
| **TeamCreate** | Initialize a team. Creates config at `~/.claude/teams/{name}/config.json` |
| **TaskCreate** | Define a work unit. Fields: subject, description, status, dependencies |
| **TaskUpdate** | Claim a task (pending → in_progress) or complete it (in_progress → completed). File-locked to prevent races |
| **TaskList** | Query all tasks across the team — subjects, statuses, owners |
| **SendMessage** | Direct peer-to-peer messaging. Types: `message`, `broadcast`, `shutdown_request`, `shutdown_response`, `plan_approval_response` |
| **TeamDelete** | Remove team config and task files. All teammates must be shut down first |

## Task States

```
pending ──→ in_progress ──→ completed
```

- Tasks with unresolved dependencies cannot be claimed
- When a dependency completes, blocked tasks automatically unblock

## Messaging Patterns

**Direct message** — send to one specific teammate:
- Use when relaying findings between specific teammates
- Use for plan approval responses

**Broadcast** — send to all teammates:
- Use sparingly (costs tokens in every teammate's context)
- Good for: announcing a critical finding, signaling shutdown

**Shutdown flow:**
1. Lead sends `shutdown_request` to teammate
2. Teammate responds with `shutdown_response` (approve or reject with reason)
3. Lead waits for response before cleanup

## Display Modes

| Mode | How | Navigation |
|------|-----|------------|
| In-process (default) | All teammates in one terminal | Shift+Down to cycle, Ctrl+T for task list |
| Split panes | Each teammate gets own pane | Click pane to interact; requires tmux or iTerm2 |

## Cost Model

Each teammate is a full Claude Code session with its own context window.

| Team Size | Approximate Token Usage |
|-----------|------------------------|
| 3 teammates | ~800k tokens total |
| 5 teammates | ~1.2M tokens total |

Token cost scales linearly with teammate count. Use the minimum team size that covers the task.
