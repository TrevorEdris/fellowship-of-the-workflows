# Test Data Patterns

Strategies for managing test data in E2E and integration test suites: factories, fixtures, seeding, mocking, and cleanup.

---

## Factory Pattern

TypeScript builder functions that generate typed test data with sensible defaults and per-test overrides.

### Basic Factory

```typescript
// tests/factories/user.factory.ts
import { faker } from '@faker-js/faker';

export interface CreateUserOptions {
  email?: string;
  password?: string;
  firstName?: string;
  lastName?: string;
  role?: 'admin' | 'editor' | 'viewer';
  emailVerified?: boolean;
  hasSavedCard?: boolean;
}

export interface CreatedUser extends Required<CreateUserOptions> {
  id: string;
  createdAt: string;
}

export function buildUserData(overrides: CreateUserOptions = {}): Required<CreateUserOptions> {
  return {
    email: faker.internet.email(),
    password: 'TestPass123!',
    firstName: faker.person.firstName(),
    lastName: faker.person.lastName(),
    role: 'viewer',
    emailVerified: true,
    hasSavedCard: false,
    ...overrides,
  };
}

// Creates user via test API endpoint
export async function createUser(overrides: CreateUserOptions = {}): Promise<CreatedUser> {
  const data = buildUserData(overrides);
  const response = await fetch(`${process.env.BASE_URL}/api/test/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create test user: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

export async function deleteUser(id: string): Promise<void> {
  await fetch(`${process.env.BASE_URL}/api/test/users/${id}`, { method: 'DELETE' });
}
```

### Factory Usage in Tests

```typescript
// Single user with defaults
const user = await createUser();

// Specific role
const admin = await createUser({ role: 'admin' });

// Multiple users
const [buyer, seller] = await Promise.all([
  createUser({ role: 'viewer' }),
  createUser({ role: 'editor', emailVerified: true }),
]);

// Cleanup in afterEach
const createdIds: string[] = [];

test.afterEach(async () => {
  await Promise.all(createdIds.map(deleteUser));
  createdIds.length = 0;
});

test('should allow admin to delete user', async ({ page }) => {
  const admin = await createUser({ role: 'admin' });
  const target = await createUser({ role: 'viewer' });
  createdIds.push(admin.id, target.id);
  // ...
});
```

### Nested / Relational Factories

```typescript
// tests/factories/order.factory.ts
export async function createOrder(overrides: Partial<OrderData> = {}): Promise<CreatedOrder> {
  // Automatically create dependencies if not provided
  const user = overrides.userId
    ? { id: overrides.userId }
    : await createUser();

  const product = overrides.productId
    ? { id: overrides.productId }
    : await createProduct({ inStock: true });

  const data = {
    userId: user.id,
    productId: product.id,
    quantity: 1,
    status: 'pending',
    ...overrides,
  };

  const response = await fetch(`${process.env.BASE_URL}/api/test/orders`, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: { 'Content-Type': 'application/json' },
  });
  return response.json();
}
```

---

## Fixture Files

Static JSON or YAML seed data for reference data that rarely changes.

### JSON Fixture Structure

```json
// tests/fixtures/products.fixture.json
{
  "standard": {
    "name": "Standard Widget",
    "description": "A basic test widget for most scenarios",
    "price": 19.99,
    "sku": "WIDGET-STD-001",
    "inStock": true,
    "category": "widgets",
    "stock": 100
  },
  "premium": {
    "name": "Premium Widget",
    "description": "High-value item for checkout flow tests",
    "price": 199.99,
    "sku": "WIDGET-PREM-001",
    "inStock": true,
    "category": "widgets",
    "stock": 10
  },
  "outOfStock": {
    "name": "Sold Out Widget",
    "description": "Used to test out-of-stock handling",
    "price": 9.99,
    "sku": "WIDGET-OOS-001",
    "inStock": false,
    "category": "widgets",
    "stock": 0
  }
}
```

```typescript
// tests/fixtures/index.ts
import products from './products.fixture.json';
import categories from './categories.fixture.json';

export { products, categories };

// Load and create fixtures
export async function seedProducts(): Promise<Record<string, CreatedProduct>> {
  const created: Record<string, CreatedProduct> = {};
  for (const [key, data] of Object.entries(products)) {
    const response = await fetch(`${process.env.BASE_URL}/api/test/products`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' },
    });
    created[key] = await response.json();
  }
  return created;
}
```

### Per-Environment Fixtures

```
tests/fixtures/
├── base/                    # Shared across all environments
│   ├── categories.json
│   └── permissions.json
├── local/                   # Local development overrides
│   └── users.json
└── ci/                      # CI-specific data
    └── users.json
```

```typescript
const env = process.env.TEST_ENV || 'local';
const fixtureDir = path.join(__dirname, 'fixtures', env);
```

---

## Database Seeding

Setup and teardown strategies when tests need direct database access.

### Global Seed / Teardown

```typescript
// tests/global.setup.ts
import { chromium, FullConfig } from '@playwright/test';

