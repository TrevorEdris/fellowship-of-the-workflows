---
name: e2e-testing
description: Scaffold E2E and integration tests using Playwright. Covers Page Object Model setup, test data management, configuration generation, coverage tracking, and CI/CD integration. Use when creating new test suites, adding E2E coverage to features, or setting up Playwright from scratch.
tags: [testing]
---

# E2E / Integration Testing

---

## Quick Start

Just describe the feature or flow you want tested:

```
scaffold e2e tests for user checkout flow
```

You'll get a complete test structure like:

```typescript
// checkout.e2e.test.ts

// AC: User can complete purchase with a saved payment method
// Behavior: User adds item to cart -> Proceeds to checkout -> Confirms order -> Order confirmation displays
// @category: e2e
// @complexity: high
// ROI: 9

import { test, expect } from '@playwright/test';
import { CheckoutPage } from '../page-objects/CheckoutPage';
import { createUser, createProduct } from '../factories';

test('should display order confirmation when user completes checkout with saved card', async ({ page }) => {
  // Arrange
  const user = await createUser({ hasSavedCard: true });
  const product = await createProduct({ inStock: true });
  const checkout = new CheckoutPage(page);

  // Act
  await checkout.addToCart(product.id);
  await checkout.proceedToCheckout();
  await checkout.confirmOrderWithSavedCard();

  // Assert
  await expect(checkout.confirmationHeading).toBeVisible();
  await expect(checkout.orderIdText).toHaveText(/ORD-\d+/);
});
```

**What to include in your request:**
- The feature or user flow (e.g., "user login", "product search", "checkout")
- Application type (web app, API, mobile web)
- Existing test infrastructure (existing Playwright config, page objects already defined)
- Any specific acceptance criteria or edge cases to cover

---

## Triggers

| Trigger | Example |
|---------|---------|
| `scaffold e2e tests` | "scaffold e2e tests for the password reset flow" |
| `add integration tests` | "add integration tests for the payment API" |
| `set up Playwright` | "set up Playwright from scratch for our Next.js app" |
| `write tests for` | "write tests for the admin user management page" |
| `create page object` | "create a page object for the settings page" |
| `add test coverage` | "add e2e test coverage to the checkout feature" |
| `generate playwright config` | "generate a playwright config with CI support" |
| `review test coverage` | "review test coverage for the auth module" |

---

## Key Terms

| Term | Definition |
|------|------------|
| **E2E test** | Tests the complete user journey through the deployed application via a real browser |
| **Integration test** | Tests multiple components together (e.g., service + database) without full browser stack |
| **POM** | Page Object Model — encapsulates page interactions behind a typed class |
| **Test fixture** | Pre-configured test environment state (test user, seeded database, mocked API) |
| **Test factory** | Builder function that generates typed test data with sensible defaults and overrides |
| **AAA** | Arrange-Act-Assert — the three sections every test must have, clearly separated |
| **Flaky test** | A test that fails intermittently without code changes — a reliability liability |
| **Test isolation** | Each test runs independently with no shared mutable state from other tests |
| **data-testid** | `data-testid="submit-button"` — stable HTML attribute used as a selector anchor |
| **Test budget** | Deliberate limit on how many tests per feature to maintain ROI and speed |

---

## Quick Reference

| Task | Approach | Key Consideration |
|------|----------|-------------------|
| New feature coverage | Write 1-2 E2E + max 3 integration | Prefer unit tests for logic, E2E for critical paths |
| Set up from scratch | Generate `playwright.config.ts` first | Choose reporters before writing tests |
| Page interactions | Create Page Object class | One POM per distinct page or component group |
| Test data | Use factory functions with overrides | Never hardcode production data |
| CI pipeline | Add GitHub Actions workflow | Shard across runners for speed |
| Flaky test | Quarantine, root cause, fix or delete | Never skip — flaky tests erode trust |
| Coverage gaps | Run `playwright show-report` + trace | Focus on user-facing behavior, not code lines |
| API testing | Use `page.route()` interception | Mock at the network boundary, not the module |

---

## Process Overview

