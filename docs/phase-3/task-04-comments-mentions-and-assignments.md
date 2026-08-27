# P3-T04 — Comments, Mentions, and Assignments

**Status:** Pending
**Full estimate:** 1.5 hours
**16-hour path:** 30 minutes
**Dependencies:** P3-T01, Phase 2 task mutation

## Objective

Support clinic-scoped discussion threads with replies, mentions, assignment,
resolve, and reopen behavior around entries or note sections.

## Required work, in order

1. Add transactional create/reply operations with optional mention and assignee IDs.
2. Validate every mentioned/assigned profile against the target clinic.
3. Add resolve/reopen mutations with authorized actor/audit metadata.
4. Add bounded comment/thread response schemas and endpoints.
5. Build the thread panel, reply form, mention selection, assignee display, and status controls.
6. Hide mutation controls for admin and all patient-facing routes.
7. Seed one open and one resolved discussion.
8. Add RLS and lifecycle tests.

## Must be done

- A comment targets exactly one entry or section.
- Replies stay within their parent thread's clinic, patient, and target.
- Mention/assignee IDs are selected from authorized clinic profiles, not free text.
- Resolve/reopen does not modify comment body or authorship.
- Audit metadata excludes comment body text.

## Optional

- Notification delivery.
- Rich text, reactions, and inline span comments.
- Multiple task assignments per thread.

## Acceptance criteria

- [ ] Authorized staff/clinician can create and reply to a thread.
- [ ] Mention and assignment remain clinic scoped.
- [ ] Thread can be resolved and reopened without losing replies.
- [ ] Admin can read but cannot write; patients receive no internal comments.
- [ ] Cross-clinic parent, mention, assignee, and target attempts fail.
- [ ] Each lifecycle mutation creates a sanitized audit event.

## Evidence

- Comment/mention RPCs and API routes
- Thread UI
- Seed fixtures and authorization tests

## Done when

Two clinic collaborators can coordinate around a source without weakening tenant boundaries.
