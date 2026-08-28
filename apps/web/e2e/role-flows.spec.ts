import { expect, Page, test } from "@playwright/test";

const USER_ID = "20000000-0000-0000-0000-000000000004";
const PATIENT_ID = "40000000-0000-0000-0000-000000000001";

function testAccessToken() {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
  const payload = Buffer.from(
    JSON.stringify({ sub: USER_ID, role: "authenticated", exp: 4_102_444_800 }),
  ).toString("base64url");
  return `${header}.${payload}.synthetic-test-signature`;
}

async function installPatientMocks(page: Page) {
  const state = { patientListRequests: 0, globalLogoutRequests: 0 };
  const cors = {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "authorization, apikey, content-type, x-client-info",
    "access-control-allow-methods": "GET, POST, PATCH, OPTIONS",
  };
  const user = {
    id: USER_ID,
    aud: "authenticated",
    role: "authenticated",
    email: "patient.a@nightingale.local",
    email_confirmed_at: "2026-08-20T00:00:00Z",
    app_metadata: { provider: "email", providers: ["email"] },
    user_metadata: { display_name: "Parker Patient" },
    created_at: "2026-08-20T00:00:00Z",
  };
  const token = testAccessToken();

  await page.route("http://127.0.0.1:54321/auth/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: cors });
    } else if (url.pathname.endsWith("/token")) {
      await route.fulfill({
        status: 200,
        headers: { ...cors, "content-type": "application/json" },
        body: JSON.stringify({
          access_token: token,
          token_type: "bearer",
          expires_in: 3600,
          refresh_token: "synthetic-refresh-token",
          user,
        }),
      });
    } else if (url.pathname.endsWith("/logout")) {
      if (url.searchParams.get("scope") === "global") state.globalLogoutRequests += 1;
      await route.fulfill({ status: 204, headers: cors });
    } else if (url.pathname.endsWith("/user")) {
      await route.fulfill({
        status: 200,
        headers: { ...cors, "content-type": "application/json" },
        body: JSON.stringify(user),
      });
    } else {
      await route.fulfill({ status: 404, headers: cors });
    }
  });

  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: cors });
      return;
    }
    if (pathname === "/patients") state.patientListRequests += 1;
    const body =
      pathname === "/me"
        ? {
            id: USER_ID,
            email: user.email,
            display_name: "Parker Patient",
            preferred_name: "Parker",
            memberships: [],
            linked_patient_id: PATIENT_ID,
            account_kind: "patient",
            landing_path: "/patient",
          }
        : pathname === "/patient/dashboard"
          ? {
              patient_id: PATIENT_ID,
              display_name: "Parker Patient (Synthetic)",
              synthetic_identifier: "SYN-A-001",
              clinic_id: "10000000-0000-0000-0000-000000000001",
              summaries: [],
              instructions: [],
              history: [],
              appointments: [],
              reports: [],
              observations: [],
              visible_tasks: [],
            }
          : pathname === "/notifications"
            ? []
            : [];
    await route.fulfill({
      status: pathname === "/patients" ? 403 : 200,
      headers: { ...cors, "content-type": "application/json" },
      body: JSON.stringify(body),
    });
  });
  return state;
}

async function signInAsPatient(page: Page) {
  await page.goto("/sign-in");
  await expect(page.locator("html")).toHaveAttribute("data-app-ready", "true");
  await page.getByLabel("Email").fill("patient.a@nightingale.local");
  await page.locator('input[autocomplete="current-password"]').fill("SyntheticPassword123!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/patient$/);
  await expect(page.getByRole("heading", { name: "Hello, Parker" })).toBeVisible();
}

test("patient login lands on the own-account dashboard without requesting the patient list", async ({
  page,
}) => {
  const state = await installPatientMocks(page);
  await signInAsPatient(page);
  expect(state.patientListRequests).toBe(0);
});

test("global logout clears the authenticated browser session and returns to sign-in", async ({
  page,
}) => {
  const state = await installPatientMocks(page);
  await signInAsPatient(page);
  await page.getByRole("button", { name: "Open account menu" }).click();
  await page.getByRole("button", { name: "Log out" }).click();

  await expect(page).toHaveURL(/\/sign-in$/);
  expect(state.globalLogoutRequests).toBe(1);
});