```
Your Feature or Flow Description
    |
    v
+-----------------------------------------------------+
| Phase 1: ANALYZE                                    |
| * Identify critical user flows (by business value)  |
| * Determine test type: E2E vs integration           |
| * Assess existing coverage to avoid duplication     |
| * Identify test data needs and API dependencies     |
+-----------------------------------------------------+
    |
    v
+-----------------------------------------------------+
| Phase 2: SCAFFOLD                                   |
| * Generate playwright.config.ts                     |
| * Create Page Object class(es)                      |
| * Set up test data factories / fixture files        |
| * Create test file structure with skeleton comments |
+-----------------------------------------------------+
    |
    v
+-----------------------------------------------------+
| Phase 3: IMPLEMENT                                  |
| * Write tests following strict AAA pattern          |
| * Behavior-first assertions (observable outcomes)   |
| * 1-2 E2E tests per feature (high ROI flows only)  |
| * Max 3 integration tests per feature               |
+-----------------------------------------------------+
    |
    v
+-----------------------------------------------------+
| Phase 4: HARDEN                                     |
| * Add CI/CD GitHub Actions workflow                 |
| * Configure artifacts: screenshots always,          |
|   video/traces on failure only                      |
| * Set coverage thresholds                           |
| * Add flaky test detection via retry counts         |
+-----------------------------------------------------+
    |
    v
Test Suite Ready for Merge
```

---

## Commands

| Command | When to Use | Action |
|---------|-------------|--------|
| `scaffold tests for {feature}` | Starting coverage for a feature | Full test file + POM + factory |
| `add page object for {page}` | Page lacks a POM class | Typed POM with fixture integration |
| `generate playwright config` | No config exists | Config for dev/CI environments |
| `review test coverage` | Pre-merge audit | Coverage report + gap analysis |
| `add ci workflow` | No CI pipeline for tests | GitHub Actions with sharding |
| `quarantine flaky test {name}` | Test fails intermittently | Isolation wrapper + tracking comment |

---

## Core Principles

| Principle | Why | Implementation |
|-----------|-----|----------------|
| **Test budget discipline** | Slow suites get skipped | Max 1-2 E2E + 3 integration per feature |
| **Behavior-first** | Tests should describe user outcomes | Assert on visible state, not internal data |
| **ROI-driven selection** | Not all paths deserve E2E | Score by risk × frequency of user path |
| **Test pyramid** | Unit tests are cheaper and faster | Unit for logic, integration for wiring, E2E for UX |
| **AAA pattern** | Clarity and reviewability | Explicit Arrange/Act/Assert comments in each test |
| **Test isolation** | Prevent cascading failures | No shared mutable state; clean up in afterEach |
| **No hardcoded waits** | Timing-based failures are flaky | Use Playwright auto-wait or explicit `waitFor*` |
| **data-testid selectors** | UI refactors break CSS selectors | Add `data-testid` to all interactive elements |
| **Artifact-rich failures** | Debugging blind is slow | Screenshots always; video/traces on retry |
| **Flakiness management** | Flaky tests cost more than no tests | Detect, quarantine, root-cause, fix or delete |

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Testing implementation details | Tests break on refactors | Assert observable behavior and UI state |
| Shared mutable test state | Tests fail depending on order | Reset state in `beforeEach`; use isolated users |
| `page.waitForTimeout(3000)` | Time-based waits are always flaky | `await expect(locator).toBeVisible()` |
| CSS class selectors in tests | Class names change with styling | `data-testid` or ARIA role selectors |
| Testing too many behaviors per test | Failures are ambiguous | One behavior assertion per test |
| Skipping cleanup after tests | State leaks into subsequent tests | Use `afterEach` to clean up created data |
| Ignoring flaky tests | They erode trust in the entire suite | Quarantine immediately; investigate within 1 sprint |
| Over-mocking | You're testing the mock, not the app | Mock at network boundary; avoid module-level mocks |

---

## Test Skeleton Specification

Every generated test file must include these structured comments for traceability:

```typescript
// AC: <exact acceptance criterion text from ticket or spec>
// Behavior: <User Action / Trigger> -> <System Process> -> <Observable Result>
// @category: e2e | integration
// @complexity: low | medium | high
// ROI: <1-10 score: risk × user path frequency>
```

**Examples:**

```typescript
// AC: User receives email confirmation within 60 seconds of completing checkout
// Behavior: User submits order -> System sends confirmation email -> User sees success banner
// @category: e2e
// @complexity: medium
// ROI: 8

// AC: Invalid credit card numbers are rejected with a user-visible error
// Behavior: User enters invalid card -> Payment processor rejects -> Error message displays below card field
// @category: integration
// @complexity: low
// ROI: 7
```

---

## File Naming Conventions

| File Type | Naming Pattern | Location |
|-----------|---------------|----------|
| E2E test | `{feature}.e2e.test.ts` | `tests/e2e/` |
| Integration test | `{feature}.integration.test.ts` | `tests/integration/` |
| Page Object | `{PageName}Page.ts` | `tests/page-objects/` |
| Factory | `{entity}.factory.ts` | `tests/factories/` |
| Fixture file | `{entity}.fixture.json` | `tests/fixtures/` |
| Global setup | `global.setup.ts` | `tests/` |
| Global teardown | `global.teardown.ts` | `tests/` |

