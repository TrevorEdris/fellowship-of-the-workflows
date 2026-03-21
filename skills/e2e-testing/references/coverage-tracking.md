# Coverage Tracking

## Istanbul / c8 Integration with Playwright

```typescript
// Collect V8 coverage per test
test('should track coverage for checkout flow', async ({ page }) => {
  await page.coverage.startJSCoverage();

  // ... test actions ...

  const coverage = await page.coverage.stopJSCoverage();
  const coverageData = coverage.map(entry => ({
    url: entry.url,
    ranges: entry.ranges,
    text: entry.text,
  }));
  require('fs').writeFileSync(
    `coverage/e2e-coverage-${Date.now()}.json`,
    JSON.stringify(coverageData)
  );
});
```

## Per-Feature Coverage Tracking

Track coverage by feature tag rather than code lines for E2E tests:

```typescript
test('should complete checkout @feature:checkout @priority:critical', async ({ page }) => {
  // ...
});
```

```bash
# Generate coverage report filtered by feature
npx playwright test --grep "@feature:checkout" --reporter=html
```

## Threshold Enforcement in CI

```bash
# package.json
{
  "scripts": {
    "test:coverage": "c8 --lines 80 --functions 80 --branches 70 npx playwright test"
  }
}
```

## Coverage vs. Quality

- E2E tests should target **critical user paths**, not code line coverage
- 5 well-designed E2E tests covering critical flows > 50 tests covering implementation details
- Track **behavior coverage** (AC items tested) alongside code coverage
