# Flaky Test Management

## Detection Strategy

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
});
```

A test that passes after retry is classified as flaky. Track with:

```bash
npx playwright test --reporter=json | jq '.suites[].specs[] | select(.tests[].results[].retry > 0)'
```

## Quarantine Pattern

```typescript
test.fixme('should load dashboard within 2 seconds', async ({ page }) => {
  // QUARANTINE: Flaky due to race condition in data loading
  // Tracked: https://github.com/org/repo/issues/456
  // Quarantined: 2026-02-15
  // Root cause: Dashboard API response timing varies under load
});
```

## Root Cause Categories

| Category | Symptoms | Fix |
|----------|----------|-----|
| Race conditions | Fails on fast machines, passes on slow | Add explicit `waitFor` on state transition |
| Animation timing | Fails during CSS transitions | Use `page.waitForFunction` to check computed style |
| Shared state | Fails only when run after specific tests | Add isolation; clean state in `beforeEach` |
| Network variability | Fails on slow CI, passes locally | Increase `expect.timeout`; mock slow endpoints |
| Test data conflicts | Fails when multiple tests create same data | Use unique identifiers via factories |

## Management Rules

- Any test failing intermittently for 3+ runs: quarantine within 24 hours
- Quarantined tests: root cause within 1 sprint or delete
- Never disable retries to "hide" flakiness — fix the test or the application
