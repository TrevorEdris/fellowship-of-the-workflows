# Learnings: orchestrate

<!-- Staging area for skill improvement findings.
     Promote valuable learnings to SKILL.md or references/.
     Entries expire after 30 days. Max 20 active entries. -->

## Active

- [2026-04-01] Claude Code v2.1.80 added `effort` frontmatter (low/medium/high) for skills to override model effort at invocation — added `effort: high` to orchestrate frontmatter given its multi-step coordination workload. — Source: ai-changelog — Status: active
- [2026-04-01] Claude Code v2.1.83 added `initialPrompt` frontmatter for agent definitions, enabling agents to auto-submit their first turn on launch — orchestrate's Task invocation step should omit explicit startup prompts for agents that declare this field. — Source: ai-changelog — Status: active
- [2026-04-01] Claude Code v2.1.76 added `TaskCreated` hook event that fires when a subagent is spawned — could enable orchestration audit logging hooks in future. — Source: ai-changelog — Status: active
