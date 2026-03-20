---
description: "Conventions for Agent Team sessions — file ownership, communication, task lifecycle"
paths:
  - "**/*"
---

## Agent Team Conventions

These conventions apply when working as part of an Agent Team (multiple Claude Code sessions coordinating via shared tasks and messaging).

### File Ownership

- Do not edit files that another teammate is actively working on
- If you need to read a file another teammate owns, that is fine — read access is shared
- If you discover you need to modify a shared file, message the owner to coordinate
- The lead assigns file ownership implicitly through task scope — respect it

### Communication Protocol

- Report significant findings to the lead via SendMessage
- When you find something relevant to another teammate's focus area, message them directly
- Respond to messages from the lead and other teammates promptly
- Use broadcast only when a finding affects the entire team

### Task Lifecycle

1. Check the task list for unclaimed pending tasks
2. Claim a task by updating its status to in_progress
3. Work on the task within its defined scope
4. When finished, update the task status to completed
5. If stuck, message the lead with what you've tried and where you're blocked

### Quality Standards

- Verify your work before marking a task complete (run tests, lint, build as applicable)
- Do not mark a task complete if you have unresolved concerns — note them in your completion message
- If a task depends on upstream work, verify the upstream output is sound before building on it

### Boundaries

- Stay within your assigned focus area — don't expand scope without lead approval
- Do not shut down without lead authorization
- Do not spawn additional teammates or nested teams
