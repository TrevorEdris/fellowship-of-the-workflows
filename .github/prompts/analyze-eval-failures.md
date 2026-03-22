# Analyze Eval Failures

The weekly eval run detected golden test failures. Your job is to analyze each failure, determine root cause, and propose fixes.

## Context

The eval output is in `eval-output.txt`. The JSON results are in `eval-results.json`.

## For each failed test:

1. **Read the failing skill's SKILL.md** to understand its purpose and expected behavior
2. **Read the golden test** in `skills/<name>/tests/golden.jsonl` — find the failing test case by ID
3. **Classify the failure:**
   - **Stale output** — The recorded `output` field no longer matches what the skill would produce (skill was improved, output is outdated). Fix: update the `output` field.
   - **Overly strict assertion** — The assertion is too narrow and rejects valid output. Fix: relax the assertion.
   - **Genuine regression** — The skill's behavior actually degraded. Fix: update SKILL.md to restore correct behavior.

4. **Add a learning** to `skills/<name>/learnings.md` with:
   - Today's date
   - Description of what failed and why
   - Source: `eval`
   - Status: `active`
   - Follow the format: `- [YYYY-MM-DD] <finding> — Source: eval — Status: active`

5. **Propose a fix:**
   - For stale outputs: update the `output` field in golden.jsonl with a corrected response
   - For overly strict assertions: relax the assertion in golden.jsonl
   - For genuine regressions: edit SKILL.md to fix the behavior, then update golden.jsonl if needed

## Commit convention

Make one commit per skill fixed:
```
fix(skills): <skill-name> — <what was fixed>
```

## Constraints

- Do NOT delete test cases — fix them
- Do NOT weaken assertions just to make tests pass if the skill genuinely regressed
- Keep learnings.md entries concise (one sentence)
- Max 20 entries per learnings.md (evict oldest if full)
