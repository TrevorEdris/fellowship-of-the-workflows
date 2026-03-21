# CI/CD Integration

## GitHub Actions Workflow

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  e2e:
    timeout-minutes: 30
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests (shard ${{ matrix.shard }}/4)
        run: npx playwright test --shard=${{ matrix.shard }}/4
        env:
          BASE_URL: ${{ secrets.STAGING_BASE_URL }}
          CI: true

      - name: Upload test artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report-shard-${{ matrix.shard }}
          path: |
            playwright-report/
            test-results/
          retention-days: 14

  merge-reports:
    if: always()
    needs: [e2e]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Download all shard reports
        uses: actions/download-artifact@v4
        with:
          pattern: playwright-report-shard-*
          merge-multiple: true
      - name: Merge reports
        run: npx playwright merge-reports --reporter html ./playwright-report
      - name: Upload merged report
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-merged
          path: playwright-report/
          retention-days: 30
```

## Artifact Configuration Guidelines

| Artifact | Upload Condition | Retention |
|----------|-----------------|-----------|
| Screenshots | Always (failure only) | 14 days |
| Videos | On failure/retry | 14 days |
| Traces | On first retry | 14 days |
| HTML report | Always | 30 days |
| JUnit XML | Always | 7 days |
