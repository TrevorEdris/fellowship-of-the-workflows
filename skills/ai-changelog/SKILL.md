---
name: ai-changelog
description: "Scan for new AI coding tool features and assess FOTW impact. Covers Claude Code, Cursor, Copilot, Windsurf, Codex, Roo, and Goose. Use to track AI tooling changes and identify skill/rule/agent improvements."
user-invocable: true
argument-hint: "[scan|briefing|impact <feature>]"
allowed-tools: WebSearch, WebFetch, Read, Write, Grep, Glob
tags: [meta]
---

# AI Changelog

Scan AI coding tool changelogs and blogs, synthesize findings, and assess impact on FOTW workflows.

---

## Mode Selection

Determine mode from the argument:

### 1. Scan (`/ai-changelog scan`)

Quick scan for recent AI tooling news.

1. Read `references/sources.md` for the curated source list
2. WebSearch each source category for posts from the last 30 days
3. Output raw findings as a bullet list, grouped by tool

### 2. Briefing (`/ai-changelog briefing`)

Full research with structured synthesis.

1. Run scan (step 1 above)
2. WebFetch the most relevant results for detail
3. For each significant finding, assess FOTW impact using the template in `references/impact-template.md`
4. Read `references/fotw-inventory.md` to cross-reference current capabilities
5. Synthesize into a structured briefing:
   - **Per-tool sections** — What changed, when, significance
   - **Impact assessment** — Which FOTW skills/rules/agents are affected
   - **Recommendations** — Concrete next steps (new skill, update existing, no action)
6. Save briefing to `briefings/YYYY-MM-DD.md`
7. Present summary to user

### 3. Impact (`/ai-changelog impact <feature>`)

Analyze a specific feature or change against FOTW inventory.

1. Read `references/fotw-inventory.md`
2. WebSearch for details about the specified feature
3. Assess which FOTW workflows are affected
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
| `references/impact-template.md` | Template for FOTW impact assessment |
| `references/fotw-inventory.md` | Current FOTW capabilities summary |
