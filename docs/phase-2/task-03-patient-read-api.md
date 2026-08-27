# P2-T03 — Patient Read API

**Status:** Locally verified; hosted integration pending  
**Full estimate:** 1-1.5 hours  
**16-hour path:** 25 minutes  
**Dependencies:** P2-T01, P2-T02

## Objective

Expose bounded, caller-scoped patient, timeline, Glance, source-metadata, and
task responses without broadening the permissions already enforced by RLS.

## Required work, in order

1. Finalize Pydantic response models for patient detail, timeline entries,
   source summaries, Glance items, and care tasks.
2. Extend the timeline query with the source type/reference needed for visible
   provenance.
3. Add `GET /patients/{patient_id}/glance` with a bounded deterministic result.
4. Add `GET /patients/{patient_id}/tasks` for authorized task reads.
5. Ensure missing and unauthorized patients have a non-leaking response.
6. Keep patient-facing response models structurally separate from clinical ones.
7. Add mocked gateway contract tests and live integration cases.

## Must be done

- The server selects only fields needed by the response.
- Glance ordering is deterministic and returns at most the documented limit.
- Provenance includes source ID, type, reference, and occurrence time.
- The endpoint does not fetch all internal content and hide it after the fact.
- Errors contain no Supabase response body, credential, or clinical text.

## Optional

- Cursor pagination for timelines longer than the demo fixture.
- `ETag` or cache headers for the Glance response.
- Timeline filters for entry type, role, and date.

## Acceptance criteria

- [ ] Clinic-scoped patient list and detail responses validate against models.
- [ ] Timeline entries expose visible provenance metadata.
- [ ] Glance contains current concern, recent change/risk, and an open action.
- [ ] Patient calls never include internal comments or raw AI summaries.
- [ ] Unauthorized and nonexistent resources do not reveal tenant membership.
- [ ] Response bounds and sort order have automated tests.
- [ ] OpenAPI exposes the intended response schemas.

## Evidence

- API router and Pydantic schemas
- Gateway contract tests
- Live RLS/API tests after hosted project migration

## Done when

The frontend can render the complete core patient experience without directly
querying unrestricted tables or recreating authorization logic.
