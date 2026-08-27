# P1-T05 — Authentication and Row-Level Security

**Status:** Implemented and contract-tested; live RLS execution pending  
**Full estimate:** 1.5 hours  
**16-hour path:** 35 minutes  
**Dependencies:** P1-T04

## Objective

Enforce clinic, role, resource ownership, and patient visibility at the server and database boundaries.

## Required work

1. Enable RLS on every exposed application table.
2. Revoke default access and grant only the operations needed by `authenticated` users.
3. Add clinic-membership helper functions with stable, non-user-editable role data.
4. Create explicit policies for each `SELECT`, `INSERT`, `UPDATE`, and `DELETE` operation.
5. Ensure staff cannot write clinician-owned sections and clinicians cannot write staff-owned sections.
6. Ensure patients can access only their linked patient-facing records.
7. Ensure patients cannot read internal comments or raw AI-scribed notes.
8. Ensure admins have read-only clinical oversight and membership-management privileges.
9. Ensure user request paths execute with the caller's JWT.
10. Reserve service-role access for the internal worker and setup only.

## Required denial cases

- Cross-clinic read and write
- Staff writing or editing as clinician
- Clinician writing or editing as staff
- Patient reading raw AI content
- Patient reading internal comments
- Patient changing visibility
- Admin changing clinical content without a clinician role

## Acceptance criteria

- [ ] All exposed tables have RLS enabled.
- [ ] Missing policies deny access by default.
- [ ] Authorization roles cannot be changed through user-editable metadata.
- [ ] API checks and RLS agree on every required role rule.
- [ ] A service-role credential never appears in frontend code or ordinary API clients.
- [ ] Denial cases return stable forbidden/not-found behavior without leaking record existence.

## Evidence

- RLS migration
- Policy inventory
- Passing authorization tests
