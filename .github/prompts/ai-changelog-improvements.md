# AI Changelog — Automated Improvement

Scan AI coding tool changelogs for recent changes, then propose skill improvements.

## Step 1: Scan sources

Read `skills/ai-changelog/references/sources.md` for the curated source list.

Only scan the **Claude / Anthropic** and **Cursor** sections. For each source:
- If scan method is `WebSearch`: run a WebSearch with the specified query, scoped to the last 30 days
- If scan method is `WebFetch`: fetch the URL directly with WebFetch

Collect all findings into a list grouped by tool.

## Step 2: Fetch details

For the top 3-5 most significant findings, use WebFetch to get full details from the source page.

## Step 3: Assess project impact

Read `skills/ai-changelog/references/impact-template.md` for the assessment format.

For each significant finding:
1. Read the project's `CLAUDE.md` for context on what this project does
2. Identify which skills in `skills/` are affected by the finding
3. Read affected skill SKILL.md files
4. Assess impact using the template

## Step 4: Save briefing

Write the full briefing (scan results + impact assessments) to `skills/ai-changelog/briefings/YYYY-MM-DD.md` using today's date. Create the `briefings/` directory if it doesn't exist.

## Step 5: Add learnings

For each affected skill, append a learning entry to `skills/<name>/learnings.md`:
- Format: `- [YYYY-MM-DD] <finding> — Source: ai-changelog — Status: active`
- One sentence per entry
- Max 20 entries per file (evict oldest if full)

## Step 6: Propose SKILL.md edits

For high/medium priority findings only:
- New capability → add or update a section in the skill's SKILL.md
- Changed tool behavior → update affected instructions
- New tool feature → add reference or update workflow

## Step 7: Commit changes

One commit per skill modified:
```
feat(skills): <skill-name> — <what was updated based on ai-changelog finding>
```

Commit the briefing file separately:
```
docs(skills): save ai-changelog briefing for YYYY-MM-DD
```

## Constraints

- Only modify skills genuinely affected by a finding
- Do NOT invent findings — only act on what the scan returns
- Keep SKILL.md edits minimal and targeted
- If the scan returns nothing significant, just save the briefing and commit that alone
