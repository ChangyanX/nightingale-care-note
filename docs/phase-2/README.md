# Phase 2 Task Breakdown — Core Patient Experience

Phase 2 turns the security foundation into the primary reviewer-facing product:
a clinic-scoped patient selector, an actionable Glance View, and a longitudinal
timeline. Tasks are ordered by dependency. Database and API tasks may be
implemented before hosted Phase 1 validation, but live integration and Phase 2
completion still require the hosted project.

| ID | Task | Status | Full estimate | 16-hour path | Depends on | Exit evidence |
|---|---|---|---:|---:|---|---|
| [P2-T01](task-01-demo-patient-contract.md) | Demo patient story and contracts | Implemented | 30 min | 10 min | Phase 1 schema | Approved narrative and bounded response contracts |
| [P2-T02](task-02-care-tasks-and-realtime-schema.md) | Care-task and realtime schema | SQL implemented; apply pending | 1 h | 20 min | T01 | Migrated task model with RLS and seed rows |
| [P2-T03](task-03-patient-read-api.md) | Patient, timeline, Glance, and task APIs | Locally verified; live pending | 1-1.5 h | 25 min | T01, T02 | Caller-scoped API responses and contract tests |
| [P2-T04](task-04-web-auth-and-data-client.md) | Web authentication and API client | Implemented; hosted Auth pending | 1 h | 20 min | Phase 1 Auth, T03 contracts | Real role-scoped session reaches FastAPI |
| [P2-T05](task-05-clinical-shell-and-patient-selector.md) | Clinical shell and patient selector | Implemented; role walkthrough pending | 1 h | 20 min | T03, T04 | Clinic-scoped navigation to a patient page |
| [P2-T06](task-06-glance-view-and-timeline.md) | Glance View and timeline | Implemented; live visual QA pending | 2 h | 50 min | T03-T05 | Primary patient is understandable in under ten seconds |
| [P2-T07](task-07-notes-and-care-task-actions.md) | Manual notes and task actions | Pending | 1 h | 20 min | T02-T06 | Role-permitted mutations appear in the UI |
| [P2-T08](task-08-realtime-states-and-verification.md) | Realtime, states, and verification | Pending | 1-1.5 h | 15 min | T05-T07 | Two-session updates and complete visual states |

**Full Phase 2 estimate:** approximately 8-9 hours  
**Critical-path allocation:** 3 hours

## Phase rules

- The Glance View is a bounded read model, not a dump of the full timeline.
- Every timeline item shows role, type, time, and source metadata.
- AI entries remain system-authored and visibly labelled as AI generated.
- The frontend never fetches internal rows for a patient-facing screen.
- Frontend role checks control usability only; FastAPI and RLS remain the
  authorization boundaries.
- Admin users see clinical information but receive no clinical mutation control.
- Realtime updates invalidate or refresh authorized queries; character-level
  collaborative editing remains out of scope.
- All names, identifiers, and clinical events remain synthetic.

## Phase completion gate

Phase 2 is complete when an authenticated staff or clinician can select an
in-clinic patient, understand the primary synthetic record from the above-fold
Glance View and timeline, create a permitted note, update a permitted task, and
observe those changes in another authorized browser session without reload.
Direct patient and cross-clinic requests must continue to return only RLS-safe
data.
