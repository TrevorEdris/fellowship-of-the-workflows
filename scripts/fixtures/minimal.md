---
schema: v1
date: 2026-03-10
slug: Fix-DB-Connection-Pool
---

# Session — Fix DB Connection Pool

## Prompts & Responses

### Prompt 1

User: Connection pool exhaustion in prod under load. Investigate and fix.

Response: Found default pool size of 5 is too low for peak traffic. Updated
`db.SetMaxOpenConns(25)` and `db.SetMaxIdleConns(10)`. Deployed. Exhaustion
errors resolved.

## Decisions

- **2026-03-10** — Set max open connections to 25 based on RDS instance class; revisit at next tier upgrade.
