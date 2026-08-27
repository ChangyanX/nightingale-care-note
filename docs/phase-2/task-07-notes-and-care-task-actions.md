# P2-T07 — Notes and Care-Task Actions

**Status:** Pending  
**Full estimate:** 1 hour  
**16-hour path:** 20 minutes  
**Dependencies:** P2-T02 through P2-T06

## Objective

Let permitted roles create a manual timeline entry and move an authorized care
task through its basic lifecycle without weakening ownership rules.

## Required work, in order

1. Add caller-scoped create/update task database functions or API mutations.
2. Add Pydantic request validation and transactional audit events.
3. Add the manual note form for staff, clinician, and patient-permitted entry types.
4. Add open/in-progress/completed task actions for staff and clinicians.
5. Hide irrelevant controls by role while relying on API/RLS for enforcement.
6. Refresh Glance and timeline state after successful mutations.
7. Show validation, conflict, forbidden, and retry feedback.

## Must be done

- Staff cannot create or edit clinician content.
- Clinicians cannot overwrite staff-owned notes.
- Admin receives no clinical mutation control and direct calls are denied.
- Patient entries remain patient insights; patients cannot create raw AI or staff notes.
- Entry creation preserves source provenance and creates an initial version/audit event.

## Optional

- Due-date editing.
- Task assignment UI.
- Optimistic UI before server confirmation.

## Acceptance criteria

- [ ] A staff user creates a staff note and sees it in the timeline.
- [ ] A clinician creates an allowed clinician entry.
- [ ] A permitted task state change updates the Glance action.
- [ ] Cross-role, admin, patient, and cross-clinic invalid mutations are denied.
- [ ] Invalid input produces specific, non-sensitive feedback.
- [ ] Mutation success creates the expected audit/version records.

## Evidence

- Task migration/RPC and API routes
- Note/task UI controls
- Authorization and mutation tests
- Hosted role walkthrough

## Done when

The reviewer can make one useful change while the role and provenance boundaries
remain demonstrably intact.
