# P3-T08 — Required Tests and Handoff

**Status:** Local automated gates pass; hosted checks pending
**Full estimate:** 1.25 hours
**16-hour path:** 15 minutes
**Dependencies:** P3-T01 through P3-T07

## Objective

Prove the trust model end to end and leave reproducible evidence for the
technical brief and demonstration.

## Required work, in order

1. Complete `test_revision_history.py` for edit, changes-since, revert, audit, and denial.
2. Complete `test_concurrent_edits.py` for same/different-resource outcomes and retry.
3. Complete `test_highlight_provenance.py` for manual/AI, Unicode spans, changed sources, and rejection.
4. Extend RBAC tests for comments, mentions, highlights, and admin read-only behavior.
5. Run SQL parsing, backend checks, web lint/type/build, and hosted live tests.
6. Run the two-session collaboration walkthrough.
7. Record screenshots/evidence and update Phase 3 statuses.

## Must be done

- Tests exercise database/RLS behavior, not only mocked serializers.
- At least one provenance fixture originates from an AI-scribed entry.
- Same-version conflict proves no successful content was lost.
- Logs, fixtures, screenshots, and reports contain synthetic data and no credentials.

## Optional

- Property-based Unicode span tests.
- Browser visual-regression snapshots.
- Performance measurement for revision/highlight endpoints.

## Acceptance criteria

- [x] Required local revision, concurrency, provenance, RBAC, and audit assertions pass.
- [ ] Live tests prove hosted RLS for collaboration tables.
- [x] Production web build and all static checks pass.
- [ ] Two-session behavior is reproducible from documentation.
- [x] Remaining limitations are explicitly external evidence gates or assigned to a later phase.

## Evidence

- Required named test files and command output
- Updated `docs/phase-3/README.md`
- Demo/technical-brief evidence notes

## Done when

The Phase 3 completion gate is satisfied and the trust model is ready for the AI pipeline.
