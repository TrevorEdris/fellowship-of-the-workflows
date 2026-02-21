# Assertion Cheatsheet

Common assertion patterns for Playwright E2E and integration tests, organized by category with anti-patterns included.

---

## Playwright Built-in Assertions

Playwright assertions automatically retry until the condition is met (up to `expect.timeout`). Always prefer these over manual polling.

### Visibility & Existence

```typescript
// Element is visible in the viewport
await expect(page.getByTestId('submit-button')).toBeVisible();

// Element exists in DOM but may be hidden
await expect(page.getByTestId('hidden-panel')).toBeAttached();

// Element is NOT visible
await expect(page.getByTestId('error-banner')).not.toBeVisible();

// Element does not exist in DOM
await expect(page.getByTestId('deleted-item')).not.toBeAttached();

// Element is enabled (not disabled)
await expect(page.getByTestId('submit-button')).toBeEnabled();

// Element is disabled
await expect(page.getByTestId('submit-button')).toBeDisabled();

// Checkbox / radio is checked
await expect(page.getByTestId('agree-checkbox')).toBeChecked();
```

### Text Content

```typescript
// Exact text match
await expect(page.getByTestId('page-title')).toHaveText('Order Confirmation');

// Partial text match
await expect(page.getByTestId('status-badge')).toContainText('Processing');

// Regex match (e.g., order IDs, dynamic content)
await expect(page.getByTestId('order-id')).toHaveText(/ORD-\d+/);

// Multiple items — check each
const items = page.getByTestId('cart-item');
await expect(items).toHaveCount(3);
await expect(items.nth(0)).toContainText('Widget A');

// Input field value
await expect(page.getByTestId('email-input')).toHaveValue('user@example.com');
```

### URL & Navigation

```typescript
// Exact URL
await expect(page).toHaveURL('http://localhost:3000/dashboard');

// URL contains path segment
await expect(page).toHaveURL(/\/orders\/\d+/);

// URL starts with
await expect(page).toHaveURL(/^http:\/\/localhost:3000\/checkout/);

// Page title
await expect(page).toHaveTitle('Checkout — My Store');
await expect(page).toHaveTitle(/My Store/);
```

### Count & Lists

```typescript
// Exact element count
await expect(page.getByRole('listitem')).toHaveCount(5);

// At least one element (prefer explicit count when possible)
await expect(page.getByTestId('search-result')).not.toHaveCount(0);

// Table rows
const rows = page.locator('table tbody tr');
await expect(rows).toHaveCount(10);
```

### Attributes & Classes

```typescript
// Check specific attribute value
await expect(page.getByTestId('avatar')).toHaveAttribute('alt', 'User avatar');

// Attribute exists (any value)
await expect(page.getByTestId('image')).toHaveAttribute('src');

// Class applied
await expect(page.getByTestId('status-badge')).toHaveClass(/badge-success/);

// Input type
await expect(page.getByTestId('password-input')).toHaveAttribute('type', 'password');
```

---

## Soft Assertions

Use soft assertions when you want to check multiple conditions in a single test without stopping on the first failure. All failures are reported at the end.

```typescript
test('should display complete order summary', async ({ page }) => {
  await page.goto('/orders/12345');

  // Soft assertions — all are checked even if one fails
  await expect.soft(page.getByTestId('order-id')).toHaveText('ORD-12345');
  await expect.soft(page.getByTestId('order-status')).toHaveText('Confirmed');
  await expect.soft(page.getByTestId('order-total')).toHaveText('$59.98');
  await expect.soft(page.getByTestId('shipping-address')).toContainText('123 Main St');

  // Hard assertion — stops if this fails
  await expect(page.getByTestId('confirmation-email-notice')).toBeVisible();
});
```

**When to use soft assertions:** Checking multiple fields on a summary/detail page where all fields should be correct and you want a complete failure report.

**When NOT to use:** Assertions that gate subsequent actions (e.g., clicking a button that may not exist).

---

## Custom Matchers

```typescript
// playwright.config.ts — extend expect globally
import { expect } from '@playwright/test';

expect.extend({
  async toBeLoadedWithinMs(locator: any, ms: number) {
    const start = Date.now();
    try {
      await expect(locator).toBeVisible({ timeout: ms });
      return { message: () => '', pass: true };
    } catch {
      const elapsed = Date.now() - start;
      return {
        message: () => `Expected element to load within ${ms}ms but took ${elapsed}ms`,
        pass: false,
      };
    }
  },
});

// Usage
await expect(page.getByTestId('dashboard')).toBeLoadedWithinMs(2000);
```

---

## Network Assertions

### Wait for Response

```typescript
// Wait for specific API call to complete
const responsePromise = page.waitForResponse('**/api/orders/**');
await page.getByTestId('submit-order').click();
const response = await responsePromise;

expect(response.status()).toBe(201);
const body = await response.json();
expect(body.id).toMatch(/ORD-\d+/);
```

### Request / Response Validation

```typescript
// Validate request payload
const requestPromise = page.waitForRequest(req =>
  req.url().includes('/api/payments') && req.method() === 'POST'
);
await checkout.submitPayment();
const request = await requestPromise;
const payload = request.postDataJSON();
expect(payload.amount).toBe(5999); // cents
expect(payload.currency).toBe('usd');
```

