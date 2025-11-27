# Testing Documentation

## Overview

This project uses a comprehensive testing strategy covering unit tests, integration tests, end-to-end tests, and accessibility testing.

## Testing Stack

### Unit & Integration Testing

- **Jest 30** - Testing framework
- **React Testing Library 16** - Component testing utilities
- **@testing-library/user-event** - User interaction simulation

### E2E Testing

- **Playwright 1.56** - Cross-browser E2E testing
- **@axe-core/playwright** - Automated accessibility testing

### Code Quality

- **Husky** - Git hooks
- **lint-staged** - Run linters on staged files
- **commitlint** - Enforce conventional commits

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pnpm test

# Watch mode (interactive)
pnpm test:watch

# Coverage report
pnpm test:coverage

# CI mode (strict, with coverage)
pnpm test:ci
```

### E2E Tests

```bash
# Install Playwright browsers (first time only)
pnpm playwright:install

# Run E2E tests (headless)
pnpm test:e2e

# Run with UI mode (recommended for development)
pnpm test:e2e:ui

# Run in headed mode (see browser)
pnpm test:e2e:headed

# Debug mode
pnpm test:e2e:debug
```

### All Tests

```bash
# Run all quality checks (type-check, lint, format, unit tests)
pnpm validate
```

## Writing Tests

### Unit Test Example

```typescript
// components/ui/__tests__/button.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "../button";

describe("Button", () => {
  it("renders correctly", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("handles click events", async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>Click</Button>);
    await user.click(screen.getByRole("button"));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### E2E Test Example

```typescript
// e2e/homepage.spec.ts
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("homepage loads successfully", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("header")).toBeVisible();
});

test("has no accessibility violations", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

## Coverage Requirements

We maintain **80% minimum coverage** across all metrics:

- **Branches**: 80%
- **Functions**: 80%
- **Lines**: 80%
- **Statements**: 80%

View coverage reports:

```bash
pnpm test:coverage
# Open: coverage/lcov-report/index.html
```

## Git Hooks

### Pre-commit Hook

Automatically runs on `git commit`:

- Lints staged files with ESLint
- Formats staged files with Prettier
- Runs tests for affected files
- Type checks all TypeScript files

### Commit Message Hook

Enforces conventional commit format:

- `feat: add new feature`
- `fix: resolve bug`
- `docs: update documentation`
- `test: add tests`
- `refactor: code refactoring`
- `perf: performance improvement`
- `chore: maintenance tasks`

## Continuous Integration

GitHub Actions automatically runs on every push/PR:

1. **Code Quality Job**
   - Type checking
   - Linting
   - Formatting checks
   - Unit tests with coverage
   - Build verification

2. **E2E Tests Job**
   - Playwright tests across multiple browsers
   - Mobile and desktop viewports

3. **Lighthouse CI Job**
   - Performance audits (>90% score)
   - Accessibility audits (>95% score)
   - Best practices (>90% score)
   - SEO (>90% score)

## Performance Monitoring

### Bundle Analysis

Analyze bundle size:

```bash
pnpm build:analyze
```

This opens an interactive visualization showing:

- Bundle composition
- Largest modules
- Duplicate packages
- Tree map of dependencies

### Lighthouse CI

Performance thresholds:

- First Contentful Paint: <2s
- Largest Contentful Paint: <2.5s
- Cumulative Layout Shift: <0.1
- Total Blocking Time: <300ms

## Best Practices

### Test Organization

```
components/
├── ui/
│   ├── button.tsx
│   └── __tests__/
│       └── button.test.tsx
└── __tests__/
    └── theme-toggle.test.tsx

e2e/
├── homepage.spec.ts
├── authentication.spec.ts
└── chat.spec.ts
```

### Test Naming

- Use descriptive test names: `it("handles click events when button is enabled")`
- Group related tests with `describe()`
- Use `test.describe()` for E2E tests

### Accessibility Testing

Every E2E test should include accessibility check:

```typescript
const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
expect(accessibilityScanResults.violations).toEqual([]);
```

### Mock Data

- Keep mocks in `__mocks__/` directory
- Use fixtures for consistent test data
- Mock external APIs and services

## Troubleshooting

### Tests Failing Locally

1. Clear Jest cache:

   ```bash
   pnpm jest --clearCache
   ```

2. Reinstall dependencies:
   ```bash
   rm -rf node_modules
   pnpm install
   ```

### Playwright Issues

1. Reinstall browsers:

   ```bash
   pnpm playwright:install
   ```

2. Update Playwright:
   ```bash
   pnpm update @playwright/test
   ```

### Pre-commit Hook Failing

Skip hooks (only when necessary):

```bash
git commit --no-verify -m "emergency fix"
```

## Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Documentation](https://playwright.dev/)
- [Axe Accessibility Testing](https://www.deque.com/axe/playwright/)
- [Conventional Commits](https://www.conventionalcommits.org/)
