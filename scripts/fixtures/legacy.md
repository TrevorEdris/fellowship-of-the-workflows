# Session: Add Integration Tests + Missing Service Jobs to CI

**Date:** 2026-02-14
**Branch:** phase-4-entitlements

## Prompts & Responses

### 1. Implement CI plan

- User: Implement the approved plan for CI workflow changes
- Action: Modifying `.github/workflows/ci.yml` and `.github/workflows/contracts.yml`
- Steps: Fix contracts codegen, add identity/entitlements service jobs, add integration test jobs

### 2. Fix lint failures

- User: Lint is failing on the new workflow file
- Action: Fixed YAML indentation issue in ci.yml step definitions

## Key Decisions

- Use matrix strategy for service jobs so new services can be added by adding a row
- Run integration tests only on push to main (not on every PR) to keep PR feedback fast
