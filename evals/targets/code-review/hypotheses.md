# Hypothesis Log — code-review

Institutional memory for the autoresearch loop. Each iteration appends one entry here
**before** committing the skill change, so `git revert` of a discard never erases the log.

## Two-Commit Sequence

Every iteration produces exactly two commits in this order:

1. **Log commit** — append entry below with Status: pending, commit hash TBD, deltas TBD.
   `git add evals/targets/code-review/hypotheses.md && git commit -m "log: <one-line hypothesis>"`
2. **Skill commit** — apply the actual skill change.
   `git add <variable_files> && git commit -m "<hypothesis description>"`

On discard: `git revert HEAD` (reverts only the skill commit). The log commit survives.
On keep: both commits stay. Update this file's last entry with final Status, score delta, and lesson.

## Entry Format

```
### <YYYY-MM-DD> — <one-line hypothesis>

- **Status:** pending | keep | discard
- **Commit:** <skill commit hash>
- **Score delta:** <new_score>/<max> (<new_rate>%) vs <prev_score>/<max> (<prev_rate>%) [+N or -N points]
- **Per-criterion delta:** <criterion>: PASS→FAIL, <criterion>: FAIL→PASS (or "no change")
- **Change summary:** <what was edited and why>
- **Lesson:** <what this result tells us about the skill or the eval criteria>
```

---

## Entries

### 2026-03-25 — self-verification step and safe SQL patterns

- **Status:** keep
- **Commit:** fa7269e
- **Score delta:** 48/60 (80.0%) vs 43/60 (71.7%) [+5 points]
- **Per-criterion delta:** unknown (pre-log era; per-criterion breakdown not captured)
- **Change summary:** Added a self-verification step instructing the model to re-check its output before responding, plus explicit safe-SQL patterns to reduce false positives on parameterized queries.
- **Lesson:** Verification steps and concrete negative examples both appear to help. The +5 point jump from 71.7% → 80.0% is the largest single-iteration gain observed so far. Keep building on self-verification and explicit negative examples.
