# Snippet: Session Documentation

Add this to your CLAUDE.md to enable session tracking for complex tasks.

---

## Session Documentation

For non-trivial tasks, create a session directory: `.ai/sessions/YYYY-MM-DD_<description>/`

Maintain these files:
- **SESSION.md** — Log of prompts, responses, decisions made
- **DISCOVERY.md** — Technical analysis during discovery phase
- **PLAN.md** — Implementation plan awaiting approval

### Directory Examples
```
.ai/sessions/2026-01-30_PROJ-123_Add-Auth/
.ai/sessions/2026-01-30_Refactor-API-Layer/
```

### When to Create Sessions
- Multi-step implementation tasks
- Tasks spanning multiple files or components
- Debugging complex issues
- Architectural changes
