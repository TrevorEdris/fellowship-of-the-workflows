# Test Isolation

## Database Transaction Rollback

```typescript
import { db } from '../src/db';

let transaction: any;

test.beforeEach(async () => {
  transaction = await db.transaction();
});

test.afterEach(async () => {
  await transaction.rollback();
});

test('should create order record', async () => {
  const order = await createOrder(transaction, { userId: 'test-user' });
  expect(order.id).toBeDefined();
});
```

## Browser Storage Cleanup

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

## API State Reset

```typescript
// global.teardown.ts
export default async function globalTeardown() {
  await fetch(`${process.env.BASE_URL}/api/test/reset`, { method: 'POST' });
}
```

## Independent Test Ordering Verification

```bash
# Verify tests pass in random order
npx playwright test --workers=1 --repeat-each=3

# Run in reverse order
npx playwright test --grep-invert "your-test" && npx playwright test "your-test"
```

## Isolation Checklist Per Test

- [ ] Test creates its own data via factory (no reliance on data from other tests)
- [ ] Test cleans up all created records in `afterEach`
- [ ] No module-level variables mutated during test execution
- [ ] Browser cookies and localStorage cleared between tests
- [ ] API mocks scoped to the test (not registered globally)
- [ ] Test passes when run in isolation: `npx playwright test --grep "test name"`
