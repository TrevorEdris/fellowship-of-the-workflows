---
name: e2e-testing
description: "Scaffold E2E and integration tests using Playwright. Covers Page Object Model setup, test data management, configuration generation, coverage tracking, and CI/CD integration. Triggered by: set up Playwright, write E2E tests, integration test, end-to-end test, test this user flow, scaffold test suite, browser testing. Use when creating new test suites, adding E2E coverage to features, or setting up Playwright from scratch."
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

## References

Consult these when you need detailed patterns for a specific aspect of E2E testing:

| Reference | When to Read |
|-----------|-------------|
| [page-object-model.md](references/page-object-model.md) | POM class templates, fixture integration, usage patterns |
| [test-data-patterns.md](references/test-data-patterns.md) | Factory functions, fixture files, seeding, API mocking, state management |
| [playwright-config-templates.md](references/playwright-config-templates.md) | Standard config, browser projects, option reference |
| [ci-integration.md](references/ci-integration.md) | GitHub Actions workflow with sharding, artifact upload, report merging |
| [coverage-tracking.md](references/coverage-tracking.md) | V8 coverage, feature tagging, threshold enforcement |
| [flaky-test-management.md](references/flaky-test-management.md) | Detection, quarantine pattern, root cause categories |
| [test-isolation.md](references/test-isolation.md) | Transaction rollback, storage cleanup, ordering verification |
| [assertion-cheatsheet.md](references/assertion-cheatsheet.md) | Common Playwright assertions and patterns |

---

## Extension Points

1. **Cypress adapter:** Generate Cypress-compatible test structure as an alternative to Playwright (swap `page.getByTestId` for `cy.get('[data-testid=...]')`)
2. **Visual regression testing:** Add `toHaveScreenshot()` assertions with pixel tolerance thresholds using Playwright's built-in visual comparison
3. **API contract testing:** Extend integration tests to validate OpenAPI schema compliance using `@apidevtools/swagger-validator`
4. **Performance budgets:** Add `page.evaluate(() => performance.timing)` assertions to fail tests when Core Web Vitals exceed thresholds
5. **Accessibility testing:** Integrate `@axe-core/playwright` to add `await checkA11y(page)` assertions to every E2E test
