import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./test-results",
  snapshotDir: "./e2e/__screenshots__",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-chromium", use: { ...devices["Pixel 5"] } },
  ],
  webServer: {
    command: `"${process.execPath}" ./node_modules/next/dist/bin/next dev --webpack --port 3100`,
    cwd: ".",
    env: {
      NEXT_DIST_DIR: ".next-playwright",
      NEXT_PUBLIC_SUPABASE_URL: "http://127.0.0.1:54321",
      NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "visual-test-public-key",
      NEXT_PUBLIC_API_URL: "http://127.0.0.1:8000",
    },
    url: "http://127.0.0.1:3100/sign-in",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
