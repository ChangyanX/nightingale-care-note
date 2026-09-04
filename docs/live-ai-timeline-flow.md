# Live AI Timeline Generation

## Outcome

Authenticated care participants can initiate a genuine, durable AI-scribe flow
from the product UI using synthetic text. Clinicians create doctor-consult
sources, staff create nurse-consult sources, and patients create AI-patient
session sources. Admin remains read-only.

The flow is asynchronous so an interrupted browser request or provider call
does not lose or duplicate work:

1. FastAPI forwards the caller JWT to a role-checking database function.
2. PostgreSQL atomically creates the role-owned source record, visible timeline
   entry, immutable version, audit event, and queued AI job.
3. The separately deployed worker claims the job with its service identity and
   loads only non-system entries linked to the exact source record.
4. Deterministic redaction removes supported names, identity numbers, phone
   numbers, and other configured identifiers before the provider call.
5. Groq returns strict structured output. Domain validation rejects malformed
   summaries or highlights.
6. One database transaction creates the internal system-authored AI entry,
   version-one snapshot, exact-span suggested highlights, safe audit metadata,
   output link, and succeeded job state.
7. Supabase Realtime invalidates authorized clinic screens, which refetch the
   timeline and job status through FastAPI.

## Role and privacy boundary

| Account | May trigger | Source ownership | What the account can see |
|---|---|---|---|
| Clinician | Doctor consult | Clinician note | Source, internal AI summary, provenance, review controls |
| Staff | Nurse consult | Staff note | Source and internal AI summary; no clinician-note overwrite |
| Patient | AI patient session | Patient insight | Original question and status-only job result |
| Admin | Nothing | None | Clinic-scoped read-only oversight |

Patient job responses deliberately omit `source_record_id`, `output_entry_id`,
provider/model metadata, prompts, raw generated content, highlights, audit
events, and provenance targets. A succeeded status means the care team received
an internal summary; it does not release that summary to the patient.

## Local operation

Use four terminals after applying the migrations and configuring ignored
worker secrets:

```bash
make db-start
make dev-api
make dev-worker
make dev-web
```

`make dev-worker` polls continuously. `make worker-once` is useful when stepping
through exactly one queued job. Worker logs contain job IDs, status, model, and
safe error codes only—never source or generated note bodies.

## Demo: clinician and patient in synchronized sessions

1. Open a normal browser session as `clinician.a@nightingale.local` and a
   private/incognito session as `patient.a@nightingale.local`.
2. On the patient dashboard, ask a clearly synthetic non-emergency question
   under **Chat with AI**. Show the queued/processing status without any raw AI
   content.
3. In the clinician session, open that patient. The patient-authored question
   appears in the longitudinal timeline, followed by the separate
   **AI generated** patient-session summary after the worker completes.
4. Show its source metadata and suggested highlight review. Return to the
   patient session and show only “Summary delivered to your care team.”
5. In the clinician session, select **Generate AI summary**, choose the
   synthetic example, and submit. Show progress stages, then the original
   clinician source and distinct system-authored doctor-consult summary.

If the worker is stopped, jobs remain queued and recover when it restarts. A
retry with the same idempotency key returns the existing job. Provider or
redaction failures persist only a bounded safe error code and never expose the
provider response.

Queue submission and background processing are deliberately reported as
different stages. A **not queued** message includes a sanitized API reason, or
reports that the browser could not confirm the API response. The browser
retains the idempotency key across submission retries, including when it misses
a successful API response. After the job appears in the status panel,
queued/processing failures can be diagnosed from the worker's safe job/event
metadata.

The clinical status panel combines Realtime invalidation with a two-second
polling fallback while any job is queued or processing. It displays safe stages
and sanitized failure codes. If a local worker receives 403 from a claim or
completion RPC, apply migrations through `202608280008`; those migrations add
the least-privilege service-role table and row-lock grants required by the
`SECURITY INVOKER` worker functions.
