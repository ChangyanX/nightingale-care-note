# Nightingale Care Note — Project Blueprint

## 1. Project Summary

Nightingale Care Note is a provenance-first, longitudinal care-note web application for clinic teams. It consolidates clinician notes, staff updates, patient-provided insights, AI-scribed consultation summaries, tasks, comments, and audit history into one patient record.

The core product must help a clinician or staff member answer three questions in under ten seconds:

1. What matters right now?
2. What changed?
3. What requires action?

Every surfaced insight must remain traceable to its original timeline entry and source text. AI-generated information is presented as a suggestion until reviewed, and clinician-confirmed information takes precedence when sources conflict.

This repository uses a modular monolith with separately runnable frontend, API, and background-worker processes. It deliberately avoids microservices during the 72-hour build.

## 2. Success Criteria

The prototype is successful when it demonstrates the following end-to-end behavior:

- A staff member or clinician can sign in and open a synthetic patient record.
- The patient page presents a glance view and longitudinal timeline.
- Manual and AI-scribed timeline entries are visibly distinguishable.
- Staff and clinicians can collaborate without overwriting each other's content.
- A user can comment, mention another clinic user, assign work, and resolve a thread.
- A clinician can highlight important source text.
- A highlight displays an importance reason and links to the exact source entry and span.
- The application retains immutable revision history and supports reversion.
- Patient-facing responses exclude internal comments and raw AI-scribed notes.
- Server-side authorization and database policies prevent cross-role and cross-clinic access.
- Text is redacted before it is sent to an LLM.
- One genuine AI-scribe flow produces a structured summary through the redacted LLM pipeline.
- Timeline entries, comments, tasks, and highlight decisions update live for connected users.
- The glance-view API meets or credibly approximates a warm-path P95 latency of 300 ms or less.
- Automated tests prove the required security, provenance, versioning, and concurrency behavior.

## 3. Scope

### 3.1 Required MVP

The MVP includes:

- Authentication and synthetic demo accounts
- Clinic-scoped role-based access control
- Patient selection
- One shared Care Note per patient
- Glance View / Top Card
- Longitudinal timeline
- Manual staff and clinician entries
- Distinct AI-scribed entries
- Patient-facing summaries and instructions
- Threaded comments
- Mentions and assignments
- Resolve and unresolve actions
- Entry revision history
- Change comparison
- Revert to a previous version
- Highlight suggestion, acceptance, and rejection
- Exact highlight provenance
- Deterministic conflict handling
- Lightweight live updates for timeline entries, comments, tasks, and highlights
- PHI redaction before LLM processing
- Genuine LLM-generated structured summaries
- Lightweight adaptive importance weights based on review interactions
- Audit events
- Required automated tests
- Synthetic seed data
- Performance measurement

### 3.2 Include If Time Permits

- Mobile-friendly progressive web application behavior
- Enhanced notification delivery for mentions and assignments
- Rich-text editing beyond the required section editor

### 3.3 Deferred or Demonstrated Architecturally

- Full hybrid-storage and data-decay implementation; this is planned as a separate milestone after the core submission
- Production ambient voice capture
- Speaker diarization and overlap handling
- Noisy-environment audio processing
- Multilingual medical transcription
- Embedding-based semantic search
- CRDT-based character-level collaborative editing
- Independently deployed domain microservices
- Enterprise EHR integration
- Production handling of real protected health information

## 4. Architectural Decisions

### 4.1 Architecture Style

Use a modular monolith in a single repository. The frontend, API, and worker are independently runnable processes, but they share one domain model and one backend codebase.

Reasons:

- Faster implementation and debugging during a 72-hour build
- Easier transactional consistency for versions, audit events, and provenance
- One authorization model
- Minimal deployment and observability overhead
- Clear internal module boundaries can later become service boundaries

### 4.2 Frontend

- Language: TypeScript
- Framework: Next.js with React and App Router
- Styling: Tailwind CSS
- UI components: shadcn/ui or a small custom component set
- Server-state management: TanStack Query
- Forms: React Hook Form
- Client validation: Zod
- Component tests: Vitest and React Testing Library
- End-to-end tests: Playwright

### 4.3 Backend

