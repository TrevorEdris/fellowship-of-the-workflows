# CLAUDE.md

## Project Overview

<!-- Describe your project in 1-2 sentences -->
<!-- Example: A React dashboard for managing customer subscriptions. -->

## Tech Stack

<!-- List your primary technologies -->
<!-- Example: TypeScript, React, Node.js, PostgreSQL -->

## Repository Map

<!-- For multi-repo workspaces, map out your repositories -->
<!--
| Repository | Purpose | Tech Stack |
|------------|---------|------------|
| `frontend` | Web application | React, TypeScript |
| `backend`  | API server | Node.js, Express |
| `shared`   | Common types/utils | TypeScript |
-->

## Build Commands

```bash
# Add your common commands here
# npm install        # Install dependencies
# npm run dev        # Start dev server
# npm test           # Run tests
# npm run lint       # Lint code
# npm run build      # Production build
```

## Workflow: Question → Research → Structure → Plan → Implement

1. **Question** — Surface design decisions as numbered options before reading any code
2. **Research** — Targeted investigation of each question; capture in `DISCOVERY.md`
3. **Structure** — Phased breakdown with dependency graph; NOT implementation steps
4. **Plan** — Granular steps (2-5 min each) with file paths and per-step verification; wait for approval
5. **Implement** — Execute plan; after-action review at phase boundaries

## Session Documentation

For non-trivial tasks, create a session directory: `.ai/sessions/YYYY-MM-DD_<description>/`

Maintain these files:
- **SESSION.md** — Log of prompts, responses, decisions made
- **DISCOVERY.md** — Technical analysis during research phase
- **PLAN.md** — Implementation plan awaiting approval

