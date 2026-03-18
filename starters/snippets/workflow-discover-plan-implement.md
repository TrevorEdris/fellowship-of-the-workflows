# Snippet: Question → Research → Structure → Plan → Implement Workflow

Add this to your CLAUDE.md to enforce a structured 5-phase workflow.

---

## Workflow: Question → Research → Structure → Plan → Implement

### 1) Question
- Surface design decisions as numbered options **before** reading any code
- Confirm scope, constraints, and non-goals
- Output: explicit questions with alternatives answered by user

### 2) Research
- Targeted investigation of each question from phase 1 — no broad exploration
- Each question answered with code evidence (file:line references)
- Capture findings in `DISCOVERY.md`

### 3) Structure
- Phased breakdown: what gets built in what order, dependency graph
- NOT implementation details — just sequence and dependencies
- Surface risks per phase

### 4) Plan
- Create `PLAN.md` with: target files, granular steps (2-5 min each), risks, verification per step
- **Wait for explicit user approval** before implementing
- Validate with `/plan-validator` before presenting

### 5) Implement
- Execute plan with minimal, traceable diffs
- **Branch check:** If on `main`/`master`, stop and ask before making changes
- After-action review at phase boundaries: what succeeded, what deviated, what carries forward
- Verify changes work (run tests, lint, build)