export default async function globalSetup(config: FullConfig) {
  const baseURL = config.projects[0].use.baseURL!;

  // Seed reference data (read-only, shared across all tests)
  const res = await fetch(`${baseURL}/api/test/seed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario: 'baseline' }),
  });

  if (!res.ok) {
    throw new Error(`Seeding failed: ${res.status}`);
  }

  // Optional: create a shared auth session
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(`${baseURL}/login`);
  await page.getByTestId('email').fill('e2e-admin@test.local');
  await page.getByTestId('password').fill('TestPass123!');
  await page.getByTestId('login-submit').click();
  await page.waitForURL(`${baseURL}/dashboard`);
  await page.context().storageState({ path: 'tests/.auth/admin.json' });
  await browser.close();
}
```

```typescript
// tests/global.teardown.ts
export default async function globalTeardown() {
  const baseURL = process.env.BASE_URL || 'http://localhost:3000';

  // Remove all test-created data using a test API endpoint
  await fetch(`${baseURL}/api/test/teardown`, {
    method: 'POST',
    body: JSON.stringify({ scenario: 'baseline' }),
    headers: { 'Content-Type': 'application/json' },
  });
}
```

### Per-Test Cleanup Pattern

```typescript
// Pattern: track IDs, clean up in afterEach
test.describe('Order management', () => {
  const cleanup: { type: string; id: string }[] = [];

  test.afterEach(async ({ request }) => {
    // Clean up in reverse creation order
    for (const { type, id } of cleanup.reverse()) {
      await request.delete(`/api/test/${type}/${id}`);
    }
    cleanup.length = 0;
  });

  test('should allow cancellation of pending orders', async ({ page, request }) => {
    // Arrange
    const user = await createUser();
    cleanup.push({ type: 'users', id: user.id });
    const order = await createOrder({ userId: user.id });
    cleanup.push({ type: 'orders', id: order.id });

    // Act + Assert
    // ...
  });
});
```

### Transaction Rollback (Integration Tests)

```typescript
// When tests have direct DB access (integration tests only)
import { db } from '../../src/db/connection';

let trx: Knex.Transaction;

test.beforeEach(async () => {
  trx = await db.transaction();
});

test.afterEach(async () => {
  await trx.rollback();
});

test('should create order in database', async () => {
  const order = await OrderRepository.create(trx, {
    userId: 'test-user-id',
    total: 59.99,
  });
  expect(order.id).toBeDefined();
  // Transaction rolls back after test — no cleanup needed
});
```

---

## API Mocking

Mock strategies at the network boundary using Playwright's `page.route()`.

### Basic Route Interception

```typescript
test('should display error banner when API returns 500', async ({ page }) => {
  // Arrange: mock before navigation
  await page.route('**/api/products**', (route) => {
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Internal server error' }),
    });
  });

  // Act
  await page.goto('/products');

  // Assert
  await expect(page.getByTestId('error-banner')).toBeVisible();
  await expect(page.getByTestId('error-banner')).toContainText('trouble loading');
});
```

### Selective Mocking (Only Specific Requests)

```typescript
test('should show payment declined message', async ({ page }) => {
  // Only mock the payment charge endpoint
  await page.route('**/api/payments/charge', (route) => {
    route.fulfill({
      status: 402,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'card_declined', code: 'insufficient_funds' }),
    });
  });

  // All other requests pass through normally
  const checkout = new CheckoutPage(page);
  await checkout.navigate();
  await checkout.submitPayment();

  await expect(checkout.paymentError).toContainText('card was declined');
});
```

### Mock with Request Inspection

```typescript
test('should send correct payload to order API', async ({ page }) => {
  let capturedBody: any;

  await page.route('**/api/orders', async (route) => {
    capturedBody = JSON.parse(route.request().postData() || '{}');
    // Let the request through to the real API
    await route.continue();
  });

  const checkout = new CheckoutPage(page);
  await checkout.completeOrder({ quantity: 2, productId: 'PROD-001' });

  expect(capturedBody.quantity).toBe(2);
  expect(capturedBody.productId).toBe('PROD-001');
});
```

### MSW Handler Template (for unit/component tests)

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/products', () => {
    return HttpResponse.json({
      items: [
        { id: 'prod-1', name: 'Widget', price: 19.99, inStock: true },
      ],
      total: 1,
    });
  }),

  http.post('/api/orders', async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      id: `ORD-${Date.now()}`,
      ...body,
      status: 'pending',
      createdAt: new Date().toISOString(),
    }, { status: 201 });
  }),

  http.post('/api/payments/charge', () => {
    return HttpResponse.json({ error: 'card_declined' }, { status: 402 });
  }),
];
```

### Mock Data Co-location

Co-locate mock data with the test that uses it — don't store in a global mock directory:

```typescript
// tests/e2e/products.e2e.test.ts
const MOCK_PRODUCT_LIST = {
  items: [
    { id: 'p1', name: 'Widget A', price: 9.99, inStock: true },
    { id: 'p2', name: 'Widget B', price: 19.99, inStock: false },
  ],
  total: 2,
};

test('should show out-of-stock badge on unavailable products', async ({ page }) => {
  await page.route('**/api/products', route =>
    route.fulfill({ json: MOCK_PRODUCT_LIST })
  );
  // ...
});
```

---

## State Management Summary

| Strategy | When to Use | Cleanup |
|----------|-------------|---------|
| Fresh factory per test | Default — creates unique data each test | `afterEach` deletion via API |
| Shared read-only fixtures | Reference data (categories, permissions) | Global teardown or none |
| Transaction rollback | Integration tests with direct DB access | Automatic on rollback |
| `page.route()` interception | Error states, unavailable services | Scoped to test; auto-removed |
| Shared auth state (storageState) | Auth is not under test; skip repeated login | Global setup; never mutate |
| Isolated test user | When user session state is under test | `afterEach` deletion |
