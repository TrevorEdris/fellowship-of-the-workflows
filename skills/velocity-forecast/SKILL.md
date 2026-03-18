---
name: velocity-forecast
description: "Analyze GitHub velocity and technical debt trends. Forecasts sprint bottlenecks and tracks debt accumulation. Use for sprint planning, retros, or health checks."
tags: [meta]
allowed-tools: Bash(git log:*), Bash(git shortlog:*), Bash(git rev-list:*), Bash(git branch:*), Bash(gh api:*), Bash(gh pr list:*), Bash(gh repo view:*), Grep, Glob, Read
---

# Velocity Forecast

Analyze project velocity, technical debt trends, and sprint health.

## Context

REPO INFO:
```
!`gh repo view --json name,owner,defaultBranchRef --jq '"\(.owner.login)/\(.name) (default: \(.defaultBranchRef.name))"' 2>/dev/null || echo "Not a GitHub repo"`
```

RECENT VELOCITY (last 8 weeks — PRs merged per week):
```
!`scripts/github-velocity.sh 2>/dev/null || echo "Run from skill directory or install scripts"`
```

TECH DEBT SNAPSHOT:
```
!`scripts/debt-tracker.sh 2>/dev/null || echo "Run from skill directory or install scripts"`
```

CONTRIBUTOR ACTIVITY (last 30 days):
```
!`git shortlog -sn --since="30 days ago" 2>/dev/null || echo "No git history"`
```

OPEN PR AGE:
```
!`gh pr list --json number,title,createdAt --jq '.[] | "\(.number)\t\(.title)\t\(.createdAt)"' 2>/dev/null | head -20 || echo "No open PRs"`
```

## Analysis

Using the data above, provide:

### 1. Velocity Trend
- PRs merged per week over the last 8 weeks
- Trend direction: accelerating, stable, or decelerating
- If decelerating, identify likely causes from the data

### 2. Technical Debt Assessment
- Current TODO/FIXME/HACK count
- Debt density (comments per 1K lines of code)
- Top 5 files by debt comment count

### 3. Sprint Health Indicators
- Average open PR age (flag if >3 days)
- Contributor distribution (flag bus factor <2)
- Merge frequency pattern (steady vs bursty)

### 4. Forecast
- Based on current velocity trend, project completion estimates for open issues
- Identify bottleneck risks for the next 2 weeks
- Recommend 1-2 actionable improvements

## References

- `references/metrics-guide.md` — Metric definitions and interpretation
- `references/bottleneck-patterns.md` — Common bottleneck patterns and mitigations
