---
name: ai-changelog
description: "Scan for new AI coding tool features and assess impact on your project. Covers Claude Code, Cursor, Copilot, Windsurf, Codex, Roo, and Goose. Use to track AI tooling changes and identify workflow improvements."
user-invocable: true
argument-hint: "[scan|briefing|impact <feature>] [--tools claude,cursor]"
effort: medium
allowed-tools: WebSearch, WebFetch, Read, Write, Grep, Glob
tags: [meta]
---

# AI Changelog

Scan AI coding tool changelogs and blogs, synthesize findings, and assess impact on your project's workflows.

---

## Tool Filtering

If the user specifies `--tools`, only scan and report on those tools. Accepts comma-separated names.

**Valid tool names:** `claude`, `cursor`, `copilot`, `windsurf`, `codex`, `roo`, `goose`

Examples:
- `/ai-changelog scan --tools claude,cursor` — only Claude Code and Cursor
- `/ai-changelog briefing --tools claude` — only Claude Code

If no `--tools` flag is provided, auto-detect from the project: look for `.claude/`, `.cursor/`, `.github/copilot-instructions.md`, etc. If nothing is detected, scan all tools.

---

## Mode Selection

Determine mode from the argument:

### 1. Scan (`/ai-changelog scan`)

Quick scan for recent AI tooling news.

1. Read `references/sources.md` for the curated source list
2. Filter to selected tools only (from `--tools` flag or auto-detected)
3. WebSearch each matching source category for posts from the last 30 days
4. Output raw findings as a bullet list, grouped by tool

### 2. Briefing (`/ai-changelog briefing`)

Full research with structured synthesis.

1. Run scan (step 1 above)
2. WebFetch the most relevant results for detail
3. Understand the project context:
   - Read the project's CLAUDE.md, README, or equivalent for an overview
   - Scan for AI workflow files (skills, rules, agents, hooks, .cursorrules, copilot instructions)
   - Identify the AI tools the project targets
4. For each significant finding, assess project impact using `references/impact-template.md`
5. Synthesize into a structured briefing:
   - **Per-tool sections** — What changed, when, significance
   - **Impact assessment** — Which project workflows are affected
   - **Recommendations** — Concrete next steps (new workflow, update existing, no action)
6. Save briefing to `briefings/YYYY-MM-DD.md`
7. Present summary to user

### 3. Impact (`/ai-changelog impact <feature>`)

Analyze a specific feature or change against the current project.

1. Scan the project for AI workflow files and configuration
2. WebSearch for details about the specified feature
3. Assess which project workflows are affected
4. Output using the impact template

---

## Agent Mode

When invoked with `--agent` flag (for GHA automation):
- Skip interactive prompts
- Run full briefing mode
- Save to `briefings/YYYY-MM-DD.md`
- Output JSON summary to stdout

---

## References

| File | Purpose |
|------|---------|
| `references/sources.md` | Curated list of changelog URLs and blogs to scan |
| `references/impact-template.md` | Template for project impact assessment |
