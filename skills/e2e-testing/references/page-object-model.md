# Page Object Model

## POM Class Template

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

## Fixture Integration (Playwright fixtures)

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

## Usage in Tests

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

## POM Guidelines

- One POM per distinct page or significant component group
- Locators defined in constructor, never inline in test methods
- Action methods are async and return `void`
- Assertion methods are async and use `expect()` internally
- No business logic in POMs — pure interaction encapsulation