- Language: Python 3.12+
- Framework: FastAPI
- Request and response validation: Pydantic
- Database: PostgreSQL managed by Supabase
- Database access: caller-scoped Supabase access for normal requests, plus narrowly scoped transactional database functions
- Schema migrations: versioned SQL migrations or Alembic
- Backend tests: pytest
- API contract: FastAPI-generated OpenAPI

### 4.4 Managed Infrastructure

Use Supabase for:

- PostgreSQL
- Authentication
- Row-Level Security
- Private object storage
- Realtime subscriptions for timeline entries, comments, tasks, and highlight decisions

Use one supported LLM provider for structured summaries and highlight suggestions. The provider integration must be isolated behind a backend interface so the application is not tightly coupled to a single model.

The request path must preserve database authorization:

- FastAPI verifies the caller's Supabase JWT and resolves clinic membership.
- Normal user reads and writes execute with the caller's JWT so PostgreSQL RLS sees the authenticated identity.
- Multi-row mutations use narrowly scoped, security-invoker database functions or transactions that repeat the same clinic and role checks.
- The service-role credential is reserved for the internal worker and administrative setup. It is never used for ordinary user requests.
- Tests exercise both API authorization and direct RLS denial.

### 4.5 Background Processing

Use a Postgres-backed `jobs` table and one Python worker process. Do not introduce Redis, RabbitMQ, Kafka, or Celery for the prototype.

The worker runs from the same backend package as the API:

```text
python -m app.api
python -m app.worker
```

The job design must support:

- Durable state
- Idempotency keys
- Atomic job claiming
- Retry counts
- Retry backoff
- Error recording
- Status visibility
- Safe recovery from a stopped worker

## 5. High-Level System Design

```text
┌─────────────────────────────┐
│ Next.js Web Application    │
│                            │
│ Glance View                │
│ Timeline                   │
│ Comments and Tasks         │
│ Revision History           │
│ Patient View               │
└──────────────┬──────────────┘
               │ HTTPS + JWT
               ▼
┌─────────────────────────────┐
│ FastAPI Backend            │
│                            │
│ Authentication Context     │
│ RBAC                       │
│ Care Note Domain           │
│ Revision and Audit Logic   │
│ Provenance                 │
│ Redaction                  │
│ Importance Ranking         │
└───────┬───────────┬─────────┘
        │           │ creates jobs
        │           ▼
        │    ┌─────────────────────┐
        │    │ Python Worker       │
        │    │                     │
        │    │ Redaction Check     │
        │    │ LLM Invocation      │
        │    │ Structured Parsing  │
        │    │ Highlight Proposals │
        │    └──────────┬──────────┘
        │               │
        ▼               ▼
┌─────────────────────────────┐
│ Supabase                   │
│                            │
│ PostgreSQL + RLS           │
│ Authentication             │
│ Private Object Storage     │
│ Realtime                   │
└─────────────────────────────┘
```

## 6. Repository Structure

```text
nightingale-care-note/
├── apps/
│   └── web/
│       ├── app/
│       │   ├── (auth)/
│       │   ├── (clinical)/
│       │   │   └── patients/[patientId]/
│       │   └── (patient)/
│       ├── components/
│       │   ├── glance-card/
│       │   ├── timeline/
│       │   ├── comments/
│       │   ├── revision-history/
│       │   └── provenance/
│       ├── lib/
│       │   ├── api/
│       │   ├── auth/
│       │   └── validation/
│       └── tests/
│
├── services/
│   └── backend/
│       ├── app/
│       │   ├── api/
│       │   │   ├── auth.py
│       │   │   ├── patients.py
│       │   │   ├── entries.py
│       │   │   ├── comments.py
│       │   │   ├── highlights.py
│       │   │   └── revisions.py
│       │   ├── domain/
│       │   │   ├── access_control/
│       │   │   ├── care_notes/
│       │   │   ├── provenance/
│       │   │   ├── prioritization/
│       │   │   ├── redaction/
│       │   │   └── revisions/
│       │   ├── infrastructure/
│       │   │   ├── database/
│       │   │   ├── storage/
│       │   │   └── llm/
│       │   ├── worker/
│       │   └── main.py
│       └── tests/
│           ├── test_rbac_scope.py
│           ├── test_revision_history.py
│           ├── test_highlight_provenance.py
│           ├── test_concurrent_edits.py
│           └── test_self_learning_importance.py
│
├── supabase/
│   ├── migrations/
│   ├── seed.sql
│   └── config.toml
│
├── docs/
│   ├── blueprint.md
│   ├── architecture.md
│   ├── threat-model.md
│   ├── demo-script.md
│   ├── requirements-traceability.md
│   ├── submission-checklist.md
│   ├── phase-1-foundation.md
│   ├── phase-2-core-patient-experience.md
│   ├── phase-3-trust-and-collaboration.md
│   ├── phase-4-ai-pipeline.md
│   ├── phase-5-proof-and-presentation.md
│   ├── phase-6-data-decay.md
│   └── technical-brief/
│
├── scripts/
│   ├── seed-demo-data.sh
│   └── benchmark-glance-view.sh
│
├── .env.example
├── docker-compose.yml
├── Makefile
├── README.md
└── ATTRIBUTION.txt
```

