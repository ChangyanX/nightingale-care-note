# P1-T04 — Foundation Schema

**Status:** Implemented and parser-verified; database apply pending  
**Full estimate:** 2 hours  
**16-hour path:** 35 minutes  
**Dependencies:** P1-T03

## Objective

Create the minimum relational model needed to prove tenancy, content ownership, provenance, revision history, and patient visibility before feature UI work begins.

## Required tables

- `clinics`
- `profiles`
- `clinic_memberships`
- `patients`
- `source_records`
- `care_notes`
- `entries`
- `note_sections`
- `entry_versions`
- `section_versions`
- Minimal `comments`
- `audit_events`

## Required invariants

1. Every tenant-owned table includes `clinic_id`.
2. A patient has exactly one Care Note within a clinic.
3. Entry types include manual, patient, all three required AI-scribed types, and system events.
4. AI entries use `author_role = system` and require a source record.
5. Note sections have an explicit owner role.
6. Versions are immutable and unique by resource/version number.
7. Patient-facing visibility is explicit, never inferred from UI location.
8. Foreign keys prevent cross-patient and cross-clinic provenance relationships.
9. Provenance offsets use half-open Unicode-code-point ranges over NFC-normalized plaintext.
10. Useful clinic, patient, timeline, version, and status indexes are created.

## Optional work

- Database trigger for automatic audit metadata.
- Generated columns for search.
- Database-level enum types instead of check constraints.

## Acceptance criteria

- [ ] Migration applies to an empty database.
- [ ] Migration rollback/reset path is documented.
- [ ] A second application resets to the same schema without dashboard edits.
- [ ] Cross-clinic foreign relationships are structurally prevented where feasible.
- [ ] AI entry metadata and source requirements are enforced.
- [ ] Version rows cannot be updated or deleted by ordinary authenticated roles.
- [ ] Admin clinical writes are not granted by the schema/policy design.

## Evidence

- Versioned migration file
- Schema diagram or generated relation list
- Migration/reset output
