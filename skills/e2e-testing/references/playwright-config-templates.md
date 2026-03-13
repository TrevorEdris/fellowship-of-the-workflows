# Playwright Configuration Templates

Ready-to-use `playwright.config.ts` templates for common project setups.

---

## Minimal Config

Single browser, HTML reporter, no retries. Use for local development or small projects.

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: ['**/*.e2e.test.ts', '**/*.integration.test.ts'],
  timeout: 30_000,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    trace: 'off',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

**When to use:** Bootstrapping a new project; local-only test runs; single-browser coverage is sufficient.

---

## Standard Config

Three browsers, HTML + JUnit reporters, 2 retries on CI, screenshots on failure. This is the recommended default for most projects.

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

const isCI = !!process.env.CI;

export default defineConfig({
  testDir: './tests',
  testMatch: ['**/*.e2e.test.ts', '**/*.integration.test.ts'],
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 2 : undefined,
  timeout: 30_000,
  expect: { timeout: 5_000 },

  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    isCI ? ['github'] : ['list'],
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],

  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !isCI,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
```

**When to use:** Production applications; projects with CI pipelines; cross-browser coverage required.

---

## Full CI Config

Three browsers + mobile viewports, all reporters, sharding, `webServer`, global setup/teardown. Use when you need maximum coverage and CI performance.

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

const isCI = !!process.env.CI;

export default defineConfig({
  testDir: './tests',
  testMatch: ['**/*.e2e.test.ts', '**/*.integration.test.ts'],
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 1 : undefined,
  timeout: 60_000,
  expect: { timeout: 10_000 },

  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['json', { outputFile: 'test-results/results.json' }],
    isCI ? ['github'] : ['list'],
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'on',            // Screenshots on ALL tests, not just failures
    video: 'retain-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
    // Global auth state (if using a shared logged-in state)
    // storageState: 'tests/.auth/user.json',
  },

  projects: [
    // Setup project (runs auth once, shares state)
    {
      name: 'setup',
      testMatch: /global\.setup\.ts/,
    },

    // Desktop browsers
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      dependencies: ['setup'],
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
      dependencies: ['setup'],
    },

    // Mobile viewports
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
      dependencies: ['setup'],
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
      dependencies: ['setup'],
    },
  ],

  webServer: {
    command: 'npm run start:test',
    url: 'http://localhost:3000',
    reuseExistingServer: !isCI,
    timeout: 120_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },

  globalSetup: './tests/global.setup.ts',
  globalTeardown: './tests/global.teardown.ts',
});
```

**When to use:** Large-scale projects; mobile coverage required; authentication state shared across tests; test sharding across CI runners.

---

## Config Option Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `testDir` | string | — | Root directory for test files |
| `testMatch` | string[] | `**/*.{test,spec}.{js,ts}` | Glob patterns for test files |
| `timeout` | number | 30000 | Per-test timeout in ms |
| `expect.timeout` | number | 5000 | Assertion auto-wait timeout in ms |
| `retries` | number | 0 | Number of retries on failure |
| `workers` | number | CPU count / 2 | Parallel worker count |
| `fullyParallel` | boolean | false | Run tests across files in parallel |
| `forbidOnly` | boolean | false | Fail if `.only` is used (set to `true` in CI) |
| `reporter` | string | `list` | Reporter type(s) |
| `use.baseURL` | string | — | Default URL prefix for `page.goto('/')` |
| `use.trace` | string | `off` | `off`, `on`, `on-first-retry`, `retain-on-failure` |
| `use.screenshot` | string | `off` | `off`, `on`, `only-on-failure` |
| `use.video` | string | `off` | `off`, `on`, `retain-on-failure`, `on-first-retry` |
| `use.actionTimeout` | number | 0 (inherits) | Timeout for each action (click, fill, etc.) |
| `use.navigationTimeout` | number | 0 (inherits) | Timeout for page navigation |
| `webServer.command` | string | — | Command to start the app under test |
| `webServer.url` | string | — | URL to poll until server is ready |
| `webServer.reuseExistingServer` | boolean | false | Reuse existing server if running |
| `globalSetup` | string | — | Path to global setup module |
| `globalTeardown` | string | — | Path to global teardown module |

---

## Environment Variable Conventions

```bash
# .env.test (never commit — add to .gitignore)
BASE_URL=http://localhost:3000
CI=false
PLAYWRIGHT_BROWSERS_PATH=0  # Use local install

# GitHub Actions secrets
BASE_URL=https://staging.yourapp.com
CI=true
```

```typescript
// Access in config
baseURL: process.env.BASE_URL || 'http://localhost:3000',
```

---

## Common Gotchas

| Gotcha | Explanation | Fix |
|--------|-------------|-----|
| `workers: 1` in CI | Prevents port conflicts when webServer is used | Always set `workers: 1` when using `webServer` in CI |
| `forbidOnly: true` in CI | Prevents accidentally merging `test.only` calls | Always set this for CI environments |
| `reuseExistingServer: false` in CI | CI must start a fresh server; local dev can reuse | Set to `!process.env.CI` |
| `screenshot: 'on'` vs `'only-on-failure'` | `'on'` captures all tests (large storage); `'only-on-failure'` is preferred for CI | Use `'only-on-failure'` unless debugging specific flows |
| Missing `dependencies` in multi-project | Auth setup runs in parallel with tests | Use `dependencies: ['setup']` on all projects that need auth |