## 7. User Roles and Permissions

The application supports four roles:

- Patient
- Staff
- Clinician
- Admin

All staff, clinician, and admin access is scoped to a clinic. A user with access to one clinic must not be able to retrieve records from another clinic.

| Action | Patient | Staff | Clinician | Admin |
|---|---:|---:|---:|---:|
| View own patient-facing summary | Yes | N/A | N/A | N/A |
| View clinic patient-facing summary | No | Yes | Yes | Yes |
| View raw AI-scribed notes | No | Yes, within clinic | Yes, within clinic | Yes, read-only oversight |
| View internal comments | No | Yes | Yes | Yes |
| Add staff note | No | Yes | No | No |
| Edit staff note | No | Own or permitted | No | No |
| Add clinician section | No | No | Yes | No |
| Edit clinician section | No | No | Own or permitted | No |
| Review suggested highlights | No | Optional | Yes | Read-only |
| View revision history | No | Limited | Yes | Yes |
| Manage clinic membership | No | No | No | Yes |

Authorization is enforced at three layers:

1. The frontend only renders permitted controls.
2. FastAPI validates identity, clinic membership, role, ownership, and operation.
3. PostgreSQL Row-Level Security prevents unauthorized row access.

Frontend checks are a usability feature, not a security boundary.

The service-role key must never be included in frontend code. Patient-facing endpoints must query a deliberately restricted response shape and must not fetch internal content merely to hide it in the browser.

Admin is a read-only oversight role for patient and clinical content. An administrator who must edit clinical content needs a separate clinician membership, preserving the correct author role and audit trail.

## 8. Domain Model

Every clinic-owned row contains a `clinic_id` to support tenant isolation and efficient authorization policies.

### 8.1 Identity and Tenancy

```text
clinics
- id
- name
- created_at

profiles
- id
- auth_user_id
- display_name
- created_at

clinic_memberships
- clinic_id
- profile_id
- role: staff | clinician | admin
- created_at

patients
- id
- clinic_id
- linked_profile_id nullable
- synthetic_identifier
- display_name
- created_at
```

Authorization roles must be stored in protected membership data or protected application metadata, not user-editable profile metadata.

### 8.2 Source Records, Care Notes, Entries, and Sections

```text
source_records
- id
- clinic_id
- patient_id
- source_type: manual | doctor_consult | nurse_consult | ai_patient_session | system
- external_reference nullable
- storage_object_path nullable
- occurred_at
- metadata
- created_at

care_notes
- id
- clinic_id
- patient_id
- current_version
- created_at
- updated_at

entries
- id
- clinic_id
- patient_id
- care_note_id
- author_id nullable
- author_role
- entry_type
- visibility: internal | patient_facing
- content
- source_record_id
- source_start_offset nullable
- source_end_offset nullable
- current_version
- occurred_at
- created_at
- updated_at

note_sections
- id
- clinic_id
- patient_id
- care_note_id
- section_type: assessment | plan | staff_note | patient_instruction
- owner_role: staff | clinician | system
- content
- current_version
- created_at
- updated_at
```

`source_records` is the canonical provenance target for original interactions and imported source messages. Every entry points to a source record. A manual entry may point to a manual source record representing itself; an AI-scribed entry points to the doctor consult, nurse consult, or AI-patient session from which it was generated.

AI-scribed notes are modelled as typed `entries`, not as a disconnected table. They must use `author_role = system`, a null system author ID or a dedicated immutable system principal, one of the three required AI entry types, and a resolvable `source_record_id`.

