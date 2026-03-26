---
name: code-review
description: Perform thorough code review on a PR using the Pragmatic Quality framework. Integrates with Jira to validate implementation matches ticket requirements. Use when reviewing pull requests or providing PR feedback.
context: fork
agent: pragmatic-code-review
model: opus
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(git status), Bash(git branch:*), Bash(gh pr view:*), Bash(gh pr diff:*), Grep, Glob, LS, Read, WebFetch, TodoWrite
tags: [review]
tier: core
---

# Code Review

Review the pending changes using the Pragmatic Quality framework.

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

Review the complete diff above. Your final reply MUST contain the structured markdown report below.

### Rule 1: Do Not Invent Problems (MOST IMPORTANT)

A great code review finds real bugs AND avoids false alarms. You MUST NOT:
- Flag correct code as buggy
- Invent issues in clean, well-structured code to seem thorough
- Flag things that look suspicious but are actually correct

**These are NOT bugs — do not flag them:**
- `import hashlib` when `hashlib.sha256` is used → correct standard library usage
- `async` on a route handler → valid Python syntax
- Inline React style objects with dynamic/computed values → idiomatic React, not "should be CSS"
- Parameterized SQL with `%s` placeholders → SAFE, not SQL injection
- Well-structured refactors that improve code quality → acknowledge as clean

**If the code is clean, say so.** A review that correctly finds zero bugs is better than one that manufactures findings. Only report issues you can justify with a specific exploit scenario or concrete failure mode.

### Rule 2: Find Real Issues

Scan the diff for these specific patterns at the listed severity:

**CRITICAL:**
- SQL injection via string interpolation/f-strings in queries (e.g., `f"SELECT ... WHERE x = '{input}'"`)
- XSS via `dangerouslySetInnerHTML` with user-supplied data
- Dangerous migrations: `ALTER TABLE ADD COLUMN` without `NOT NULL DEFAULT` on existing tables — breaks existing rows
- Command injection, SSRF, path traversal

**HIGH:**
- Missing input validation on user-supplied parameters
- Non-constant-time password comparison (using `==` instead of `hmac.compare_digest`)

**MEDIUM:**
- Missing React `key` prop on list items
- Incomplete API documentation (new endpoint with undocumented parameters)

**LOW:**
- Style nits, naming suggestions
- Process concerns (vague PR descriptions) go in Recommendations, not Findings

### Rule 3: Verify Before Reporting

For each finding, confirm: (1) the issue exists in the actual code shown, (2) it has a real consequence, (3) you can cite the exact file and line. Delete any finding that fails this check.

### Output Requirements

Every finding MUST include:
- **Exact file and line:** e.g., `auth_service.py:18` or quote the specific code snippet
- **Concrete fix:** Show corrected code or describe the exact change. Never say "consider improving security" — say exactly what to change.

### Required Report Format

```markdown
### Code Review Summary
[1-3 sentence overall assessment. State if code is clean or has issues.]

### Findings

#### Critical
- **file.ext:line** — [Description: what the vulnerability is, why it's dangerous]
  - Fix: [exact code change or specific action]

#### High
- **file.ext:line** — [Description and engineering rationale]
  - Fix: [exact code change or specific action]

#### Medium
- **file.ext:line** — [Description and rationale]
  - Fix: [exact code change or specific action]

#### Low
- **file.ext:line** — [Minor observation]

### Recommendations
[Architecture, process, or documentation suggestions. Vague PR descriptions go here.]
```

Omit severity sections with no findings. If the code is clean, state that in the summary and omit the Findings section entirely.
