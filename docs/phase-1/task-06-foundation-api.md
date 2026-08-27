# P1-T06 — Foundation API

**Status:** Implemented and locally verified; live Supabase Auth pending  
**Full estimate:** 1 hour  
**16-hour path:** 20 minutes  
**Dependencies:** P1-T02, P1-T05

## Objective

Expose the minimum authenticated API required to validate identity, clinic scope, patient visibility, and role-owned writes.

## Required endpoints

```text
GET  /health
GET  /me
GET  /patients
GET  /patients/{patient_id}
GET  /patients/{patient_id}/timeline
POST /entries
PATCH /entries/{entry_id}
```

## Required behavior

1. Verify the Supabase JWT and derive the caller identity server-side.
2. Resolve memberships from protected database data.
3. Pass the caller token to normal database operations so RLS remains active.
4. Return patient-safe schemas from patient routes.
5. Validate role-owned entry types and visibility.
6. Return typed errors without including raw clinical content or stack details.
7. Create request IDs and metadata-only audit events for mutations.

## Optional work

- OpenAPI-generated frontend client.
- Pagination beyond a simple bounded limit.
- Structured access logs.

## Acceptance criteria

- [ ] Anonymous access is denied except `/health`.
- [ ] `/me` reports authenticated profile and memberships.
- [ ] Patient lists are clinic-scoped.
- [ ] Timeline reads respect internal versus patient-facing visibility.
- [ ] Staff/clinician write boundaries are enforced before and by the database.
- [ ] Responses and logs contain no secret or unredacted request body.

## Evidence

- OpenAPI output
- Endpoint tests
- Sample authorized and denied responses
