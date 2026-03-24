# systematic-debugging

Structured root-cause analysis that prevents brute-force debugging loops.

## Usage

```
/debug                              # Start systematic debugging on current issue
```

## When to Use

- A test is failing and you don't know why
- Unexpected behavior that retry/tweak cycles haven't fixed
- You've tried 2+ fixes and the issue persists
- Need to investigate before proposing any fix

## What It Does

- Four-phase methodology: investigate, analyze patterns, hypothesize, implement fix
- Will not propose fixes until root cause is confirmed with evidence
- Produces actionable root-cause statements: "The bug occurs because [X] causes [Y] when [Z]"

## References

- `references/anti-patterns.md` — Debugging anti-patterns to avoid
- `references/debugging-log-template.md` — Structured investigation log
- `references/defense-in-depth.md` — Preventing recurrence
- `references/root-cause-tracing.md` — Tracing methodology