Editable Care Note sections are separate versioned resources. This makes role ownership and concurrent editing deterministic: staff own staff sections, clinicians own assessment and plan sections, and patient instructions are published through an authorized clinical workflow.

Suggested entry types:

```text
staff_note
clinician_note
patient_insight
patient_instruction
ai_doctor_consult_summary
ai_nurse_consult_summary
ai_patient_session_summary
system_event
```

### 8.3 Revisions

```text
entry_versions
- id
- entry_id
- version_number
- content_snapshot
- changed_by
- changed_by_role
- change_reason
- created_at

section_versions
- id
- section_id
- version_number
- content_snapshot
- changed_by
- changed_by_role
- change_reason
- created_at
```

Use immutable full snapshots for the prototype. Generate a display diff between any selected historical version and the current version to provide the required "view changes since X" behavior. Reverting creates a new version; it never deletes historical versions.

### 8.4 Comments, Mentions, and Assignments

```text
comments
- id
- clinic_id
- entry_id
- parent_comment_id nullable
- author_id
- body
- status: open | resolved
- assigned_to nullable
- created_at
- resolved_at nullable

mentions
- id
- comment_id
- mentioned_profile_id
- created_at
```

### 8.5 Highlights and Provenance

```text
highlights
- id
- clinic_id
- patient_id
- source_entry_id
- source_version_id
- source_start_offset
- source_end_offset
- quoted_text
- normalized_claim
- risk_level
- risk_reason
- score
- status: suggested | accepted | rejected
- generated_by: rule | ai | clinician
- reviewed_by nullable
- created_at
- updated_at
```

A provenance pointer is structured data rather than only a URL:

```json
{
  "entry_id": "uuid",
  "version_id": "uuid",
  "start_offset": 142,
  "end_offset": 197,
  "quoted_text": "Patient reported worsening shortness of breath."
}
```

Offsets use a half-open `[start, end)` range of Unicode code points over NFC-normalized canonical plaintext. The backend owns normalization and validates that slicing the historical source with those offsets equals `quoted_text`; the frontend does not invent or reinterpret offsets.

The frontend derives a deep link from the pointer:

```text
/patients/{patientId}?entry={entryId}&start=142&end=197
```

`quoted_text` is stored as an integrity fallback. If the current entry changes, the historical source remains resolvable through `source_version_id`.

Exact source resolution is a publication invariant. A highlight may enter the Glance View only when its source entry, historical version, start offset, end offset, and quoted text resolve successfully. Entry-only fallback provenance is not sufficient.

### 8.6 Care Tasks

```text
care_tasks
- id
- clinic_id
- patient_id
- source_entry_id nullable
- title
- assigned_to nullable
- status: open | in_progress | completed | cancelled
- priority
- due_at nullable
- created_at
- updated_at
```

### 8.7 Audit Events

```text
audit_events
- id
- clinic_id
- patient_id nullable
- actor_id
- actor_role
- action
- resource_type
- resource_id
- metadata
- created_at
```

Audit metadata describes who performed an action and what resource changed without duplicating raw clinical text into logs.

### 8.8 Background Jobs

```text
jobs
- id
- clinic_id
- job_type
- payload
- idempotency_key
- status: pending | processing | completed | failed
- attempts
- max_attempts
- available_at
- locked_at nullable
- locked_by nullable
- last_error nullable
- created_at
- completed_at nullable
```

## 9. Frontend Components

### 9.1 Authentication and Role Switcher

Provide seeded demo accounts for patient, staff, clinician, and admin roles. A development-only role switcher may accelerate demonstrations, but it must still obtain a real role-scoped session rather than changing authorization only in client state.

### 9.2 Patient Selector

The selector lists only patients accessible within the authenticated user's clinic. Include at least two clinics in seed data to prove tenant isolation.

### 9.3 Glance View / Top Card

The glance card contains a small, deliberately prioritized set of items:

- Critical risks
- Current concern
- Unresolved actions
- Important medications or allergies
- Recent significant changes
- Clinician-confirmed items
- Suggested items awaiting review

Each item displays:

- Concise claim
- Risk or importance reason
- Status
- Source type and date
- Link to the exact timeline source
- Accept or reject controls where appropriate

### 9.4 Longitudinal Timeline

The timeline supports:

- Reverse or forward chronological display
- Date grouping
- Entry-type filters
- Author and role labels
- Clear AI-generated labels
- Patient-provided insights and AI-patient session key questions
- Source navigation
- Deep links to entries and spans
- Comments and editing actions
- System events
- Live updates when authorized collaborators add entries, comments, tasks, or highlight decisions

### 9.5 Section-Level Note Editor

Prefer section-level collaboration over a Google Docs-style character-level editor. Suggested sections include:

- Assessment
- Plan
- Staff note
- Patient instruction

Section-level ownership makes permissions, versioning, and concurrent-edit behavior explicit and testable.

### 9.6 Comments Panel

The comments panel supports:

- Threads
- Replies
- Mentions
- Assignment
- Resolve and unresolve actions

### 9.7 Revision Viewer

The revision viewer supports:

- Ordered version list
- Actor and timestamp
- Before-and-after diff
- Change reason
- Revert action

### 9.8 Patient View

Use a separate patient-facing route and response schema. It may include:

- Patient-facing summaries
- Instructions
- Follow-up tasks intended for the patient

It must never include:

- Internal comments
- Raw AI-scribed notes
- Internal staff notes
- Clinician-only reasoning
- Internal audit information

## 10. API Responsibilities

Suggested API groups:

```text
/auth
/patients
/patients/{patient_id}/glance
/patients/{patient_id}/timeline
/sources
/entries
/entries/{entry_id}
/entries/{entry_id}/versions
/entries/{entry_id}/revert
/entries/{entry_id}/comments
/sections/{section_id}
/sections/{section_id}/versions
/sections/{section_id}/revert
/highlights
/highlights/{highlight_id}/accept
/highlights/{highlight_id}/reject
/tasks
/jobs
```

All mutation endpoints must:

1. Validate the authenticated identity.
2. Resolve clinic membership.
3. Authorize the operation by role and resource.
4. Validate an expected version where relevant.
5. Perform the domain mutation transactionally.
6. Create an audit event.
7. Return the updated resource version.

## 11. Concurrent Editing Strategy

Use optimistic concurrency control rather than CRDTs.

Lightweight realtime collaboration is required for timeline entries, comments, tasks, and highlight decisions. Supabase Realtime invalidates or updates authorized client queries. Character-level co-editing, shared cursors, and CRDTs remain out of scope.

An update includes the version the client last read:

```json
{
  "expected_version": 4,
  "content": "Updated plan"
}
```

The database update succeeds only when `current_version = expected_version`.

- Edits to different entries or sections can succeed independently.
- Two edits to the same version result in one success and one `409 Conflict`.
- The conflict response returns the latest version.
- No edit is silently overwritten.
- The user can reload, compare, merge, and retry.

## 12. Redaction and AI Processing

### 12.1 Processing Order

```text
Raw input
  → deterministic redaction
  → redaction verification
  → sanitized processing record
  → LLM request
  → structured output validation
  → provenance attachment
  → human review
  → glance-card eligibility
```

### 12.2 Minimum Redaction Rules

Redact at least:

- Personal names
- IC, NRIC, FIN, or similar identity numbers
- Phone numbers
- Email addresses
- Dates of birth, if present
- Addresses, if present

Use synthetic data throughout the prototype, but still demonstrate the redaction pipeline.

### 12.3 AI Safety Rules

- Never send unredacted text to the LLM.
- Never log raw clinical request bodies.
- Store the model identifier and prompt version with generated output.
- Require structured JSON output validated by Pydantic.
- Reject malformed or incomplete model output.
- Mark AI output as system-authored.
- AI highlights begin as `suggested`.
- A clinician can accept or reject each suggestion quickly.
- A clinician-confirmed entry outranks conflicting AI or patient memory.
- Contradictions are flagged for review rather than silently merged.
- Every AI-derived item contains resolvable provenance.
- A proposed highlight that cannot be mapped to an exact source entry, historical version, and source span is rejected rather than published.

## 13. Background Job Lifecycle

Example AI-scribe processing flow:

```text
1. API accepts synthetic consultation text or a source reference.
2. API applies deterministic redaction.
3. API verifies that prohibited identifier patterns are absent.
4. API stores the sanitized input.
5. API creates an idempotent pending job.
6. Worker atomically claims the job.
7. Worker calls the LLM.
8. Worker validates structured output.
9. Worker creates the AI-scribed entry and source metadata.
10. Worker creates suggested highlights with provenance.
11. Worker marks the job complete.
12. UI refreshes or receives a realtime update.
```