**Directory structure:**

```
tests/
├── e2e/
│   ├── auth.e2e.test.ts
│   └── checkout.e2e.test.ts
├── integration/
│   ├── payment-api.integration.test.ts
│   └── user-service.integration.test.ts
├── page-objects/
│   ├── LoginPage.ts
│   └── CheckoutPage.ts
├── factories/
│   ├── user.factory.ts
│   └── product.factory.ts
├── fixtures/
│   └── products.fixture.json
├── global.setup.ts
└── global.teardown.ts
```

---

## Verification Checklist

After scaffolding tests:

- [ ] All tests follow AAA pattern with explicit section comments
- [ ] Each test has a skeleton comment block (AC, Behavior, @category, @complexity, ROI)
- [ ] Test file names match naming convention (`*.e2e.test.ts` / `*.integration.test.ts`)
- [ ] Page objects exist for all page-level interactions
- [ ] No `page.waitForTimeout()` or `sleep()` calls present
- [ ] All selectors use `data-testid` or ARIA roles (no CSS classes or XPath)
- [ ] Test data uses factories or fixtures (no hardcoded production data)
- [ ] `afterEach` cleanup is present for any created database records or state
- [ ] Playwright config includes screenshot on failure, traces on retry
- [ ] CI workflow artifact upload is configured with retention policy
- [ ] Feature stays within test budget (max 2 E2E, max 3 integration)
- [ ] Tests pass locally with `npx playwright test`

---

<details>
<summary><strong>Deep Dive: Page Object Model</strong></summary>

### POM Class Template

```typescript
// tests/page-objects/LoginPage.ts
import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByTestId('login-email');
    this.passwordInput = page.getByTestId('login-password');
    this.submitButton = page.getByTestId('login-submit');
    this.errorMessage = page.getByTestId('login-error');
  }

  async navigate() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toBeVisible();
    await expect(this.errorMessage).toContainText(message);
  }
}
```

### Fixture Integration (Playwright fixtures)

```typescript
// tests/fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';
import { DashboardPage } from './page-objects/DashboardPage';

type PageFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
};

export const test = base.extend<PageFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
});

export { expect } from '@playwright/test';
```

### Usage in Tests

```typescript
// tests/e2e/auth.e2e.test.ts
import { test, expect } from '../fixtures';

// AC: Authenticated user is redirected to dashboard after login
// Behavior: User submits valid credentials -> Session created -> Dashboard renders
// @category: e2e
// @complexity: low
// ROI: 10

test('should redirect to dashboard when credentials are valid', async ({ loginPage, dashboardPage }) => {
  // Arrange
  await loginPage.navigate();

  // Act
  await loginPage.login('test@example.com', 'ValidPass123!');

  // Assert
  await expect(dashboardPage.welcomeHeading).toBeVisible();
});
```

### POM Guidelines

- One POM per distinct page or significant component group
- Locators defined in constructor, never inline in test methods
- Action methods are async and return `void`
- Assertion methods are async and use `expect()` internally
- No business logic in POMs — pure interaction encapsulation

</details>

---

<details>
<summary><strong>Deep Dive: Test Data Management</strong></summary>

### Factory Pattern (TypeScript builder functions)

```typescript
// tests/factories/user.factory.ts
import { faker } from '@faker-js/faker';

export interface UserData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'user';
  hasSavedCard?: boolean;
}

const defaults = (): UserData => ({
  email: faker.internet.email(),
  password: 'TestPass123!',
  firstName: faker.person.firstName(),
  lastName: faker.person.lastName(),
  role: 'user',
  hasSavedCard: false,
});

export async function createUser(overrides: Partial<UserData> = {}): Promise<UserData & { id: string }> {
  const data = { ...defaults(), ...overrides };
  // POST to test API or seed database directly
  const response = await fetch('/api/test/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const created = await response.json();
  return { ...data, id: created.id };
}

export async function deleteUser(id: string): Promise<void> {
  await fetch(`/api/test/users/${id}`, { method: 'DELETE' });
}
```

### Fixture Files (JSON seeds)

```json
// tests/fixtures/products.fixture.json
{
  "basic": {
    "name": "Test Widget",
    "price": 19.99,
    "sku": "WIDGET-001",
    "inStock": true,
    "category": "widgets"
  },
  "outOfStock": {
    "name": "Sold Out Widget",
    "price": 9.99,
    "sku": "WIDGET-OOS",
    "inStock": false,
    "category": "widgets"
  }
}
```

