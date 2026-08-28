import { expect, test } from "@playwright/test";

test("sign-in remains readable at desktop and mobile widths", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/sign-in");
  await expect(page.locator("html")).toHaveAttribute("data-app-ready", "true");
  await expect(page.getByRole("heading", { name: "Sign in to your clinic workspace" })).toBeVisible();
  await expect(page.getByText(".env.hosted-demo")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Staff" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Open Next.js Dev Tools" })).toHaveCount(0);
  await expect(page).toHaveScreenshot("sign-in.png", {
    animations: "disabled",
    fullPage: true,
  });
});

test("synthetic personas are isolated to the demo route", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByText("Demo environment", { exact: true })).toBeVisible();
  await expect(page.getByText("Synthetic patient data only. Do not enter real patient information.")).toBeVisible();

  await page.getByRole("button", { name: /Clinician/ }).click();
  await expect(page.getByLabel("Work email")).toHaveValue("clinician.a@nightingale.local");
  await expect(page.locator('input[autocomplete="current-password"]')).toBeFocused();
});

test("dark mode keeps the calm hierarchy and contrast", async ({ page }) => {
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

test("client-owned preferences do not cause hydration warnings", async ({ page }) => {
  const hydrationErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" && message.text().toLowerCase().includes("hydration")) {
      hydrationErrors.push(message.text());
    }
  });
  await page.addInitScript(() => {
    localStorage.setItem("nightingale-theme", "dark");
    localStorage.setItem(
      "nightingale-recent-patients",
      JSON.stringify(["40000000-0000-0000-0000-000000000001"]),
    );
  });

  await page.goto("/patients");
  await page.waitForURL(/\/sign-in$/);
  await expect(page.locator("html")).toHaveAttribute("data-app-ready", "true");
  expect(hydrationErrors).toEqual([]);
});

test("browser-extension body attributes do not cause hydration warnings", async ({ page }) => {
  const hydrationErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" && message.text().toLowerCase().includes("hydration")) {
      hydrationErrors.push(message.text());
    }
  });
  await page.addInitScript(() => {
    const observer = new MutationObserver(() => {
      if (document.body) {
        document.body.classList.add("__bm__extension");
        observer.disconnect();
      }
    });
    observer.observe(document, { childList: true, subtree: true });
  });

  await page.goto("/sign-in");
  await expect(page.locator("body")).toHaveClass(/__bm__extension/);
  await expect(page.locator("html")).toHaveAttribute("data-app-ready", "true");
  expect(hydrationErrors).toEqual([]);
});
