# Learnings Format

Per-skill `learnings.md` files serve as a **staging area** for skill improvement findings. Learnings are temporary — they must be promoted into the skill itself or they expire.

## Location

`skills/<name>/learnings.md`

## Format

```markdown
# Learnings: <skill-name>

<!-- Staging area for skill improvement findings.
     Promote valuable learnings to SKILL.md or references/.
     Entries expire after 30 days. Max 20 active entries. -->

## Active

- [2026-03-22] Finding description — Source: eval — Status: active
- [2026-03-15] Another finding — Source: user — Status: expiring
```

## Fields

| Field | Format | Description |
|-------|--------|-------------|
| Date | `[YYYY-MM-DD]` | When the learning was recorded |
| Finding | Free text | What was learned |
| Source | `eval`, `user`, `ai-changelog` | Where the learning came from |
| Status | `active`, `expiring` | `expiring` when >21 days old |

## Lifecycle: Promote or Die

```
New finding ──→ learnings.md (staging) ──→ Promoted to SKILL.md/references/
                     │                          ↑
                     │ 30 days, no promotion     │ Human or eval validates value
                     ↓                          │
                  Auto-removed ─────────────────┘
```

### Rules

1. Entries expire after **30 days** unless promoted
2. Hard cap of **20 active entries** per skill — when full, oldest un-promoted entry is evicted
3. Status changes to `expiring` at day 21 (gives 9-day warning window)
4. Promotion means incorporating the learning into SKILL.md or a reference file, then removing from learnings.md
5. No archive section — learnings are either promoted or deleted

### Promotion

Use `/eval promote <skill>` to interactively promote or discard learnings.

### Sources

- `eval` — Discovered during evaluation runs (regressions, new failure patterns)
- `user` — Manually added by the user during a session
- `ai-changelog` — Identified from AI tooling changes that affect this skill
