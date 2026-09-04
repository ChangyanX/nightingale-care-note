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

async function installPatientMocks(
  page: Page,
  account: "patient" | "clinician" | "staff" = "patient",
  options: { scribeFailure?: { status: number; detail: string } } = {},
) {
  const state = {
    patientListRequests: 0,
    globalLogoutRequests: 0,
    actionRequests: [] as string[],
    entryRequests: [] as Record<string, unknown>[],
    scribeRequests: [] as Record<string, unknown>[],
    patientAiQuestions: [] as Record<string, unknown>[],
    patientAiJobs: [] as Record<string, unknown>[],
  };
  const cors = {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "authorization, apikey, content-type, x-client-info",
    "access-control-allow-methods": "GET, POST, PATCH, DELETE, OPTIONS",
  };
  const user = {
    id: USER_ID,
    aud: "authenticated",
    role: "authenticated",
    email: account === "patient" ? "patient.a@nightingale.local" : `${account}.a@nightingale.local`,
    email_confirmed_at: "2026-08-20T00:00:00Z",
    app_metadata: { provider: "email", providers: ["email"] },
    user_metadata: { display_name: account === "patient" ? "Parker Patient" : account === "staff" ? "Sam Staff" : "Dr. Casey Clinician" },
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
    if (pathname === "/entries" && request.method() === "POST") {
      const entryRequest = request.postDataJSON() as Record<string, unknown>;
      state.entryRequests.push(entryRequest);
      await route.fulfill({
        status: 201,
        headers: { ...cors, "content-type": "application/json" },
        body: JSON.stringify({
          id: state.entryRequests.length === 1
            ? "70000000-0000-0000-0000-000000000099"
            : "70000000-0000-0000-0000-000000000098",
          clinic_id: "10000000-0000-0000-0000-000000000001",
          patient_id: PATIENT_ID,
          author_id: USER_ID,
          author_role: "clinician",
          entry_type: entryRequest.entry_type,
          visibility: entryRequest.visibility,
          content: entryRequest.content,
          source_record_id: state.entryRequests.length === 1
            ? "60000000-0000-0000-0000-000000000099"
            : "60000000-0000-0000-0000-000000000098",
          current_version: 1,
          occurred_at: entryRequest.occurred_at,
          source: null,
        }),
      });
      return;
    }
    if (pathname === `/patients/${PATIENT_ID}/scribe-sessions` && request.method() === "POST") {
      const scribeRequest = request.postDataJSON() as Record<string, unknown>;
      state.scribeRequests.push(scribeRequest);
      if (options.scribeFailure) {
        await route.fulfill({
          status: options.scribeFailure.status,
          headers: { ...cors, "content-type": "application/json" },
          body: JSON.stringify({ detail: options.scribeFailure.detail }),
        });
        return;
      }
      await route.fulfill({
        status: 202,
        headers: { ...cors, "content-type": "application/json" },
        body: JSON.stringify({
          id: "d0000000-0000-0000-0000-000000000099",
          patient_id: PATIENT_ID,
          interaction_type: scribeRequest.interaction_type,
          status: "queued",
          attempt_count: 0,
          queue_position: 1,
          output_entry_id: null,
          provider_name: null,
          model_name: null,
          created_at: "2026-08-28T12:00:00+08:00",
          updated_at: "2026-08-28T12:00:00+08:00",
        }),
      });
      return;
    }
    if (pathname === "/patient/ai-question" && request.method() === "POST") {
      const questionRequest = request.postDataJSON() as Record<string, unknown>;
      state.patientAiQuestions.push(questionRequest);
      const job = {
        id: "d0000000-0000-0000-0000-000000000098",
        status: "queued",
        created_at: "2026-08-28T12:00:00+08:00",
        updated_at: "2026-08-28T12:00:00+08:00",
        completed_at: null,
        safe_error_code: null,
      };
      state.patientAiJobs = [job];
      await route.fulfill({
        status: 201,
        headers: { ...cors, "content-type": "application/json" },
        body: JSON.stringify({
          entry: {
            id: "71000000-0000-0000-0000-000000000099",
            entry_type: "patient_insight",
            content: `Patient question for care team: ${questionRequest.question}`,
            occurred_at: "2026-08-28T12:00:00+08:00",
          },
          job,
          message: "Your question was recorded and AI generation was queued for your care team.",
        }),
      });
      return;
    }
    if (pathname.startsWith("/comments/") && ["POST", "DELETE"].includes(request.method())) {
      state.actionRequests.push(`${request.method()} ${pathname}`);
      await route.fulfill({
        status: request.method() === "DELETE" ? 204 : 200,
        headers: { ...cors, "content-type": "application/json" },
        body: request.method() === "DELETE" ? undefined : JSON.stringify({ status: "recorded" }),
      });
      return;
    }
    const body =
      pathname === "/me"
        ? account === "patient" ? {
            id: USER_ID,
            email: user.email,
            display_name: "Parker Patient",
            preferred_name: "Parker",
            memberships: [],
            linked_patient_id: PATIENT_ID,
            account_kind: "patient",
            landing_path: "/patient",
          } : {
            id: USER_ID,
            email: user.email,
            display_name: account === "staff" ? "Sam Staff" : "Dr. Casey Clinician",
            preferred_name: account === "staff" ? "Sam" : "Casey",
            memberships: [{ clinic_id: "10000000-0000-0000-0000-000000000001", role: account }],
            linked_patient_id: null,
            account_kind: "clinic_user",
            landing_path: "/patients",
          }
        : pathname === "/patients"
          ? [{ id: PATIENT_ID, clinic_id: "10000000-0000-0000-0000-000000000001", synthetic_identifier: "SYN-A-001", display_name: "Parker Patient (Synthetic)", caller_role: "clinician" }]
        : pathname === `/patients/${PATIENT_ID}`
          ? { id: PATIENT_ID, clinic_id: "10000000-0000-0000-0000-000000000001", synthetic_identifier: "SYN-A-001", display_name: "Parker Patient (Synthetic)" }
        : pathname === `/patients/${PATIENT_ID}/glance`
          ? { patient_id: PATIENT_ID, items: [] }
        : pathname === `/patients/${PATIENT_ID}/timeline`
          ? [{
              id: "70000000-0000-0000-0000-000000000001",
              clinic_id: "10000000-0000-0000-0000-000000000001",
              patient_id: PATIENT_ID,
              author_id: USER_ID,
          author_role: account,
              entry_type: "clinician_note",
              visibility: "internal",
              content: "Synthetic follow-up review.",
              source_record_id: "60000000-0000-0000-0000-000000000001",
              current_version: 1,
              occurred_at: "2026-08-28T09:00:00+08:00",
              source: null,
            }]
        : pathname === `/patients/${PATIENT_ID}/comments`
          ? [{
              id: "90000000-0000-0000-0000-000000000001",
              clinic_id: "10000000-0000-0000-0000-000000000001",
              patient_id: PATIENT_ID,
              entry_id: "70000000-0000-0000-0000-000000000001",
              section_id: null,
              parent_comment_id: null,
              author_id: USER_ID,
              body: "Confirm the synthetic follow-up interval.",
              body_format: "plain",
              status: "open",
              assigned_to: null,
              source_version_id: null,
              source_start_offset: null,
              source_end_offset: null,
              quoted_text: null,
              created_at: "2026-08-28T09:10:00+08:00",
              resolved_at: null,
              reaction_counts: { acknowledged: 0, agree: 0, question: 0 },
              my_reactions: [],
            }]
        : pathname === `/patients/${PATIENT_ID}/tasks`
          || pathname === `/patients/${PATIENT_ID}/highlights`
          || pathname === `/patients/${PATIENT_ID}/scribe-jobs`
          || pathname === `/patients/${PATIENT_ID}/scribe-job-events`
          || pathname === "/provider-usage"
          || pathname === "/importance-preferences"
          ? []
        : pathname === "/patient/dashboard"
          ? {
              patient_id: PATIENT_ID,
              display_name: "Parker Patient (Synthetic)",
              synthetic_identifier: "SYN-A-001",
              clinic_id: "10000000-0000-0000-0000-000000000001",
              summaries: [{ id: "71000000-0000-0000-0000-000000000001", entry_type: "patient_summary", content: "Your breathing plan is stable; keep tracking the evening cough.", occurred_at: "2026-08-27T09:00:00+08:00" }],
              instructions: [{ id: "71000000-0000-0000-0000-000000000002", entry_type: "patient_instruction", content: "Record morning and evening peak flow for seven days.", occurred_at: "2026-08-27T09:05:00+08:00" }],
              history: [{ id: "71000000-0000-0000-0000-000000000003", entry_type: "patient_insight", content: "Night cough was milder after keeping the room warm.", occurred_at: "2026-08-28T07:30:00+08:00" }],
              appointments: [{ id: "72000000-0000-0000-0000-000000000001", preferred_date: "2026-09-02", time_preference: "morning", reason_category: "follow_up", note: null, status: "requested", created_at: "2026-08-28T08:00:00+08:00" }],
              reports: [{ id: "73000000-0000-0000-0000-000000000001", title: "Synthetic respiratory review", report_type: "care_plan", status: "available", released_at: "2026-08-27T10:00:00+08:00", patient_safe_summary: "No urgent concern was identified in this synthetic review." }],
              observations: [{ observation_type: "peak_flow", value: 410, unit: "L/min", observed_at: "2026-08-28T07:00:00+08:00" }, { observation_type: "sleep_hours", value: 7, unit: "hours", observed_at: "2026-08-28T07:00:00+08:00" }],
              visible_tasks: [{ id: "74000000-0000-0000-0000-000000000001", title: "Complete the seven-day diary", status: "open", due_at: "2026-09-03T17:00:00+08:00", patient_acknowledged_at: null }],
            }
          : pathname === "/patient/ai-jobs"
            ? state.patientAiJobs
          : pathname === "/notifications"
            ? []
            : [];
    await route.fulfill({
      status: pathname === "/patients" && account === "patient" ? 403 : 200,
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
  await expect(page).toHaveScreenshot("patient-dashboard.png", {
    animations: "disabled",
    fullPage: true,
  });
});

test("patient can trigger a status-only AI timeline generation", async ({ page }) => {
  const state = await installPatientMocks(page);
  await signInAsPatient(page);

  await page.getByRole("textbox", { name: "Your question" }).fill("Could my synthetic evening cough be related to the inhaler timing?");
  await page.getByRole("button", { name: "Generate care-team summary" }).click();

  await expect(page.getByText("Your question was recorded and AI generation was queued for your care team.")).toBeVisible();
  await expect(page.getByLabel("AI generation status").getByText("queued", { exact: true })).toBeVisible();
  await expect(page.getByText("Processing securely")).toBeVisible();
  expect(state.patientAiQuestions).toHaveLength(1);
  expect(state.patientAiQuestions[0].question).toBe("Could my synthetic evening cough be related to the inhaler timing?");
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

test("clinician login hydrates persisted recent-patient state without warnings", async ({ page }) => {
  const hydrationErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" && message.text().toLowerCase().includes("hydration")) {
      hydrationErrors.push(message.text());
    }
  });
  await page.addInitScript((patientId) => {
    localStorage.setItem("nightingale-theme", "dark");
    localStorage.setItem("nightingale-recent-patients", JSON.stringify([patientId]));
  }, PATIENT_ID);
  const state = await installPatientMocks(page, "clinician");

  await page.goto("/sign-in");
  await page.getByLabel("Email").fill("clinician.a@nightingale.local");
  await page.locator('input[autocomplete="current-password"]').fill("SyntheticPassword123!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();

  await expect(page).toHaveURL(/\/patients$/);
  await expect(page.getByRole("heading", { name: "Select a patient" })).toBeVisible();
  await expect(page.getByText("Recently viewed")).toBeVisible();
  expect(state.patientListRequests).toBeGreaterThanOrEqual(1);
  expect(hydrationErrors).toEqual([]);
});

test("clinician can toggle a comment reaction and delete their own comment", async ({ page }) => {
  const state = await installPatientMocks(page, "clinician");
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill("clinician.a@nightingale.local");
  await page.locator('input[autocomplete="current-password"]').fill("SyntheticPassword123!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("link", { name: /Parker Patient/ }).click();

  const comment = page.locator(".comment-card").filter({ hasText: "Confirm the synthetic" });
  const acknowledge = comment.getByRole("button", { name: /Acknowledge/ });
  await expect(acknowledge).toHaveAttribute("aria-pressed", "false");
  await acknowledge.click();
  await expect(acknowledge).toHaveAttribute("aria-pressed", "true");
  await expect(acknowledge).toContainText("1");
  await acknowledge.click();
  await expect(acknowledge).toHaveAttribute("aria-pressed", "false");
  await expect(acknowledge).toContainText("0");

  await comment.getByRole("button", { name: "Delete comment" }).click();
  await comment.getByRole("button", { name: "Confirm delete" }).click();
  await expect(comment).toHaveCount(0);
  expect(state.actionRequests).toEqual([
    "POST /comments/90000000-0000-0000-0000-000000000001/reactions",
    "DELETE /comments/90000000-0000-0000-0000-000000000001/reactions/acknowledged",
    "DELETE /comments/90000000-0000-0000-0000-000000000001",
  ]);
});

test("clinician can add internal and patient-facing timeline updates", async ({ page }) => {
  const state = await installPatientMocks(page, "clinician");
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill("clinician.a@nightingale.local");
  await page.locator('input[autocomplete="current-password"]').fill("SyntheticPassword123!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("link", { name: /Parker Patient/ }).click();

  await page.getByRole("button", { name: "Add update" }).click();
  await expect(page.getByLabel("Update type")).toHaveValue("clinician_note");
  await expect(page.getByText("Internal care-team content. Patients cannot access it.")).toBeVisible();
  await page.getByRole("textbox", { name: "Note", exact: true }).fill("Synthetic clinician follow-up added from the Care Note.");
  await page.getByRole("button", { name: "Save update" }).click();

  await expect(page.getByText("Synthetic clinician follow-up added from the Care Note.")).toBeVisible();
  await page.getByRole("button", { name: "Add update" }).click();
  await page.getByLabel("Update type").selectOption("patient_summary");
  await expect(page.getByText("This will be released to the patient.")).toBeVisible();
  await page.getByRole("textbox", { name: "Note", exact: true }).fill("Synthetic patient-safe breathing summary.");
  await page.getByRole("button", { name: "Save update" }).click();

  await expect(page.getByText("Synthetic patient-safe breathing summary.")).toBeVisible();
  expect(state.entryRequests).toHaveLength(2);
  expect(state.entryRequests[0]).toMatchObject({
    patient_id: PATIENT_ID,
    entry_type: "clinician_note",
    visibility: "internal",
    content: "Synthetic clinician follow-up added from the Care Note.",
  });
  expect(state.entryRequests[1]).toMatchObject({
    patient_id: PATIENT_ID,
    entry_type: "patient_summary",
    visibility: "patient_facing",
    content: "Synthetic patient-safe breathing summary.",
  });
});

test("clinician can queue the complete live AI timeline flow", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window.crypto, "randomUUID", { value: undefined, configurable: true });
  });
  const state = await installPatientMocks(page, "clinician");
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill("clinician.a@nightingale.local");
  await page.locator('input[autocomplete="current-password"]').fill("SyntheticPassword123!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("link", { name: /Parker Patient/ }).click();

  await page.getByRole("button", { name: "Generate AI summary" }).click();
  await page.getByRole("button", { name: "Use synthetic example" }).click();
  await page.getByRole("button", { name: "Save source and generate" }).click();

  await expect(page.getByText("Generation queued. The timeline will update automatically when validation finishes.")).toBeVisible();
  expect(state.scribeRequests).toHaveLength(1);
  expect(state.scribeRequests[0].interaction_type).toBe("doctor_consult");
  expect(String(state.scribeRequests[0].transcript)).toContain("Synthetic consult");
  expect(String(state.scribeRequests[0].idempotency_key)).toMatch(/^live-doctor_consult-[a-f0-9]{32}$/);
});

test("clinician sees the sanitized queue rejection instead of worker advice", async ({ page }) => {
  const state = await installPatientMocks(page, "clinician", {
    scribeFailure: { status: 403, detail: "Role cannot create this session" },
  });
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill("clinician.a@nightingale.local");
  await page.locator('input[autocomplete="current-password"]').fill("SyntheticPassword123!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("link", { name: /Parker Patient/ }).click();

  await page.getByRole("button", { name: "Generate AI summary" }).click();
  await page.getByRole("button", { name: "Use synthetic example" }).click();
  await page.getByRole("button", { name: "Save source and generate" }).click();

  await expect(page.locator(".live-scribe-panel .form-error")).toHaveText(
    "Generation was not queued. Role cannot create this session",
  );
  expect(state.scribeRequests).toHaveLength(1);
});

test("staff can add only an internal staff note", async ({ page }) => {
  const state = await installPatientMocks(page, "staff");
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill("staff.a@nightingale.local");
  await page.locator('input[autocomplete="current-password"]').fill("SyntheticPassword123!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("link", { name: /Parker Patient/ }).click();

  await page.getByRole("button", { name: "Add update" }).click();
  await expect(page.getByLabel("Update type")).toHaveValue("staff_note");
  await expect(page.getByLabel("Update type").locator('option[value="patient_summary"]')).toHaveCount(0);
  await page.getByRole("textbox", { name: "Note", exact: true }).fill("Synthetic staff coordination note.");
  await page.getByRole("button", { name: "Save update" }).click();

  await expect(page.getByText("Synthetic staff coordination note.")).toBeVisible();
  expect(state.entryRequests).toHaveLength(1);
  expect(state.entryRequests[0]).toMatchObject({
    patient_id: PATIENT_ID,
    entry_type: "staff_note",
    visibility: "internal",
  });
});
