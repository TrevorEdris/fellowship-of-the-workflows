---
name: code-review
description: Perform thorough code review on a PR using the Pragmatic Quality framework. Integrates with Jira to validate implementation matches ticket requirements. Use when reviewing pull requests or providing PR feedback.
context: fork
agent: pragmatic-code-review
allowed-tools: Bash(git:*), Bash(gh:*), Grep, Glob, LS, Read, WebFetch, TodoWrite
---

# Code Review

Conduct a comprehensive code review of the pending changes using the Pragmatic Quality framework.

## Context

GIT STATUS:

```
!`git status`
```

PR METADATA:

```
!`gh pr view --json title,body,author,files,additions,deletions,headRefName,state 2>/dev/null || echo "No PR context - reviewing local branch"`
```

FILES MODIFIED:

```
!`gh pr diff --name-only 2>/dev/null || git diff --name-only origin/HEAD...`
```

COMMITS:

```
!`gh pr view --json commits --jq '.commits[].messageHeadline' 2>/dev/null || git log --oneline origin/HEAD...`
```

DIFF CONTENT:

```
!`gh pr diff 2>/dev/null || git diff --merge-base origin/HEAD`
```

## Jira Integration

If Atlassian MCP is connected, fetch linked ticket details and validate implementation against acceptance criteria.

## Objective

Use the pragmatic-code-review agent to comprehensively review the complete diff above. Your final reply must contain the markdown report.

## Scripts

```bash
scripts/pr-context.sh 123              # Fetch PR metadata via gh
scripts/extract-ticket-ids.sh 123      # Extract Jira IDs from PR
python scripts/diff-analysis.py --staged  # Analyze diff patterns
```

## References

- `references/REVIEW_CHECKLIST.md` — Detailed checklist
- `assets/feedback-templates.md` — Common feedback patterns
