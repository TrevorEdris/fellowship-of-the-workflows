---
name: orchestrate
description: "Coordinate multiple subagents to complete a large task. Decomposes work, delegates to specialists, aggregates results, handles failures. Use for tasks spanning multiple domains or requiring parallel workstreams."
context: fork
agent: multi-agent-orchestrator
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(git status), Bash(git branch:*), Bash(gh pr view:*), Bash(gh pr diff:*), Bash(gh pr list:*), Glob, Grep, Read, Write, Task
tags: [meta]
tier: core
---

# Orchestrate

Coordinate multiple specialized agents to complete a complex, multi-faceted task that spans multiple domains or requires parallel workstreams.

## Context

AVAILABLE AGENTS (core):
```
!`ls agents/ 2>/dev/null | sed 's/\.md$//' | sort || echo "No agents found"`
```

AVAILABLE AGENTS (platforms/vendors — if installed):
```
!`{ ls platforms/agents/ 2>/dev/null; ls vendors/agents/ 2>/dev/null; } | sed 's/\.md$//' | sort 2>/dev/null || true`
```

GIT STATUS:
```
!`git status --short 2>/dev/null || echo "Not a git repo"`
```

CURRENT BRANCH:
```
!`git branch --show-current 2>/dev/null || echo "Unknown"`
```

## When to Use This Skill

Use `orchestrate` when the task:
- Spans multiple domains (e.g., code quality + security + documentation + diagrams)
- Would benefit from parallel workstreams (independent subtasks that can run concurrently)
- Is too large or complex for a single agent to handle in one pass
- Requires different specialist agents for different parts of the work

Do not use `orchestrate` for simple, single-domain tasks — invoke the appropriate specialist agent directly.

## Process

### Step 1: Intake

Parse the user's task description. Identify:
- Primary objective and definition of done
- Domains involved (code, tests, docs, security, design, infrastructure, etc.)
- Files, directories, or systems in scope
- Hard constraints and preferences

If the task description is ambiguous or underspecified, ask targeted clarifying questions before decomposing. Decomposing an unclear task wastes everyone's time.

### Step 2: Decomposition

Break the task into subtasks using the schema in [references/task-schema.md](references/task-schema.md).

Map each subtask to an available agent using [references/agent-catalog.md](references/agent-catalog.md). Cross-check against the dynamic agent list in the Context section above — the list is authoritative.

Build the dependency graph:
- Identify which subtasks are fully independent (can run in parallel)
- Identify sequential chains (B requires output from A)
- Mark the critical path (the longest dependency chain — this determines minimum elapsed time)

Decomposition quality checklist:
- [ ] Each subtask is atomic and assignable to a single agent
- [ ] Dependencies are explicit and minimal
- [ ] Independent subtasks are grouped into parallel batches
- [ ] Critical subtasks are clearly flagged
- [ ] Each subtask has specific acceptance criteria

### Step 3: Plan Approval

Present the orchestration plan to the user using [assets/orchestration-plan-template.md](assets/orchestration-plan-template.md).

Fill in the template completely:
- Objective restated in concrete terms
- Full subtask table with IDs, agents, dependencies, complexity, criticality
- ASCII DAG showing the dependency graph
- Execution batches showing what runs in parallel vs. sequentially
- Risk assessment covering known failure modes

**Wait for explicit user approval before executing.** The user may modify the plan — update it and confirm again before proceeding.

### Step 4: Execution

Execute subtasks in topological order. For each executable batch:

1. Prepare each subagent's context using the handoff format in [references/handoff-format.md](references/handoff-format.md)
   - Include task ID, title, full description, acceptance criteria
   - Include file paths and scope explicitly
   - Include summaries of completed upstream subtask outputs
   - Include current branch and repository context

2. Invoke each agent in the batch via the `Task` tool
   - For independent subtasks, invoke multiple `Task` calls in the same turn (parallel)
   - For sequential subtasks, wait for each to complete before invoking the next
   - For critical subtasks requiring deep reasoning, set `/effort xhigh` before dispatch (Opus 4.7+)

3. Collect and validate output
   - Check that output addresses the acceptance criteria
   - Note any partial completions or caveats

4. Update the status board after each batch
   - Mark each subtask: `completed` / `failed` / `partial` / `skipped`

### Step 5: Failure Handling

On failure, apply the escalation ladder in order:

1. **Retry (1x):** Re-invoke the same agent with enriched context — include the failure reason and any additional clarifying information
2. **Fallback:** If retry fails, invoke `general-purpose` as the universal fallback agent
3. **Skip:** If the subtask is non-critical and has no downstream dependents, mark it `skipped` and continue
4. **Halt:** If a critical subtask fails after retry + fallback, stop and report to the user with full context

Never absorb failures silently. Document every failure in the final report.

### Step 6: Aggregation

Produce the final report covering:
- **Executive summary**: What was accomplished, what was skipped, what failed
- **Per-subtask results**: Status, agent used, key output for every subtask
- **Modified files**: Aggregated across all subagents, deduplicated
- **Unresolved items**: Anything left incomplete, with context
- **Ship recommendation**: SHIP / NEEDS WORK / BLOCKED with rationale

## References

- [references/task-schema.md](references/task-schema.md) — Subtask and dependency graph schema
- [references/handoff-format.md](references/handoff-format.md) — Agent-to-agent context format
- [references/agent-catalog.md](references/agent-catalog.md) — Available agents and their capabilities
- [assets/orchestration-plan-template.md](assets/orchestration-plan-template.md) — Plan presentation template
