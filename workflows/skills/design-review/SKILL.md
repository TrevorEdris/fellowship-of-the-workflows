---
name: design-review
description: Conduct comprehensive design review on front-end code changes using Playwright for live browser testing. Covers visual hierarchy, accessibility (WCAG AA+), responsive design, and interaction patterns. Use when reviewing UI/UX changes before merge.
context: fork
agent: design-review
allowed-tools: Bash(git:*), Bash(gh:*), Grep, Glob, LS, Read, WebFetch, TodoWrite, mcp__playwright__browser_close, mcp__playwright__browser_resize, mcp__playwright__browser_console_messages, mcp__playwright__browser_handle_dialog, mcp__playwright__browser_evaluate, mcp__playwright__browser_file_upload, mcp__playwright__browser_install, mcp__playwright__browser_press_key, mcp__playwright__browser_type, mcp__playwright__browser_navigate, mcp__playwright__browser_navigate_back, mcp__playwright__browser_network_requests, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_snapshot, mcp__playwright__browser_click, mcp__playwright__browser_drag, mcp__playwright__browser_hover, mcp__playwright__browser_select_option, mcp__playwright__browser_tabs, mcp__playwright__browser_wait_for
---

# Design Review

Conduct a comprehensive design review of the pending front-end changes.

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

DIFF CONTENT:

```
!`gh pr diff 2>/dev/null || git diff --merge-base origin/HEAD`
```

## Prerequisites

- Playwright MCP server connected
- Live preview environment running (provide URL to agent)

## Objective

Use the design-review agent to comprehensively review the UI/UX changes above. Execute the 7-phase review process with live browser testing. Your final reply must contain the markdown report with screenshots.

## References

- `references/DESIGN_PRINCIPLES.md` — S-tier design checklist
- `references/CLAUDE_MD_SNIPPET.md` — CLAUDE.md integration guide
