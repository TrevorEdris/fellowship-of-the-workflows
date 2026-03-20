# Team Rosters

Predefined team compositions for the `/team` skill. Each roster defines a set of teammates, their agent assignments, and a coordination strategy.

## Available Rosters

| Roster | Teammates | Best For |
|--------|-----------|----------|
| `review-team` | security-review, pragmatic-code-review, chaos-engineer | PR reviews, pre-merge audits |
| `implementation-team` | tdd-enforcer, refactoring-specialist, documentation-sync | Feature work, large refactors |
| `investigation-team` | 3x systematic-debugger | Bug hunting, root cause analysis |
| `design-team` | system-design-reviewer, chaos-engineer, pragmatic-code-review | Architecture debates before planning |
| `plan-review-team` | system-design-reviewer, chaos-engineer, scope-analyzer | Stress-test an existing PLAN.md |

## Schema

See `teams/skills/team/references/team-roster-schema.md` for the full field specification.