### Database Seeding / Teardown Hooks

```typescript
// tests/global.setup.ts
import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  // Seed reference data that all tests share (read-only)
  await fetch(`${config.projects[0].use.baseURL}/api/test/seed`, {
    method: 'POST',
    body: JSON.stringify({ scenario: 'baseline' }),
  });
}

export default globalSetup;
```

```typescript
// Per-test cleanup pattern
test.afterEach(async ({ request }) => {
  // Clean up any test-created records by ID tracked during the test
  for (const userId of createdUserIds) {
    await request.delete(`/api/test/users/${userId}`);
  }
  createdUserIds.length = 0;
});
```

### API Mocking with Playwright route()

```typescript
// Mock specific endpoint for one test
test('should show error when payment service is unavailable', async ({ page }) => {
  // Arrange: intercept and mock payment API
  await page.route('**/api/payments/**', (route) => {
    route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Service unavailable' }),
    });
  });

  // Act
  const checkout = new CheckoutPage(page);
  await checkout.submitPayment();

  // Assert
  await expect(checkout.errorBanner).toContainText('payment service');
});
```

### State Management Strategy

| Strategy | When to Use |
|----------|-------------|
| Fresh factory data per test | Default — prevents state leakage |
| Shared read-only fixtures | Reference data that never changes (categories, countries) |
| Database transaction rollback | High-volume tests needing fast cleanup |
| API route interception | Testing error states and edge cases without real backends |
| Isolated test user per test | When user session state is under test |

</details>

---

<details>
<summary><strong>Deep Dive: Playwright Configuration</strong></summary>

### Standard Config (3 browsers, CI-ready)

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: ['**/*.e2e.test.ts', '**/*.integration.test.ts'],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  timeout: 30_000,
  expect: { timeout: 5_000 },

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    process.env.CI ? ['github'] : ['list'],
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
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  ],

  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    stdout: 'ignore',
    stderr: 'pipe',
  },

  globalSetup: './tests/global.setup.ts',
  globalTeardown: './tests/global.teardown.ts',
});
```

### Config Option Reference

| Option | Description | Recommended Value |
|--------|-------------|-------------------|
| `retries` | Retry count on failure | `2` in CI, `0` locally |
| `workers` | Parallel worker count | `1` in CI to avoid port conflicts |
| `timeout` | Per-test timeout (ms) | `30000` |
| `expect.timeout` | Assertion timeout (ms) | `5000` |
| `trace` | When to capture trace | `on-first-retry` |
| `screenshot` | When to capture screenshot | `only-on-failure` |
| `video` | When to capture video | `retain-on-failure` |
| `fullyParallel` | Run all tests in parallel | `true` |
| `forbidOnly` | Block `.only` in CI | `!!process.env.CI` |

</details>

---

<details>
<summary><strong>Deep Dive: CI/CD Integration</strong></summary>

### GitHub Actions Workflow

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
        shard: [1, 2, 3, 4]  # Adjust based on test count

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

### Artifact Configuration Guidelines

| Artifact | Upload Condition | Retention |
|----------|-----------------|-----------|
| Screenshots | Always (failure only) | 14 days |
| Videos | On failure/retry | 14 days |
| Traces | On first retry | 14 days |
| HTML report | Always | 30 days |
| JUnit XML | Always | 7 days |

</details>

---

<details>
<summary><strong>Deep Dive: Coverage Tracking</strong></summary>

### Istanbul / c8 Integration with Playwright

```typescript
// playwright.config.ts - add coverage to global setup
// tests/global.setup.ts
export default async function globalSetup() {
  // Coverage is collected per browser context
  // Use @playwright/test built-in coverage API
}
```

```typescript
// Collect V8 coverage per test
test('should track coverage for checkout flow', async ({ page }) => {
  await page.coverage.startJSCoverage();

  // ... test actions ...

  const coverage = await page.coverage.stopJSCoverage();
  // Write coverage to file for Istanbul/c8 processing
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

### Per-Feature Coverage Tracking

Track coverage by feature tag rather than code lines for E2E tests:

```typescript
// Add feature tags to tests
test('should complete checkout @feature:checkout @priority:critical', async ({ page }) => {
  // ...
});
```

```bash
# Generate coverage report filtered by feature
npx playwright test --grep "@feature:checkout" --reporter=html
```

### Threshold Enforcement in CI

```bash
# package.json
{
  "scripts": {
    "test:coverage": "c8 --lines 80 --functions 80 --branches 70 npx playwright test"
  }
}
```

### Coverage vs. Quality

- E2E tests should target **critical user paths**, not code line coverage
- 5 well-designed E2E tests covering critical flows > 50 tests covering implementation details
- Track **behavior coverage** (AC items tested) alongside code coverage

</details>

---

<details>
<summary><strong>Deep Dive: Flaky Test Management</strong></summary>

### Detection Strategy

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0,  // Flaky tests fail on retry 1, pass on retry 2
  // Enable retry tracking in reporters
});
```

A test that passes after retry is classified as flaky. Track with:

```bash
# Run with explicit retry logging
npx playwright test --reporter=json | jq '.suites[].specs[] | select(.tests[].results[].retry > 0)'
```

### Quarantine Pattern

```typescript
// Quarantine a flaky test without deleting it
test.fixme('should load dashboard within 2 seconds', async ({ page }) => {
  // QUARANTINE: Flaky due to race condition in data loading
  // Tracked: https://github.com/org/repo/issues/456
  // Quarantined: 2026-02-15
  // Root cause: Dashboard API response timing varies under load
});
```

### Root Cause Categories

| Category | Symptoms | Fix |
|----------|----------|-----|
| Race conditions | Fails on fast machines, passes on slow | Add explicit `waitFor` on state transition |
| Animation timing | Fails during CSS transitions | Use `page.waitForFunction` to check computed style |
| Shared state | Fails only when run after specific tests | Add isolation; clean state in `beforeEach` |
| Network variability | Fails on slow CI, passes locally | Increase `expect.timeout`; mock slow endpoints |
| Test data conflicts | Fails when multiple tests create same data | Use unique identifiers via factories |

### Flakiness Dashboard (minimal)

```typescript
// scripts/flakiness-report.ts
// Run weekly to identify tests with >5% flakiness rate
// Report format: test name, flake rate, quarantine date if set
```

### Management Rules

- Any test failing intermittently for 3+ runs: quarantine within 24 hours
- Quarantined tests: root cause within 1 sprint or delete
- Never disable retries to "hide" flakiness — fix the test or the application

</details>

---

<details>
<summary><strong>Deep Dive: Test Isolation</strong></summary>

### Database Transaction Rollback

```typescript
// For integration tests with direct DB access
import { db } from '../src/db';

