# P5-T02 — Unified Validation and Required Tests

**Status:** Local audit and required tests implemented; hosted/final gates remain
**Full estimate:** 1 hour
**16-hour path:** 30 minutes
**Dependencies:** P5-T01

## Objective

Provide one documented command that checks backend tests, frontend lint/types,
SQL contracts, tracked-secret safety, and the exact required evidence files.

## Required work, in order

1. Inventory the exact brief-named test files.
2. Add missing highlight provenance and adaptive-learning tests with real assertions.
3. Keep hosted/live tests opt-in and visibly skipped without credentials.
4. Add an automated release audit for tracked secrets and required artifacts.
5. Add a root `make release-check` target.
6. Run the command from a clean installation or equivalent fresh environment.
7. Record tool versions, pass counts, skips, and known limitations.

## Must be done

- Required test filenames exist exactly as documented.
- Tests fail for a broken invariant rather than merely matching a keyword.
- Release audit never prints a detected secret value.
- A strict release check exits nonzero for missing tests, attribution, or technical brief.
- Live-provider and hosted checks are not silently replaced with mocks.

## Optional

- GitHub Actions workflow and badge.
- Coverage threshold after required behaviors are complete.

## Acceptance criteria

- [x] Automated audit detects missing required files and tracked secret patterns safely.
- [x] Root release command is documented.
- [x] `test_rbac_scope.py` passes locally; the hosted RLS run remains pending.
- [x] `test_revision_history.py` passes locally.
- [x] `test_highlight_provenance.py` exists and passes with manual/AI exact-source evidence.
- [x] `test_concurrent_edits.py` passes locally; live transaction evidence remains pending.
- [x] `test_self_learning_importance.py` exists and passes bounded/idempotent safety behavior.
- [ ] Strict `make release-check` exits successfully.

## Done when

One command produces a trustworthy release result and every required test has meaningful evidence.