Retries must not produce duplicate timeline entries or highlights. Use an idempotency key associated with the source session and job type.

## 14. Importance Ranking

Use an explainable scoring model:

```text
importance_score =
    risk_weight
  + unresolved_task_weight
  + recency_weight
  + clinician_confirmed_weight
  + entity_weight
  + interaction_feedback_weight
  - age_decay
  - rejection_penalty
```

Illustrative weights:

| Signal | Weight |
|---|---:|
| Critical risk | +50 |
| Unresolved task | +25 |
| Clinician-confirmed item | +20 |
| Medication or allergy entity | +15 |
| Occurred within seven days | +12 |
| Similar topic repeatedly pinned | +10 |
| Older than 180 days | -10 |
| Similar suggestion previously rejected | -15 |

Every ranked item exposes its explanation:

```json
{
  "score": 82,
  "risk_reason": "High-risk symptom with unresolved clinician follow-up",
  "factors": [
    "risk_level: high",
    "task_status: unresolved",
    "age: 2 days"
  ]
}
```

### 14.1 Adaptive Component

The adaptive behavior learns presentation preferences, not medical truth. It is not a reinforcement-learning system: it does not train a policy, optimize a clinical reward, or autonomously change medical decisions. It is a deterministic online weight update derived from explicit user interactions.

```text
topic_preferences
- clinic_id
- actor_role
- topic_key
- accepted_count
- rejected_count
- pinned_count
- learned_weight
- updated_at
```

Accepting, pinning, editing, or commenting on a topic increases its future interaction weight according to a documented formula. Rejection decreases it. Hard-coded safety floors ensure high-risk items cannot be suppressed solely by user feedback. Every score exposes its base factors and learned adjustment, and the adjustment can be reset.

## 15. Database and Storage Setup

### 15.1 Supabase Project

Create one Supabase project for the challenge.

Configure:

- Email and password authentication
- Seeded demo accounts
- PostgreSQL schema migrations
- Row-Level Security on every exposed application table
- Separate `SELECT`, `INSERT`, `UPDATE`, and `DELETE` policies
- Private object storage
- Realtime subscriptions for entries, comments, tasks, and highlight decisions
- TLS for deployed web, API, database, storage, and LLM connections
- Provider-managed encryption at rest for PostgreSQL and private object storage, documented in the technical brief

### 15.2 Required Indexes

At minimum, index:

- All primary and foreign keys
- `clinic_id`
- `(clinic_id, patient_id)`
- `(patient_id, occurred_at)`
- `(entry_id, version_number)`
- `(patient_id, status)` for tasks and highlights
- `(status, available_at)` for jobs
- Unique job idempotency keys

### 15.3 Storage Buckets

Create a private bucket named:

```text
consult-recordings
```

Use object keys such as:

```text
{clinic_id}/{patient_id}/{session_id}/{filename}
```

Apply clinic-scoped access policies and use short-lived signed URLs. Do not make clinical artifacts public.

### 15.4 Environment Variables

Document variables in `.env.example` without committing secrets:

```text
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=
LLM_API_KEY=
```

## 16. Synthetic Demo Data

Seed at least:

- Two clinics to prove tenant isolation
- One admin
- Two clinicians
- Two staff users
- One patient-linked account
- Several synthetic patients
- Timeline entries from multiple dates
- Manual staff and clinician notes
- All three AI-scribed entry types
- Patient-provided insights and AI-patient key questions
- Source records for every manual and AI-scribed entry
- Patient-facing instructions
- Resolved and unresolved tasks
- Open and resolved comments
- Accepted and rejected highlights
- Conflicting AI and clinician information
- Multiple entry versions

The primary demo patient should contain a coherent story that exercises every main UI component without overwhelming the reviewer.

## 17. Automated Test Plan

### 17.1 `test_rbac_scope.py`

Assert that:

- Staff cannot create or edit clinician-owned content.
- Clinicians cannot create or edit staff-owned content.
- A user cannot access another clinic's patients.
- A patient cannot retrieve raw AI-scribed notes.
- A patient cannot retrieve internal comments.
- An admin remains limited to their clinic.
- Both API authorization and database policies reject prohibited access.

### 17.2 `test_revision_history.py`

Assert that:

