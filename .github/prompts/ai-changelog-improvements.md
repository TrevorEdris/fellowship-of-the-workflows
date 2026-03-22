# AI Changelog — Automated Improvement

Run the ai-changelog skill to scan for recent AI tooling changes and propose skill improvements.

## Steps

1. **Run the scan.** Use `/ai-changelog briefing --tools claude,cursor`. This scans Anthropic and Cursor changelogs for the last 30 days.

2. **Save the briefing.** Write the output to `skills/ai-changelog/briefings/YYYY-MM-DD.md` using today's date.

3. **Assess impact on existing skills.** For each finding with high or medium priority:
   - Identify which skills in `skills/` are affected
   - Read the affected skill's SKILL.md

4. **Add learnings.** For each affected skill, add a learning entry to `skills/<name>/learnings.md`:
   - Format: `- [YYYY-MM-DD] <finding> — Source: ai-changelog — Status: active`
   - Keep entries concise (one sentence)
   - Max 20 entries per file (evict oldest if full)

5. **Propose SKILL.md edits.** For high/medium priority findings:
   - If a new capability should be documented: add a section or update an existing one
   - If a tool changed behavior that affects the skill: update instructions
   - If a new tool feature could improve the skill: add a reference or update the workflow

6. **Commit changes.** One commit per skill modified:
   ```
   feat(skills): <skill-name> — <what was updated based on ai-changelog finding>
   ```
   Commit the briefing file separately:
   ```
   docs(skills): save ai-changelog briefing for YYYY-MM-DD
   ```

## Constraints

- Only modify skills that are genuinely affected by a finding
- Do NOT invent findings — only act on what the scan returns
- Keep SKILL.md edits minimal and targeted
- If the scan returns nothing significant, just save the briefing and commit that alone
