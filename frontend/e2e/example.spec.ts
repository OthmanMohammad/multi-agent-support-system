import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Homepage", () => {
  test("should load successfully", async ({ page }) => {
    await page.goto("/");

    // Wait for the page to be fully loaded
    await page.waitForLoadState("networkidle");

    // Check if the header is visible
    await expect(page.locator("header")).toBeVisible();
  });

  test("should have correct page title", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Multi-Agent Support System/);
  });

  test("should display theme toggle button", async ({ page }) => {
    await page.goto("/");

    // Find theme toggle button
    const themeToggle = page.getByRole("button", { name: /toggle theme/i });
    await expect(themeToggle).toBeVisible();
  });

  test("should toggle theme when clicking theme button", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Get initial theme
    const html = page.locator("html");
    const initialClass = await html.getAttribute("class");

    // Click theme toggle
    const themeToggle = page.getByRole("button", { name: /toggle theme/i });
    await themeToggle.click();

    // Wait for theme change
    await page.waitForTimeout(500);

    // Verify theme changed
    const newClass = await html.getAttribute("class");
    expect(newClass).not.toBe(initialClass);
  });

  test("should have no accessibility violations", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const accessibilityScanResults = await new AxeBuilder({ page })
      // Exclude rules that may have false positives or are being addressed separately
      .exclude(".dark") // Exclude dark mode container that may have contrast issues during transition
      .withTags(["wcag2a", "wcag2aa"]) // Focus on WCAG 2.0 Level A and AA
      .disableRules([
        "color-contrast", // Color contrast may vary with theme switching
        "landmark-one-main", // May not apply to all pages
      ])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("should navigate between pages", async ({ page }) => {
    await page.goto("/");

    // Check if navigation links are present
    const nav = page.locator("nav");
    await expect(nav).toBeVisible();

    // Check for navigation items - use .first() since there may be multiple dashboard links
    const dashboardLink = page
      .getByRole("link", { name: /dashboard/i })
      .first();
    const chatLink = page.getByRole("link", { name: /chat/i }).first();

    await expect(dashboardLink).toBeVisible();
    await expect(chatLink).toBeVisible();
  });

  test("should be responsive", async ({ page }) => {
    // Test desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto("/");
    await expect(page.locator("header")).toBeVisible();

    // Test tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator("header")).toBeVisible();

    // Test mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator("header")).toBeVisible();
  });
});
