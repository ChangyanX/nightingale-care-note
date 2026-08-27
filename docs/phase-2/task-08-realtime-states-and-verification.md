# P2-T08 — Realtime, States, and Verification

**Status:** Pending  
**Full estimate:** 1-1.5 hours  
**16-hour path:** 15 minutes  
**Dependencies:** P2-T05 through P2-T07

## Objective

Complete the Phase 2 experience with authorized live refresh, resilient visual
states, focused automated coverage, and reproducible handoff evidence.

## Required work, in order

1. Subscribe to scoped `entries` and `care_tasks` changes through Supabase Realtime.
2. Invalidate or refresh only the affected patient timeline, Glance, and task data.
3. Tear down subscriptions on patient/session change and component unmount.
4. Verify loading, empty, forbidden, network-error, mutation-error, and stale-session states.
5. Add API, component, and focused browser tests for the critical path.
6. Run two authorized sessions and verify entry/task changes without reload.
7. Run lint, type checking, backend tests, production build, and live RLS tests.
8. Record screenshots, commands, and remaining optional scope.

## Must be done

- Subscriptions must not use the service-role key.
- Events trigger a server-authorized refetch rather than trusting arbitrary payloads.
- Duplicate events must not duplicate visible entries or tasks.
- A lost realtime channel must not make ordinary reads or manual refresh unusable.
- Test logs and screenshots must not expose access tokens or passwords.

## Optional

- Reconnect indicator.
- Toast showing which collaborator changed a resource.
- Responsive/mobile and keyboard-polish pass.
- Timeline filters and URL-persisted filter state.

## Acceptance criteria

- [ ] A new entry appears in a second authorized session without page reload.
- [ ] A task-state change updates the second session's Glance action.
- [ ] Cross-clinic and patient sessions receive no internal event-derived content.
- [ ] Repeated events do not duplicate UI rows.
- [ ] Loading, empty, forbidden, and error states are understandable.
- [ ] Production build, lint, type checks, backend tests, and live RLS checks pass.
- [ ] Phase 2 README statuses and evidence links reflect the implemented result.

## Evidence

- Realtime subscription module and tests
- Component/browser test results
- Two-session verification note or demo capture
- Updated `docs/phase-2/README.md`

## Done when

The Phase 2 completion gate in `docs/phase-2/README.md` is satisfied and the
remaining gaps are explicitly optional or assigned to a later phase.
