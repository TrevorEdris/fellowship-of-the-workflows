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

Review the complete diff above. Your final reply MUST contain the structured markdown report below. Every real issue must be found. Every finding must cite a specific file and line.

### Review Checklist

Scan the diff for each of these in order. If found, report it at the listed severity.

**CRITICAL — must block merge:**
- SQL injection: string interpolation/f-strings in SQL queries (e.g., `f"SELECT ... WHERE x = '{user_input}'"`)
- XSS: `dangerouslySetInnerHTML` with user-supplied data, unescaped user input rendered as HTML
- Dangerous migrations: `ALTER TABLE ... ADD COLUMN` without `NOT NULL DEFAULT` on tables with existing rows — this breaks existing data
- Command injection, SSRF, path traversal

**HIGH — strong recommendation to fix:**
- Missing input validation (no format/type checks on user-supplied parameters)
- Non-constant-time password/token comparison (using `==` instead of `hmac.compare_digest` or equivalent)
- Unsafe cryptographic patterns

**MEDIUM — should fix:**
- Missing React `key` prop on list items
- Incomplete API documentation (new endpoint parameters not documented, missing response field descriptions)

**LOW — optional:**
- Style nits, naming suggestions, minor improvements
- Process concerns like vague/empty PR descriptions (note these in Recommendations, not as code bugs)

### False Positive Avoidance (CRITICAL — read carefully)

Before flagging ANY issue, verify it is a real bug, not one of these false positives:

**NEVER flag as issues:**
- `import hashlib` when the code uses `hashlib.sha256` — correct standard library usage, not "weak hashing"
- `async` keyword on a Flask route — valid Python syntax, not a bug
- Inline style objects with dynamic computed values in React (e.g., conditional colors based on state) — this is idiomatic React, not "should be CSS"
- Parameterized SQL queries using `%s` placeholders — this is SAFE, not SQL injection. Only flag string interpolation/f-strings in queries.
- Clean, well-structured code — do NOT invent problems that don't exist

**When code is correct:** Say so. A review that finds no bugs is a valid, good outcome. Do not manufacture findings to seem thorough. If a PR is a clean refactor that improves code quality, acknowledge that explicitly and keep findings empty.

**When only some files have issues:** Only flag issues in files that actually have bugs. If a PR has one problematic file and three clean files, do not invent issues in the clean files.

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
