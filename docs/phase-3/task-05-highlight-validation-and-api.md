# P3-T05 — Highlight Validation and API

**Status:** Pending
**Full estimate:** 1.5 hours
**16-hour path:** 35 minutes
**Dependencies:** P3-T01, P3-T02

## Objective

Create and review manual/AI/rule highlights only when their exact historical
source can be resolved and proven.

## Required work, in order

1. Define create, list, source-resolution, accept, and reject schemas.
2. Normalize source content and quote consistently before validation.
3. Validate clinic/patient/entry/version identity and half-open offsets.
4. Reject any quoted-text mismatch before insertion/publication.
5. Allow clinician manual highlights and clinician review of suggestions.
6. Record reviewer, decision time, reason, and audit event atomically.
7. Keep rejected highlights for audit but exclude them from Glance eligibility.
8. Add fixtures from manual and AI-scribed source entries.

## Must be done

- The source version is immutable and remains resolvable after later edits.
- Accept/reject is clinician-only; admin is read-only.
- AI/rule creation is reserved for the worker/service path.
- Source-resolution errors return safe validation responses.
- Review operations are idempotent or reject invalid repeat transitions deterministically.

## Optional

- Bulk review.
- Duplicate/overlapping-highlight consolidation.
- Risk-category taxonomy.

## Acceptance criteria

- [ ] Valid manual and AI-scribed highlights resolve exact historical substrings.
- [ ] Invalid entry, version, offset, quote, clinic, or patient cannot be published.
- [ ] Accepted/rejected decisions identify a clinician reviewer.
- [ ] Rejected items never enter Glance.
- [ ] Later source edits do not break historical resolution.
- [ ] API and database validation tests cover Unicode code-point offsets.

## Evidence

- Highlight API/RPC implementation
- `test_highlight_provenance.py`
- Accepted/rejected synthetic fixtures

## Done when

Every surfaced highlight can prove exactly which historical characters support it.
