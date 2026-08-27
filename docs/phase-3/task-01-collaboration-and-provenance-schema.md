# P3-T01 — Collaboration and Provenance Schema

**Status:** SQL implemented; hosted apply pending
**Full estimate:** 1.25 hours
**16-hour path:** 25 minutes
**Dependencies:** Phase 1 foundation schema, Phase 2 `care_tasks`

## Objective

Create migration-controlled data structures for threaded comments, mentions,
assignments, and highlights whose clinic, patient, entry, historical version,
and source span are enforced by PostgreSQL.

## Required work, in order

1. Extend comments with parent-thread and assignee fields.
2. Add composite comment identity needed for tenant-safe parent references.
3. Add a mentions table tied to the same clinic, patient, and comment.
4. Add highlight status, risk, and generator enums.
5. Add highlights with source entry/version, offsets, quote, normalized claim,
   reason, score, review identity, and timestamps.
6. Add composite foreign keys proving that source entry/version and highlight
   belong to the same clinic and patient.
7. Validate the exact historical substring in a database trigger.
8. Protect comment/highlight provenance and ownership fields from mutation.
9. Add RLS grants/policies and Realtime publication entries.
10. Add schema and policy contract tests.

## Must be done

- Parent comments cannot cross patient or clinic boundaries.
- Mentioned/assigned profiles must belong to the comment's clinic.
- Highlight offsets are zero-based, half-open Unicode code-point offsets.
- `quoted_text` must equal the selected historical `content_snapshot` substring.
- Clinicians may create/review manual highlights; service-role workers may later
  insert AI/rule suggestions. Staff/admin/patients cannot forge accepted highlights.
- Patient and anonymous roles receive no collaboration/highlight table access.

## Optional

- Inline comment source spans.
- Highlight categories beyond risk level.
- Notification outbox rows for mentions.

## Acceptance criteria

- [ ] Comment parent and mention foreign keys preserve clinic/patient tenancy.
- [ ] Invalid assignee or mentioned profile is rejected.
- [ ] Highlight entry/version mismatch is rejected.
- [ ] Negative, reversed, out-of-range, or quote-mismatched offsets are rejected.
- [ ] Highlight provenance remains immutable after creation.
- [ ] Admin has read-only collaboration access.
- [ ] Comments, mentions, and highlights are migration-managed Realtime tables.
- [ ] Migration SQL parses and contract tests pass.

## Evidence

- Versioned migration under `supabase/migrations/`
- Schema/RLS contract tests
- Updated local and hosted synthetic fixtures

## Done when

Later APIs can rely on database-enforced collaboration tenancy and exact
historical provenance rather than duplicating those invariants in every route.
