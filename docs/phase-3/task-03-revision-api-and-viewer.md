# P3-T03 — Revision API and Viewer

**Status:** Implemented locally; hosted role walkthrough pending
**Full estimate:** 1 hour
**16-hour path:** 25 minutes
**Dependencies:** P3-T02

## Objective

Expose authorized version history, a changes-since comparison, and confirmed
revert controls without sending unavailable clinical data to the browser.

## Required work, in order

1. Add bounded version-list and single-version response models.
2. Add entry/section version endpoints with caller-scoped reads.
3. Add a deterministic text comparison between selected and current snapshots.
4. Add revert endpoints with expected-current-version validation.
5. Build a viewer showing actor, role, time, reason, and before/current content.
6. Require explicit confirmation immediately before revert.
7. Refresh the resource, history, timeline, and Glance data after success.

## Must be done

- Patients do not receive internal version history.
- Diff text is generated from already authorized snapshots.
- Revert UI explains that history is preserved.
- A conflict keeps the user's selected comparison visible.

## Optional

- Word-level colored diff.
- Pagination beyond the demo history.
- Downloadable audit report.

## Acceptance criteria

- [ ] Any selected historical version can be compared with current content.
- [ ] Metadata identifies actor role, timestamp, and reason.
- [ ] Revert requires confirmation and produces a new visible version.
- [ ] Stale revert returns a usable conflict state.
- [ ] Staff/clinician/admin/patient visibility matches policy.

## Evidence

- Revision endpoints and response schemas
- Revision viewer component
- API/component tests and hosted role walkthrough

## Done when

A reviewer can explain what changed, who changed it, and how a prior state was restored.
