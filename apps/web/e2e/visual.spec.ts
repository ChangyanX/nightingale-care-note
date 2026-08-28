import { expect, test } from "@playwright/test";

test("sign-in remains readable at desktop and mobile widths", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/sign-in");
  await expect(page.locator("html")).toHaveAttribute("data-app-ready", "true");
  await expect(page.getByRole("heading", { name: "Open the shared patient story." })).toBeVisible();
  await expect(page).toHaveScreenshot("sign-in.png", {
    animations: "disabled",
    fullPage: true,
  });
});

test("dark mode keeps the editorial hierarchy and contrast", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("nightingale-theme", "dark"));
  await page.goto("/sign-in");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page).toHaveScreenshot("sign-in-dark.png", {
    animations: "disabled",
    fullPage: true,
  });
});

test("sign-in is keyboard operable", async ({ page }) => {
  await page.goto("/sign-in");
  await expect(page.locator("html")).toHaveAttribute("data-app-ready", "true");
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
});

test("password visibility preserves focus and selection", async ({ page }) => {
  await page.goto("/sign-in");
  await expect(page.locator("html")).toHaveAttribute("data-app-ready", "true");
  const password = page.locator('input[autocomplete="current-password"]');
  await password.fill("SyntheticSecret123!");
  await password.evaluate((input: HTMLInputElement) => input.setSelectionRange(2, 9));

  await page.getByRole("button", { name: "Show password" }).click();
  await expect(password).toHaveAttribute("type", "text");
  await expect(password).toBeFocused();
  await expect
    .poll(() =>
      password.evaluate((input: HTMLInputElement) => [input.selectionStart, input.selectionEnd]),
    )
    .toEqual([2, 9]);

  await page.getByRole("button", { name: "Hide password" }).press("Enter");
  await expect(password).toHaveAttribute("type", "password");
  await expect(password).toBeFocused();
});

test("theme selection persists after reload", async ({ page }) => {
  await page.addInitScript(() => {
    if (!window.sessionStorage.getItem("theme-test-started")) {
      window.localStorage.removeItem("nightingale-theme");
      window.sessionStorage.setItem("theme-test-started", "true");
    }
  });
  await page.goto("/sign-in");
  await expect(page.locator("html")).toHaveAttribute("data-app-ready", "true");
  const initial = await page.locator("html").getAttribute("data-theme");

  await page.getByRole("button", { name: /Use (dark|light) theme/ }).click();
  const selected = await page.locator("html").getAttribute("data-theme");
  expect(selected).not.toBe(initial);
  expect(selected).toMatch(/^(light|dark)$/);

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", selected!);
});