### Response Status Checks

```typescript
// Ensure no unexpected error responses occurred during a workflow
page.on('response', response => {
  if (response.url().includes('/api/') && response.status() >= 500) {
    throw new Error(`Unexpected 5xx response: ${response.url()} -> ${response.status()}`);
  }
});
```

---

## Visual Assertions

### Screenshot Comparison

```typescript
// Full page screenshot
await expect(page).toHaveScreenshot('checkout-confirmation.png');

// Element screenshot
await expect(page.getByTestId('order-summary')).toHaveScreenshot('order-summary.png');

// With pixel threshold (allow minor differences)
await expect(page).toHaveScreenshot('dashboard.png', {
  maxDiffPixels: 100,
  threshold: 0.1,  // 10% per-pixel tolerance
});

// Mask dynamic regions (timestamps, user IDs)
await expect(page).toHaveScreenshot('profile.png', {
  mask: [
    page.getByTestId('last-login-time'),
    page.getByTestId('user-id'),
  ],
});
```

**First run:** Playwright generates baseline screenshots. Subsequent runs compare against them. Commit baselines to source control.

**Update baselines after intentional UI changes:**
```bash
npx playwright test --update-snapshots
```

---

## Accessibility Assertions

### @axe-core/playwright Integration

```typescript
// npm install -D @axe-core/playwright
import { checkA11y, injectAxe } from 'axe-playwright';

test('should have no accessibility violations on checkout page', async ({ page }) => {
  await page.goto('/checkout');
  await injectAxe(page);

  // Check entire page
  await checkA11y(page, undefined, {
    runOnly: {
      type: 'tag',
      values: ['wcag2a', 'wcag2aa'],
    },
  });
});

test('should have no a11y violations on modal dialog', async ({ page }) => {
  await page.getByTestId('open-modal').click();
  await injectAxe(page);

  // Check only the modal
  await checkA11y(page, '[data-testid="modal"]', {
    includedImpacts: ['critical', 'serious'],
  });
});
```

---

## Anti-Pattern Examples

These assertion patterns create brittle, unreliable tests. Avoid them.

### Testing Implementation Details

```typescript
// BAD: Asserts on internal state, not observable behavior
const component = page.locator('.ProductCard__container--active');
expect(await component.getAttribute('class')).toContain('active');

// GOOD: Assert on what the user sees
await expect(page.getByTestId('product-card')).toHaveClass(/active/);
await expect(page.getByTestId('product-active-badge')).toBeVisible();
```

### Hardcoded Timing

```typescript
// BAD: Fixed delay — always wrong (too long or too short)
await page.waitForTimeout(3000);
await expect(page.getByTestId('results')).toBeVisible();

// GOOD: Wait for the condition directly
await expect(page.getByTestId('results')).toBeVisible();
// Playwright auto-waits up to expect.timeout (default 5s)
```

### Asserting on Exact Timestamps

```typescript
// BAD: Timestamps are non-deterministic
await expect(page.getByTestId('created-at')).toHaveText('2026-02-20T14:32:11Z');

// GOOD: Assert format, not exact value; or mask it in screenshot tests
await expect(page.getByTestId('created-at')).toHaveText(/\d{4}-\d{2}-\d{2}/);
```

### Element Count That Changes

```typescript
// BAD: Count changes as application data changes
await expect(page.getByRole('row')).toHaveCount(47);

// GOOD: Assert relative to your test's data setup
const { count: initialCount } = await getOrderCount();
await createOrder({ userId: user.id });
await page.reload();
await expect(page.getByRole('row')).toHaveCount(initialCount + 1);
```

### Boolean Existence Check (Fragile)

```typescript
// BAD: Doesn't auto-wait; fails if element appears after assertion
const isVisible = await page.getByTestId('banner').isVisible();
expect(isVisible).toBe(true);

// GOOD: Auto-waits for the condition
await expect(page.getByTestId('banner')).toBeVisible();
```

### Asserting Internal API Data Not Shown to User

```typescript
// BAD: Tests database state rather than user experience
const dbOrder = await db.orders.findOne({ where: { userId: user.id } });
expect(dbOrder.status).toBe('confirmed');

// GOOD: Assert what the user can observe
await expect(page.getByTestId('order-status')).toHaveText('Confirmed');
await expect(page.getByTestId('confirmation-banner')).toBeVisible();
```

---

## Quick Reference Card

| Assertion | Use For |
|-----------|---------|
| `.toBeVisible()` | Element renders on screen |
| `.toBeAttached()` | Element in DOM (may be hidden) |
| `.toBeEnabled()` | Form controls not disabled |
| `.toHaveText(str)` | Exact text content match |
| `.toContainText(str)` | Partial text match |
| `.toHaveValue(str)` | Input field value |
| `.toHaveURL(str\|regex)` | Current page URL |
| `.toHaveTitle(str)` | Page title |
| `.toHaveCount(n)` | Number of matching elements |
| `.toHaveAttribute(k, v)` | HTML attribute value |
| `.toHaveClass(regex)` | CSS class applied |
| `.toHaveScreenshot(name)` | Visual regression comparison |
| `expect.soft(...)` | Non-blocking multi-assertion |
| `page.waitForResponse(url)` | Network call completed |
| `checkA11y(page)` | No WCAG violations |
