---
name: desloppify
description: Identify and remove AI slop from code comments, documentation, and prose. Use when cleaning up AI-generated output, reviewing for AI tells, or improving signal-to-noise ratio in any text.
context: fork
agent: desloppify
allowed-tools: Bash(git:*), Grep, Glob, LS, Read, Write, Edit
argument-hint: "[code|docs|prose|review]"
---

# Desloppify

## Overview

AI-generated content regresses to statistical means: verbose comments that restate the code, defensive error handling for impossible cases, and prose stuffed with "robust", "leverage", and "it's worth noting." This skill identifies those patterns and removes them — or rewrites them to carry actual signal.

## When to Use This Skill

- After AI generates or modifies code — clean up the comments and patterns it left behind
- Before committing AI-assisted work — strip the tells
- Reviewing a PR that smells like unedited AI output
- Cleaning up documentation that reads like marketing copy
- Tightening commit messages or PR descriptions

## Modes

| Argument | Behavior |
|----------|----------|
| (none) | Auto-detect from git diff context — scan changed files, classify by type |
| `code` | Scan code files for sloppy comments and AI code patterns |
| `docs` | Scan markdown/documentation files for AI prose patterns |
| `prose` | Desloppify specific text files (commit messages, PR descriptions, READMEs) |
| `review` | Report-only — identify and classify slop without modifying files |

## Context

GIT STATUS:
```
!`git status --short`
```

RECENT CHANGES:
```
!`git diff --cached --stat 2>/dev/null || git diff --stat`
```

## Process

### Phase 1: Scan

Identify target files from git context or user specification.

**For code files:**
- Match comments against the comment slop catalog (narrator, step, obvious, section dividers, over-documented trivials, language tutorials, placeholders, apologetic, redundant type docs)
- Match code patterns against the code pattern catalog (defensive impossible-case handling, unnecessary try-catch, redundant type assertions, single-use constants, premature abstractions, speculative generality, empty catch blocks)

**For documentation/prose files:**
- Match against the prose slop catalog (filler phrases, AI vocabulary, promotional adjectives, structural tells, content-level patterns)
- Cross-reference the slop word list for specific term replacements

### Phase 2: Classify

Group findings and assign severity:

| Severity | Meaning | Action |
|----------|---------|--------|
| CRITICAL | Pure noise — zero information content | Remove entirely |
| HIGH | Restates what code, types, or context already says | Remove or reduce to essential |
| MEDIUM | Verbose but contains some signal buried in noise | Rewrite concisely |
| LOW | Stylistic preference, borderline call | Flag for human decision |

Present a summary table:
```
Category           | CRITICAL | HIGH | MEDIUM | LOW
-------------------+----------+------+--------+----
Comment slop       |        3 |    5 |      2 |   1
Code pattern slop  |        0 |    2 |      1 |   0
Prose slop         |        1 |    4 |      3 |   2
```

### Phase 3: Transform

**In `review` mode:** Stop here. Present findings with file locations and suggested fixes.

**In all other modes:**
1. Present proposed changes grouped by severity
2. **Wait for user approval before applying changes**
3. Apply transformations:
   - CRITICAL: Delete entirely
   - HIGH: Remove redundant content, keep only what types/code don't already express
   - MEDIUM: Rewrite to be concise and direct
   - LOW: Add inline comment flagging the pattern for human review
4. One logical change per edit — don't batch unrelated fixes

### Phase 4: Verify

- Confirm no meaning was lost in transformations
- Run available linters/formatters if configured
- Present before/after summary with counts per severity

## Relationship to Other Skills

This skill **complements** but does not replace:
- `writing-clearly-and-concisely` — teaches good writing principles. Desloppify **detects and removes** specific AI patterns.
- `code-review` — holistic PR review. Desloppify is a **narrow, targeted pass** for AI noise.
- `refactoring` — structural code smells. Desloppify targets **AI-characteristic** noise patterns specifically.

## Reference Files

| Reference | File | ~Tokens |
|-----------|------|---------|
| Code comment & pattern taxonomy | `references/code-slop-catalog.md` | 2,500 |
| Prose & documentation taxonomy | `references/prose-slop-catalog.md` | 2,000 |
| Word/phrase blocklist with replacements | `references/slop-word-list.md` | 800 |
| Concrete before/after transformations | `references/before-after-examples.md` | 1,500 |

**For most tasks**, the relevant catalog (code or prose) plus the word list is sufficient. Load `before-after-examples.md` when you need transformation guidance.
