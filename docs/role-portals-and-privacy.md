# Role Portals, Account Security, and Patient Privacy

All identities and care records described here are synthetic. The principal
product remains the clinic-scoped longitudinal Care Note: Top Card, timeline,
collaboration, revision/revert, distinct AI-scribed entries, exact provenance,
and server-enforced authorization. Patient-service modules are deliberately
lightweight prototypes and do not replace that assessed core.

## Role routing

`GET /me` is the authoritative post-login routing response:

| Account | Landing path | Clinical patient list |
|---|---|---|
| Staff | `/patients` | Own clinic only |
| Clinician | `/patients` | Own clinic only |
| Admin | `/patients` | Own clinic, read-only clinical oversight |
| Patient | `/patient` | Denied with `403` |

The sign-in and passwordless callback pages route from `landing_path`. The
patient-list and patient-detail pages independently re-check `/me` before
clinical reads. FastAPI also rejects patient accounts from the clinical patient
list, detail, timeline, task, and Glance endpoints before reading clinical rows.
Those checks complement PostgreSQL RLS; the UI is never the security boundary.

## Patient-safe data boundary

The patient dashboard uses a dedicated `GET /patient/dashboard` DTO. Its
backend queries select explicit safe columns and only:

- released `patient_summary` and `patient_instruction` entries;
- the signed-in patient's own `patient_insight` submissions;
- the patient's own appointment requests;
- reports with `status = available` and an explicit release timestamp;
- patient-safe structured observations; and
- tasks explicitly marked `patient_visible`.

The patient response schema has no author ID, raw source-record ID, version ID,
offset, comment, risk reason, assignment, audit, or internal provenance field.
It cannot serialize those fields even if an upstream row accidentally contains
them. Raw AI doctor/nurse/patient-session notes remain `internal` and are never
selected by the patient endpoint.

PostgreSQL provides the second enforcement layer:

- entry RLS permits only released summaries/instructions or a patient's own
  submitted insight;
- source records, entry/section versions, comments, highlights, audit events,
  AI jobs, and internal collaboration remain clinical-role-only;
- report RLS exposes only available, explicitly released reports;
- appointment, observation, task, avatar, profile, and notification policies
  bind reads and writes to the caller;
- notification inserts/updates validate that the recipient is a member of the
  notification clinic or its linked patient; and
- guessed restricted IDs resolve to no row/`404`, never a restricted target.

If a patient-facing summary needs provenance, the application may expose a
separate patient-safe source label such as “clinic-approved summary, 23 Aug”.
It must not expose or resolve the restricted source entry, raw transcript,
historical version, offsets, or internal authoring detail.

## Patient dashboard scope

Implemented modules are intentionally concise:

- **My Care Summary:** released summaries, instructions, and visible actions.
- **Book Appointment:** create and review a lightweight request; this is not a
  scheduling engine.
- **Chat with AI:** non-emergency, non-diagnostic question capture. It creates a
  patient-session source plus a patient-authored Care Note input with
  provenance. The current prototype does not call an LLM or provide an answer.
- **Log Symptoms:** structured severity/start time plus optional text becomes a
  patient-authored longitudinal input.
- **History:** only the patient's submitted updates/questions.
- **Reports:** only explicitly released reports; preparing reports remain
  hidden until release.
- **Health Dashboard:** simple patient-safe trends from synthetic observations,
  without internal clinical interpretations.

This scope keeps Care Note trust, provenance, collaboration, and RBAC as the
implementation and demo focus.

## Account and session handling

Every role receives the same global header controls: content-safe Notification
Centre, persisted system-aware light/dark theme, and an avatar menu linking to
Account Settings and logout.

Account Settings permits only the current user to change `preferred_name`,
optional birth date, and private avatar. `update_own_profile` accepts a strict
field allowlist and always updates `auth.uid()`; role, memberships, clinic,
linked patient, and account email are read-only context. Avatar uploads are
limited to 1 MB PNG/JPEG/WebP, checked in the browser and by server MIME magic,
stored in a private bucket under the caller's UUID, and displayed through a
short-lived signed URL.

Password changes require current-password reauthentication, a confirmed strong
replacement, Supabase-managed password hashing, and global sign-out. Ordinary
logout also uses global sign-out, clears the browser session, and returns to
sign-in. Passwords, credentials, tokens, prompts, and note bodies are not logged.

Notification preview strings are fixed by event type. They do not include note
bodies, comments, risk reasons, patient names, or raw resource content. Direct
table update is revoked; read state changes only through the caller-owned RPC.

## Redaction and infrastructure assumptions

Any future LLM response for patient-entered text must accept only the verified
redaction type from `app.domain.redaction`. Names, IC/ID numbers, and phone
numbers are removed before the provider boundary. The current patient AI-chat
prototype records a question for the care team without invoking an LLM; it
still executes the redaction check and stores only safe redaction counts in
session metadata so the boundary remains ready for a later provider call.

Deployed web/API/Supabase/LLM connections use TLS. PostgreSQL and private object
storage rely on the selected provider's encryption-at-rest controls. These are
deployment assumptions that must be verified on the final hosted environment.

## Verification map

- `test_role_portal_api.py`: patient landing and clinical-workspace denial,
  reduced dashboard queries, guessed-ID denial, redaction, profile allowlist,
  avatar validation, ownership-checked notifications, and RLS contracts.
- `test_rbac_scope.py`: clinic isolation, raw-AI/comment denial, and role-owned
  write boundaries, with opt-in live RLS tests.
- `e2e/role-flows.spec.ts`: patient routing without `/patients` and global
  logout request/redirect.
- `e2e/visual.spec.ts`: password visibility focus/selection, keyboard access,
  theme persistence, and desktop/mobile snapshots.
- Existing revision, revert, concurrent-edit, collaboration, and provenance
  suites continue to guard the primary Care Note.

## Demo flows

### Staff/clinician Care Note

1. Sign in as `staff.a@nightingale.local` and open Parker or Morgan.
2. Read the bounded Top Card, then scan the multi-date timeline with separate
   staff, clinician, patient, doctor-AI, nurse-AI, and AI-patient entries.
3. Open an accepted highlight and resolve its exact historical source span.
4. Add a staff note/comment or update a task; observe the role ownership rule.
5. Sign in as the clinician, revise the clinician-owned note, compare versions,
   and revert to create a new immutable version.

### Patient-safe portal

1. Sign in as `patient.a@nightingale.local`; confirm the landing page is
   `/patient`, not the clinic patient list.
2. Review only the released care summary, instruction, visible action, report,
   and patient-safe trend.
3. Submit a synthetic symptom update and a clearly non-diagnostic question.
4. Create an appointment request and inspect its status.
5. Open Account Settings, change the preferred name or avatar if desired, then
   log out from either Account Settings or the avatar menu.