- Editing increments the version.
- Previous snapshots remain immutable.
- Reverting creates a new version.
- Revert content matches the selected prior snapshot.
- The current state can be compared with any selected historical version ("changes since X").
- The audit event identifies the actor and action.
- Unauthorized users cannot revert.

### 17.3 `test_highlight_provenance.py`

Assert that:

- Every highlight has a source entry and version.
- At least one generated highlight originates from an AI-scribed note.
- Source offsets fall within the source content.
- The selected substring equals `quoted_text`.
- Source entry and highlight belong to the same patient and clinic.
- A historical source remains resolvable after later edits.
- The source-navigation endpoint resolves the exact entry and span.
- A highlight without exact, valid source resolution is rejected.

### 17.4 `test_concurrent_edits.py`

Assert that:

- Concurrent updates to different entries or sections both succeed.
- Concurrent updates to the same expected version produce one success and one `409 Conflict`.
- No successful edit is silently lost.
- The conflict response contains the latest version.
- A client can merge and retry deterministically.

### 17.5 `test_self_learning_importance.py`

Assert that:

- A topic begins with a deterministic base score.
- Pinning or accepting the topic records feedback.
- A similar later suggestion receives a higher interaction component.
- Repeated rejection lowers the interaction component.
- A high-risk safety floor cannot be removed by feedback.

### 17.6 Additional Backend Tests

- `test_redaction.py`
- `test_patient_view_serialization.py`
- `test_clinic_isolation.py`
- `test_audit_log.py`
- `test_job_idempotency.py`
- `test_glance_ranking.py`
- `test_conflict_resolution.py`

### 17.7 Frontend Tests

Test that:

- Patient UI never renders internal actions or content.
- Highlight selection scrolls to and marks the exact source.
- AI-generated entries are visually distinct.
- Revision diff and revert confirmation work.
- Accepted and rejected highlight states update correctly.
- Loading, empty, unauthorized, and error states are clear.

### 17.8 End-to-End Tests

Use Playwright for these primary paths:

1. Staff adds a note, comments, mentions a clinician, and assigns a task.
2. Clinician opens the task, highlights source text, and verifies provenance navigation.
3. Clinician edits a section, views the diff, and reverts it.
4. Patient attempts to open internal content and receives a server-side denial.

## 18. Performance Measurement

Measure the actual endpoint used by the glance card.

Suggested method:

1. Seed 200 to 500 entries for one patient.
2. Create representative highlights, comments, and open tasks.
3. Warm the database connection and endpoint.
4. Run at least 100 requests.
5. Record P50, P95, P99, error rate, and dataset size.
6. Record the client machine and service/database regions.
7. Confirm that warm-path P95 is 300 ms or less, or clearly document the approximation and bottleneck.

Avoid unbounded joins and compute glance-card output ahead of time when practical. Cache or materialize the small read model used by the Top Card, and update it when relevant entries, tasks, or highlight decisions change.

## 19. Deployment

Suggested challenge deployment:

- Frontend: Vercel
- API: Railway, Render, or Fly.io
- Worker: a second process on the same backend platform
- Database, Auth, and Storage: Supabase
- LLM: one provider accessed only from the backend or worker

Every deployed connection uses TLS. The technical brief identifies the platform controls that provide encryption at rest for PostgreSQL and private object storage.

Keep the API, worker, and database in compatible nearby regions to reduce latency.

Local topology:

```text
Browser
   ↓
Next.js on localhost:3000
   ↓
FastAPI on localhost:8000
   ↓
Supabase local stack or hosted project
   ↑
Python worker
```

## 20. Demonstration Scenarios

### Scenario A: Glance View and AI Scribe

1. Staff opens the primary synthetic patient.
2. The Top Card communicates the main concern and open action immediately.
3. Staff opens an AI-derived highlight.
4. The application jumps to the exact AI-scribed entry and source span.
5. The user sees why the item was ranked and whether it has been clinician-confirmed.

### Scenario B: Collaboration, Audit Trail, and Learning

1. Staff adds a note.
2. Staff comments, mentions a clinician, and assigns follow-up.
3. Clinician opens the task and highlights a phrase.
4. Clinician edits the plan.
5. Revision history shows the change.
6. Clinician reverts to a previous version.
7. Accepting or pinning the highlight increases the future weight of a similar topic.

