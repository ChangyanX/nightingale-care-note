# P1-T08 — RBAC Tests and Phase Handoff

**Status:** Contract tests pass; five live RLS integration checks pending  
**Full estimate:** 1 hour  
**16-hour path:** 20 minutes  
**Dependencies:** P1-T05, P1-T06, P1-T07

## Objective

Prove the security boundary and leave a reproducible handoff for Phase 2.

## Required tests

Create `services/backend/tests/test_rbac_scope.py` covering:

1. Staff cannot create or edit clinician-owned content.
2. Clinician cannot create or edit staff-owned content.
3. Clinic A users cannot read or mutate Clinic B records.
4. Patient cannot access internal comments.
5. Patient cannot access raw AI-scribed notes.
6. Patient can access their own patient-facing summary/instructions.
7. Read-only admin cannot change clinical content.
8. Admin cannot access another clinic.
9. API denial and direct database/RLS denial agree.

## Required handoff

- Document install, configure, migrate, seed, start, lint, and test commands.
- Record any hosted Supabase setup that cannot be automated.
- Record known limitations without weakening acceptance claims.
- Update task statuses and Phase 1 acceptance checklist.

## Acceptance criteria

- [ ] Required RBAC test file exists with named cases.
- [ ] Tests run using one documented command.
- [ ] Tests are independent of execution order.
- [ ] A fresh database can be migrated and seeded before the tests.
- [ ] No required denial is represented only as a frontend test.
- [ ] README accurately describes the current implementation.

## Evidence

- Passing pytest output
- Migration/seed output
- README quick-start verification
- Final `git status --short`
