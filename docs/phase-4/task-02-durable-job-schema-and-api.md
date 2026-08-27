# P4-T02 — Durable Job Schema and API

**Status:** Submission/claim implemented; retry transitions and hosted concurrency pending  
**Full estimate:** 1.25 hours  
**16-hour path:** 30 minutes  
**Dependencies:** P4-T01, Phase 1 RLS

## Objective

Store AI-scribe work durably in PostgreSQL and expose idempotent submission and
status endpoints without exposing worker credentials or raw model payloads.

## Required work, in order

1. Add job type/status enums and an `ai_jobs` table.
2. Store clinic, patient, source record, interaction type, requester,
   idempotency key, attempts, scheduling/claim timestamps, terminal state, and safe error code.
3. Enforce one idempotency key per clinic and one successful output per job.
4. Add caller-scoped RLS: clinical members submit/read; admin reads only; patient has no access.
5. Add a security-invoker submission function that validates source/patient/clinic/type consistency.
6. Add bounded `POST /patients/{id}/scribe-jobs` and `GET /scribe-jobs/{id}` endpoints.
7. Add an atomic worker claim function using `FOR UPDATE SKIP LOCKED`.
8. Add schema, RLS, and API contract tests.

## Must be done

- Repeating the same submission returns the existing job rather than duplicating it.
- Raw transcript text is not stored in the jobs table.
- Status responses contain safe codes, not provider bodies or prompts.
- Only the internal worker can claim, retry, complete, or fail jobs.
- Stale processing claims can be recovered after a documented timeout.

## Optional

- Queue position estimate.
- Job cancellation before claim.
- Realtime job-status publication.

## Acceptance criteria

- [ ] Duplicate idempotency submissions return one job ID.
- [x] Schema/RPC contracts reject a cross-clinic source record.
- [x] RLS contracts keep admin read-only and deny patient job access.
- [ ] Two workers cannot claim the same job.
- [ ] Failed jobs retry within the configured cap and then dead-letter safely.
- [x] Status API is bounded and reveals no clinical or provider payload.

## Done when

The API can acknowledge work immediately and a stopped worker can resume it
without losing or duplicating the requested AI-scribe operation.
