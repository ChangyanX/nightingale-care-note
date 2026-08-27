# P2-T02 — Care Tasks and Realtime Schema

**Status:** SQL implemented; hosted apply pending  
**Full estimate:** 1 hour  
**16-hour path:** 20 minutes  
**Dependencies:** P2-T01

## Objective

Add the smallest secure task model required for actionable Glance content and
configure authorized live-update publication for entries and tasks.

## Required work, in order

1. Add task status and priority enums.
2. Add `care_tasks` with clinic, patient, optional source entry, creator,
   optional assignee, title, status, priority, due time, and timestamps.
3. Add composite foreign keys and indexes for tenant integrity and open-task reads.
4. Enable RLS and grant only the necessary operations.
5. Add policies for clinic-scoped reads, staff/clinician creation and updates,
   patient-safe reads only when explicitly intended, and read-only admin access.
6. Prevent identity fields from changing after creation.
7. add `entries` and `care_tasks` to the Supabase Realtime publication
   idempotently.
8. Seed at least one open and one completed synthetic task.
9. Add SQL parsing and policy-contract tests.

## Must be done

- Cross-clinic task access must fail through RLS.
- Admin cannot create or update clinical tasks.
- A task's clinic and patient must agree through composite constraints.
- Task titles remain concise; raw clinical-note bodies are not duplicated.
- Realtime publication setup must be migration-controlled, not dashboard-only.

## Optional

- Add a task category enum.
- Add a patient-visible flag and patient acknowledgement.
- Add task event history beyond the general audit log.

## Acceptance criteria

- [ ] All task identity and tenancy constraints are enforced by PostgreSQL.
- [ ] Staff and clinicians can read clinic tasks and mutate permitted tasks.
- [ ] Admin can read but cannot mutate tasks.
- [ ] Patients cannot read internal tasks.
- [ ] Cross-clinic reads and writes return no rows or fail safely.
- [ ] Entries and tasks are present in `supabase_realtime` publication.
- [ ] Local and hosted seed paths create equivalent task fixtures.
- [ ] Migration SQL parses and policy tests pass.

## Evidence

- Versioned migration under `supabase/migrations/`
- `supabase/seed.sql`
- `services/backend/scripts/seed_hosted.py`
- SQL/RLS contract tests

## Done when

The API can rely on RLS-safe task rows and subscribed clients can receive entry
and task changes without dashboard configuration drift.
