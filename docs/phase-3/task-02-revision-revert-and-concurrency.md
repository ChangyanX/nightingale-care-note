# P3-T02 — Revision, Revert, and Concurrency

**Status:** SQL implemented; live concurrency pending
**Full estimate:** 1.5 hours
**16-hour path:** 35 minutes
**Dependencies:** P3-T01

## Objective

Complete immutable entry/section history, deterministic stale-write handling,
and transactional revert behavior with an audit event for every mutation.

## Required work, in order

1. Review entry/section mutation paths for exactly-one version increments.
2. Require positive `expected_version` for each editable resource.
3. Lock the target row and return conflict when the expected version is stale.
4. Add entry and section revert functions accepting a selected historical version.
5. Recheck role/ownership rules during revert.
6. Insert the restored content as a new current version.
7. Record action, actor, role, resource, source version, and new version in audit metadata.
8. Add direct transactional tests for concurrent same/different-resource edits.

## Must be done

- Historical snapshots are never updated or deleted.
- One stale writer fails deterministically; the successful write remains intact.
- A revert cannot change resource identity, ownership, visibility, or provenance.
- Admin and cross-role users cannot revert clinical content.
- Conflict responses reveal the latest version number but not unauthorized content.

## Optional

- Server-provided three-way merge hints.
- Batched multi-section revert.

## Acceptance criteria

- [ ] Successful edit increments current version exactly once.
- [ ] Stale same-resource edit maps to HTTP `409`.
- [ ] Different-entry/section edits can both succeed.
- [ ] Revert content matches the selected snapshot and creates a new version.
- [ ] Version and audit records commit atomically with the content mutation.
- [ ] Unauthorized edit/revert attempts leave every row unchanged.

## Evidence

- Security-invoker RPC migrations
- `test_revision_history.py`
- `test_concurrent_edits.py`

## Done when

No edit or revert can silently overwrite another accepted change or erase history.
