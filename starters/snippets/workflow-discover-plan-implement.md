# Snippet: Discover → Plan → Implement Workflow

Add this to your CLAUDE.md to enforce a structured workflow.

---

## Workflow: Discover → Plan → Implement

### 1) Discover
- Read and analyze code without modifications
- Capture findings in `DISCOVERY.md`
- Output: Technical analysis, gaps, clarifying questions

### 2) Plan
- Create `PLAN.md` with: target files, ordered steps, risks, verification
- **Wait for explicit user approval** before implementing
- Verify claims by reading actual code—no guessing
- Call out misconceptions; tell the user when they're wrong

### 3) Implement
- Execute plan with minimal, traceable diffs
- **Branch check:** If on `main`/`master`, stop and ask before making changes
- Verify changes work (run tests, lint, build)
