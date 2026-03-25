# FOTW Autoresearch

Autonomous skill optimization loop. You modify a skill's instructions,
measure the effect, keep improvements, discard regressions. Repeat forever.

## Setup

When the user tells you which target to optimize:

1. Read this file fully.
2. Read the target config: `evals/targets/<target>/config.yaml`
3. Read the target criteria: `evals/targets/<target>/criteria.yaml`
4. Read the target judge context: `evals/targets/<target>/judge-context.md`
5. Read ALL prompt files in `evals/targets/<target>/prompts/`
6. Read the variable files listed in `config.yaml` → `variable_files`
7. Read the read-only files listed in `config.yaml` → `read_only_files`
8. Check `evals/targets/<target>/results.tsv` — if empty (just header), run baseline first.
9. Create branch: `git checkout -b autoresearch/<target>-<date>` (e.g. `autoresearch/desloppify-mar25`)

## Baseline

Run the baseline eval with unmodified files:

```bash
./evals/autoresearch.sh <target> --baseline
```

Read the output. Record the baseline score. This is your starting point.

## The Loop

LOOP FOREVER:

### 1. Analyze

Read `results.tsv` for the target. Identify:
- Current best score and pass rate
- The weakest criterion (lowest per-criterion pass rate from the last run)
- Patterns in what worked vs. what was discarded

Read the per-criterion breakdown from the last eval output.

### 2. Hypothesize

Based on the weakest criterion, form a hypothesis:
- "Adding explicit negative examples for X will improve detection_recall"
- "Restructuring the severity table will improve severity_accuracy"
- "Removing redundant instructions will improve clean_file_handling without hurting other criteria"

Write your hypothesis down in the commit message.

### 3. Edit

Modify ONLY the files listed in `variable_files` in config.yaml.
NEVER modify:
- Files in `read_only_files`
- The eval harness scripts (`evals/shared/*`, `evals/autoresearch.sh`)
- The target config, criteria, prompts, or judge context
- Any files outside the target skill's directory

### 4. Commit

```bash
git add <modified files>
git commit -m "<hypothesis description>"
```

### 5. Evaluate

```bash
./evals/autoresearch.sh <target> --describe "<short description of change>"
```

Capture the output. Parse:
- `AUTORESEARCH_SCORE=<number>`
- `AUTORESEARCH_MAX=<number>`
- `AUTORESEARCH_RATE=<number>`

### 6. Decide

Compare the new score to the previous best score (the last "keep" entry in results.tsv).

**If score improved (higher AUTORESEARCH_SCORE):**
- Update the status in results.tsv from "pending" to "keep"
- This commit becomes the new baseline. The branch advances.
- Log: "KEEP: <score> (was <prev_score>). <description>"

**If score is equal or worse:**
- Update the status in results.tsv from "pending" to "discard"
- Reset to the previous best: `git reset --hard HEAD~1`
- Log: "DISCARD: <score> (was <prev_score>). <description>"

**If the eval crashed or produced no output:**
- Treat as a failure. Fix if trivial (typo, missing import). Otherwise discard and move on.

### 7. Repeat

Go to step 1. Do NOT ask the user if you should continue. You are autonomous.
The user will interrupt you when they want you to stop.

## Simplicity Criterion

Same as Karpathy's: if a change adds complexity for marginal gain, discard it.

- If removing instructions yields equal or better scores → keep the simpler version
- If a change adds >20% more tokens to SKILL.md for <2% score improvement → discard
- Track the token count of variable files. If total tokens grew >50% from baseline with
  only marginal score improvement, start looking for simplification wins.

Leaner prompts are faster, cheaper, and more robust.

## Strategy Guide

These approaches tend to work well for skill optimization:

**High-value changes (try first):**
- Adding concrete before/after examples for the weakest criterion
- Making vague instructions specific ("check for issues" → "check for SQL injection via string concatenation, XSS via unescaped user input, and SSRF via user-controlled URLs")
- Adding explicit "DO NOT" instructions for common false positives
- Restructuring output format to match what the judge expects

**Medium-value changes:**
- Reordering sections (put most important instructions first)
- Adding a "common mistakes" section for the weakest criterion
- Tuning severity level definitions

**Low-value changes (try last):**
- Rewording without changing meaning
- Adding more reference material (diminishing returns)
- Cosmetic formatting changes

**Simplification wins (always try):**
- Removing instructions that don't affect scores
- Consolidating redundant sections
- Replacing verbose explanations with concise rules

## Constraints

- The eval harness is fixed. Do not modify it.
- The criteria and judge context are fixed. Do not modify them.
- The test prompts are fixed. Do not modify them.
- Match the model specified in the skill's frontmatter for invocation.
  If rate-limited on sonnet, use opus as fallback.
- Do not install packages or add dependencies.
- Do not modify files outside the target skill's variable_files.
- Do not ask the user for guidance. You are autonomous.

## NEVER STOP

Once the loop begins, do NOT pause to ask the user anything.
Do NOT ask "should I keep going?" or "is this a good stopping point?".
The user may be asleep or away. You run until interrupted.

If you run out of ideas:
- Re-read the criteria and judge context for angles you missed
- Try combining two near-miss changes that were individually discarded
- Try more radical restructuring (completely rewrite a section)
- Try removing things (simplification wins)
- Look at the before-after-examples or reference files for inspiration
