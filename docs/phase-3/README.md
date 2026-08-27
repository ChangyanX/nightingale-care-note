# Phase 3 Task Breakdown — Trust and Collaboration

Phase 3 makes the shared Care Note auditable, conflict-safe, collaborative, and
source-verifiable. It builds on Phase 1 ownership/version primitives and the
Phase 2 patient experience. Schema work can begin independently, but the phase
cannot complete until the remaining Phase 2 note/task mutation and Realtime
paths are verified.

| ID | Task | Status | Full estimate | 16-hour path | Depends on | Exit evidence |
|---|---|---|---:|---:|---|---|
| [P3-T01](task-01-collaboration-and-provenance-schema.md) | Collaboration and provenance schema | SQL implemented; apply pending | 1.25 h | 25 min | Phase 1 schema, Phase 2 tasks | RLS-secured threads, mentions, and exact-source highlights |
| [P3-T02](task-02-revision-revert-and-concurrency.md) | Revision, revert, and concurrency logic | SQL implemented; live concurrency pending | 1.5 h | 35 min | T01 | Immutable history, transactional revert, deterministic conflict |
| [P3-T03](task-03-revision-api-and-viewer.md) | Revision API and viewer | Implemented locally; hosted walkthrough pending | 1 h | 25 min | T02 | Version list, changes-since comparison, and confirmed revert UI |
| [P3-T04](task-04-comments-mentions-and-assignments.md) | Comments, mentions, and assignments | Pending | 1.5 h | 30 min | T01, Phase 2 task mutation | Thread lifecycle and clinic-valid mentions/assignees |
| [P3-T05](task-05-highlight-validation-and-api.md) | Highlight validation and API | Pending | 1.5 h | 35 min | T01, T02 | Exact historical span validation and review mutations |
| [P3-T06](task-06-provenance-and-review-ui.md) | Provenance and review UI | Pending | 1 h | 25 min | T03-T05 | Accept/reject and exact source navigation |
| [P3-T07](task-07-audit-and-realtime-collaboration.md) | Audit and Realtime collaboration | Pending | 1 h | 20 min | T02-T06 | Live comments/tasks/highlight decisions with safe audit trail |
| [P3-T08](task-08-required-tests-and-handoff.md) | Required tests and handoff | Pending | 1.25 h | 15 min | T01-T07 | Revision, provenance, concurrency, RBAC, and two-session evidence |

**Full Phase 3 estimate:** approximately 9-10 hours
**Critical-path allocation:** 3.5 hours

## Phase rules

- Revert creates a new version; it never deletes or rewrites history.
- Same-resource writes require `expected_version`; no stale update may silently win.
- Staff and clinicians retain role/owner boundaries during edit and revert.
- Exact provenance means entry, historical version, half-open Unicode offsets,
  and quoted-text equality. Entry-only links are insufficient for highlights.
- Comments, mentions, assignments, and highlight reviews are clinic scoped.
- Admin remains read-only for clinical collaboration.
- Patient responses never fetch internal comments, mentions, highlights, or audit data.
- Realtime events trigger caller-authorized refetches; event payloads are not trusted as authorization.
- Audit metadata contains identifiers and actions, not duplicated raw clinical bodies.

## Phase completion gate

Phase 3 is complete when authorized users can discuss a source, mention or
assign a clinic collaborator, compare and revert versions, resolve a
same-resource conflict without data loss, and accept/reject a highlight that
navigates to an exact historical source span. Required revision, provenance,
concurrency, RBAC, and two-session checks must pass.