let transaction: any;

test.beforeEach(async () => {
  // Wrap each test in a transaction that gets rolled back
  transaction = await db.transaction();
});

test.afterEach(async () => {
  await transaction.rollback();
});

test('should create order record', async () => {
  // All DB operations use the transaction and are rolled back after
  const order = await createOrder(transaction, { userId: 'test-user' });
  expect(order.id).toBeDefined();
});
```

### Browser Storage Cleanup

```typescript
// playwright.config.ts - storageState cleared per test
export default defineConfig({
  use: {
    // Do NOT set storageState at root level — that would share auth state
  },
});

// Per-test auth isolation
test.use({ storageState: { cookies: [], origins: [] } });
```

### API State Reset

```typescript
// global.teardown.ts
export default async function globalTeardown() {
  // Reset any shared test state (e.g., feature flags, rate limits)
  await fetch(`${process.env.BASE_URL}/api/test/reset`, { method: 'POST' });
}
```

### Independent Test Ordering Verification

```bash
# Verify tests pass in random order (detects implicit ordering dependencies)
npx playwright test --workers=1 --repeat-each=3

# Run in reverse order
npx playwright test --grep-invert "your-test" && npx playwright test "your-test"
```

### Isolation Checklist Per Test

- [ ] Test creates its own data via factory (no reliance on data from other tests)
- [ ] Test cleans up all created records in `afterEach`
- [ ] No module-level variables mutated during test execution
- [ ] Browser cookies and localStorage cleared between tests
- [ ] API mocks scoped to the test (not registered globally)
- [ ] Test passes when run in isolation: `npx playwright test --grep "test name"`

</details>

---

## Extension Points

1. **Cypress adapter:** Generate Cypress-compatible test structure as an alternative to Playwright (swap `page.getByTestId` for `cy.get('[data-testid=...]')`)
2. **Visual regression testing:** Add `toHaveScreenshot()` assertions with pixel tolerance thresholds using Playwright's built-in visual comparison
3. **API contract testing:** Extend integration tests to validate OpenAPI schema compliance using `@apidevtools/swagger-validator`
4. **Performance budgets:** Add `page.evaluate(() => performance.timing)` assertions to fail tests when Core Web Vitals exceed thresholds
5. **Accessibility testing:** Integrate `@axe-core/playwright` to add `await checkA11y(page)` assertions to every E2E test