### Scenario C: Longitudinal Context

1. Show timeline entries from multiple visits and roles.
2. Explain the difference between manual and AI-generated entries.
3. Demonstrate that recent unresolved and clinician-confirmed items outrank older context.
4. Explain how older low-value data could be compressed without deleting source history.

### Scenario D: Security Boundary

1. Switch to the patient account.
2. Show the patient-facing summary and instructions.
3. Attempt to request an internal comment or raw AI entry directly.
4. Show that the server denies access.
5. Switch clinics and demonstrate tenant isolation.

## 21. 72-Hour Implementation Sequence

### Phase 1: Foundation

- Initialize the monorepo.
- Create the Supabase project.
- Write schema migrations.
- Add synthetic seed data.
- Configure authentication.
- Implement clinic-scoped authorization.
- Write the RBAC tests first.

### Phase 2: Core Patient Page

- Implement the patient selector.
- Implement the longitudinal timeline.
- Implement the glance card.
- Add manual entry creation.
- Add role-specific views.
- Add care tasks and lightweight live updates.

### Phase 3: Trust and Collaboration

- Add immutable entry versions.
- Add revision comparison and revert.
- Add audit events.
- Add highlights and exact provenance.
- Add comments, mentions, and assignments.
- Add optimistic concurrency handling.

### Phase 4: AI Pipeline

- Implement deterministic redaction.
- Add the job table and worker.
- Add structured LLM summaries.
- Generate suggested highlights.
- Add accept and reject feedback.
- Add transparent ranking factors.
- Add deterministic adaptive preference weights and the required learning test.

### Phase 5: Proof and Presentation

- Complete required tests.
- Run the performance benchmark.
- Finalize demo fixtures.
- Write the technical brief.
- Create the architecture diagram.
- Complete README and attribution.
- Record the demo video.

### Phase 6: Hybrid Storage and Data Decay

- Define hot, warm, and archived data tiers.
- Preserve provenance, audit history, accepted highlights, and unresolved work without decay.
- Generate immutable roll-up summaries for older low-value context.
- Verify that archived sources remain resolvable.
- Implement after the core submission is stable; include the architectural policy in the technical brief even if full tier migration is not completed.

## 22. Pre-Coding Checklist

Before feature implementation begins:

- [ ] Confirm the MVP and deferred scope.
- [ ] Write the final primary demo-patient story.
- [ ] Define roles and permission matrix.
- [ ] Draw the entity-relationship diagram.
- [ ] Define entry types and visibility rules.
- [ ] Define the structured provenance format.
- [ ] Decide the source-offset convention.
- [ ] Define optimistic concurrency behavior.
- [ ] Define the glance-card scoring formula.
- [ ] Define the redaction patterns and verification behavior.
- [ ] Create Supabase development and deployment projects.
- [ ] Create versioned database migrations.
- [ ] Create synthetic seed accounts and records.
- [ ] Write RBAC and provenance tests before UI work.
- [ ] Define the exact benchmark method.
- [ ] Write the demo script.
- [ ] Create `.env.example`.
- [ ] Create `ATTRIBUTION.txt` at project start and update it continuously.
- [ ] Record the exact submission deadline, recipients, subject, and contact deliverables in `docs/submission-checklist.md`.

## 23. Definition of Done

The build is complete when:

- The application runs from documented setup instructions.
- The principal demo scenarios work without manual database intervention.
- All required automated tests pass.
- Authorization is enforced on the server and in the database.
- Patient responses exclude all internal content.
- Every glance-card highlight resolves to an exact historical source.
- Revision history and revert behavior are demonstrable.
- Concurrent same-section edits do not silently overwrite one another.
- Redaction is applied and verified before every LLM call.
- A genuine AI-scribe flow produces validated, system-authored output.
- Entries, comments, tasks, and highlight decisions update live for authorized connected users.
- The worker is durable and idempotent.
- Glance-view latency is measured and documented.
- The repository contains no secrets or real patient data.
- TLS and encryption-at-rest controls are documented and verified for the deployed stack.
- README setup and run instructions are complete.
- The technical brief, architecture diagram, attribution file, and demo video are ready for submission.

## 24. Guiding Product Principle

The application should not ask users to trust an unexplained AI conclusion. It should help them understand what matters, show why it matters, preserve the human decision, and make the underlying source immediately accessible.
